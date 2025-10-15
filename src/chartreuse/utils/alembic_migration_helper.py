import logging
import re
from configparser import ConfigParser
from subprocess import SubprocessError

import sqlalchemy
from sqlalchemy import inspect
from wiremind_kubernetes.utils import run_command

logger = logging.getLogger(__name__)


class AlembicMigrationHelper:
    def __init__(
        self,
        *,
        alembic_directory_path: str = "/app/alembic",
        alembic_config_file_path: str = "alembic.ini",
        database_url: str,
        alembic_section_name: str,
        additional_parameters: str = "",
        allow_migration_for_empty_database: bool = False,
        configure: bool = True,
        # skip_db_checks is used for testing purposes only
        skip_db_checks: bool = False,
    ):
        if not database_url:
            raise ValueError("database_url not set, not upgrading database.")

        self.database_url = database_url
        self.allow_migration_for_empty_database = allow_migration_for_empty_database
        self.additional_parameters = additional_parameters
        self.alembic_directory_path = alembic_directory_path
        self.alembic_config_file_path = alembic_config_file_path
        self.alembic_section_name = alembic_section_name
        self.skip_db_checks = skip_db_checks

        if configure:
            self._configure()
        # skip_db_checks is used for testing purposes only
        if not skip_db_checks:
            self.is_migration_needed = self._check_migration_needed()
        else:
            self.is_migration_needed = False

    def _configure(self) -> None:
        config_path = f"{self.alembic_directory_path}/{self.alembic_config_file_path}"

        # Read the configuration file
        config = ConfigParser()
        config.read(config_path)

        # Multi-database configuration: update specific section
        if not config.has_section(self.alembic_section_name):
            raise ValueError(f"Section '{self.alembic_section_name}' not found in {self.alembic_config_file_path}")

        # Update the sqlalchemy.url in the specific section
        config.set(self.alembic_section_name, "sqlalchemy.url", self.database_url)

        # Write the updated configuration back to the file
        with open(config_path, "w") as f:
            config.write(f)

        logger.info("alembic.ini was configured for section %s.", self.alembic_section_name)

    def _get_table_list(self) -> list[str]:
        return inspect(sqlalchemy.create_engine(self.database_url)).get_table_names()

    def is_postgres_empty(self) -> bool:
        table_list = self._get_table_list()
        logger.info("Tables in the database: %s", table_list)
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
