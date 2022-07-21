import logging
import os
import re
from subprocess import SubprocessError
from time import sleep, time
from typing import List

import sqlalchemy
from sqlalchemy import inspect, text
from sqlalchemy.pool import NullPool
from wiremind_kubernetes.utils import run_command

logger = logging.getLogger(__name__)


class AlembicMigrationHelper:
    def __init__(
        self,
        *,
        alembic_directory_path: str = "/app/alembic",
        alembic_config_file_path: str = "alembic.ini",
        database_url: str,
        additional_parameters: str = "",
        allow_migration_for_empty_database: bool = False,
        configure: bool = True,
    ):
        if not database_url:
            raise ValueError("database_url not set, not upgrading database.")

        self.database_url = database_url
        self.allow_migration_for_empty_database = allow_migration_for_empty_database
        self.additional_parameters = additional_parameters
        self.alembic_directory_path = alembic_directory_path
        self.alembic_config_file_path = alembic_config_file_path

        # Chartreuse will upgrade a PG managed/configured by postgres-operator
        self.is_patroni_postgresql: bool = "CHARTREUSE_PATRONI_POSTGRESQL" in os.environ
        if self.is_patroni_postgresql:
            self.additional_parameters += " -x patroni_postgresql=yes"
            self._wait_postgres_is_configured()

        if configure:
            self._configure()

        self.is_migration_needed = self._check_migration_needed()

    def _configure(self) -> None:
        with open("%s/%s" % (self.alembic_directory_path, self.alembic_config_file_path), "r") as f:
            content = f.read()
            content_new = re.sub(
                "(sqlalchemy.url.*=.*){1}", r"sqlalchemy.url=%s" % self.database_url, content, flags=re.M
            )
        if content != content_new:
            with open("%s/%s" % (self.alembic_directory_path, self.alembic_config_file_path), "w") as f:
                f.write(content_new)
            logger.info("alembic.ini was configured.")
        else:
            raise SubprocessError("configuration of alembic.ini has failed (alembic.ini is unchanged)")

    def _wait_postgres_is_configured(self) -> None:
        """
        Make sure the user `wiremind_owner_user` was created by the postgres-operator
        and that default privileges were configured.
        # TODO: Maybe make this a readinessProbe on Patroni PG Pods
        """
        wait_timeout = int(os.getenv("CHARTREUSE_ALEMBIC_POSTGRES_WAIT_CONFIGURED_TIMEOUT", 60))
        engine = sqlalchemy.create_engine(self.database_url, poolclass=NullPool, connect_args={"connect_timeout": 1})

        default_privileges_checks: List[str] = [
            "SET ROLE wiremind_owner",  # The real owner, alembic will switch to it before running migrations.
            "CREATE TABLE _chartreuse_test_default_privileges(id serial)",
            "SET ROLE wiremind_writer_user",
            "INSERT INTO _chartreuse_test_default_privileges VALUES(1)",  # id = 1
            "SET ROLE wiremind_reader_user",
            "SELECT id from _chartreuse_test_default_privileges",
        ]
        start_time = time()

        while time() - start_time < wait_timeout:
            try:
                # Yes, we may create a connection each time.
                with engine.connect() as connection:
                    transac = connection.begin()
                    # TODO: Use scalar_one() once sqlachemly >= 1.4
                    _id = connection.execute(text(";".join(default_privileges_checks))).scalar()
                    assert _id == 1
                    transac.rollback()
                logger.info(
                    "The role wiremind_owner_user was created and the default privileges"
                    " were set by the postgres-operator."
                )
                return
            except Exception as e:
                # TODO: Learn about exceptions that should be caught here, otherwise we'll wait for nothing
                logger.info(f"Caught: {e}")
                logger.info(
                    "Waiting for the postgres-operator to create the user wiremind_owner_user"
                    " (that alembic and I use) and to set default privileges..."
                )
                sleep(2)
        raise Exception(
            f"I'm fed up! Waited {wait_timeout}s for postgres-operator to configure the"
            f" Postgres database. Check the Postgres logs and then postgres-operator for anything fishy."
        )

    def _get_table_list(self) -> List[str]:
        return inspect(sqlalchemy.create_engine(self.database_url)).get_table_names()

    def is_postgres_empty(self) -> bool:
        table_list = self._get_table_list()
        logger.info(f"Tables in the database: {table_list}")
        # Don't count "alembic" table
        table_name = "alembic_version"
        if table_name in table_list:
            table_list.remove(table_name)
        if table_list:
            return False
        return True

    def _get_alembic_current(self) -> str:
        command: str = f"alembic -c {self.alembic_config_file_path} {self.additional_parameters} current"
        alembic_current, stderr, returncode = run_command(command, return_result=True, cwd=self.alembic_directory_path)
        if returncode != 0:
            raise SubprocessError(f"{command} has failed: {alembic_current}, {stderr}")
        return alembic_current

    def _check_migration_needed(self) -> bool:
        if self.is_postgres_empty() and not self.allow_migration_for_empty_database:
            logger.info("Database is not populated yet but migration for empty database is forbidden, not upgrading.")
            return False

        head_re = re.compile(r"^\w+ \(head\)$", re.MULTILINE)
        alembic_current = self._get_alembic_current()
        if head_re.search(alembic_current):
            logger.info("SQL database schema does not need upgrade.")
            return False
        logger.info("SQL database schema can be upgraded.")
        return True

    def upgrade_db(self) -> None:
        logger.info("Database needs to be upgraded. Proceeding.")
        run_command(
            f"alembic -c {self.alembic_config_file_path} {self.additional_parameters} upgrade head",
            cwd=self.alembic_directory_path,
        )
        logger.info("Done upgrading database.")
