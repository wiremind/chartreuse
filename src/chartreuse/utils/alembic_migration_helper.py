import re
from subprocess import SubprocessError
from typing import List

import sqlalchemy

from wiremind_kubernetes.utils import run_command

ALEMBIC_DIRECTORY_PATH = "/app/alembic"


class AlembicMigrationHelper(object):
    def __init__(
        self, database_url: str, allow_migration_for_empty_database: bool = False, configure: bool = True
    ):
        if not database_url:
            raise EnvironmentError("database_url not set, not upgrading database.")

        self.database_url = database_url
        self.allow_migration_for_empty_database = allow_migration_for_empty_database

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
            print("Postgres database does not need migration.")
            return False
        print("Postgres database can be migrated.")
        return True

    def migrate_db(self):
        """
        When used in a Helm post-install hook, exceptions that this function raises should never be catched.
        We need to guarantee that: if  "migrate_db" fails then "post-deploy" fails
        It would be great if this fct returns the status of the migration (failed/succeeded)
        """
        print("Database needs to be upgraded. Proceeding.")
        run_command("alembic history -r current:head", cwd=ALEMBIC_DIRECTORY_PATH)

        print("Upgrading database...")
        run_command("alembic upgrade head", cwd=ALEMBIC_DIRECTORY_PATH)

        print("Done upgrading database.")
