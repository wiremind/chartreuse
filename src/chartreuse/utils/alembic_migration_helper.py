import re
from subprocess import SubprocessError
from typing import List

import sqlalchemy
from wiremind_kubernetes.utils import run_command

ALEMBIC_DIRECTORY_PATH = "/app/alembic"


class AlembicMigrationHelper:
    def __init__(
        self, database_url: str, additional_parameters: str = "", allow_migration_for_empty_database: bool = False, configure: bool = True
    ):
        if not database_url:
            raise OSError("database_url not set, not upgrading database.")

        self.database_url = database_url
        self.allow_migration_for_empty_database = allow_migration_for_empty_database
        self.additional_parameters = additional_parameters

        if configure:
            self._configure()

        self.is_migration_needed = self._check_migration_needed()

    def _configure(self):
        cleaned_url = self.database_url.replace("/", r"\/")
        run_command(
            f"sed -i -e 's/sqlalchemy.url.*=.*/sqlalchemy.url={cleaned_url}/' alembic.ini",
            cwd=ALEMBIC_DIRECTORY_PATH
        )

    def _get_table_list(self) -> List[str]:
        return sqlalchemy.create_engine(self.database_url).table_names()

    def is_postgres_empty(self) -> bool:
        table_list = self._get_table_list()
        print("Tables in database: %s" % table_list)
        # Don't count "alembic" table
        table_name = "alembic_version"
        if table_name in table_list:
            table_list.remove(table_name)
        if table_list:
            return False
        return True

    def _get_alembic_current(self) -> str:
        alembic_current, stderr, returncode = run_command("alembic current", return_result=True, cwd=ALEMBIC_DIRECTORY_PATH)
        if returncode != 0:
            raise SubprocessError(f"alembic current failed: {alembic_current}, {stderr}")
        return alembic_current

    def _check_migration_needed(self):
        if self.is_postgres_empty() and not self.allow_migration_for_empty_database:
            print(
                "Database is not populated yet but migration for empty database is forbidden, not upgrading."
            )
            return False

        head_re = re.compile(r"^\w+ \(head\)$", re.MULTILINE)
        alembic_current = self._get_alembic_current()
        if head_re.search(alembic_current):
            print("SQL database schema does not need upgrade.")
            return False
        print("SQL database schema can be upgraded.")
        return True

    def upgrade_db(self):
        print("Database needs to be upgraded. Proceeding.")
        run_command(f"alembic {self.additional_parameters} upgrade head", cwd=ALEMBIC_DIRECTORY_PATH)
        print("Done upgrading database.")
