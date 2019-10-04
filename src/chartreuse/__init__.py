# -*- coding: utf-8 -*-
from .utils import AlembicMigrationHelper, EslembicMigrationHelper


class Chartreuse(object):
    def __init__(self, database_url, elasticsearch_url, allow_migration_for_empty_database):
        self.allow_migration_for_empty_database = allow_migration_for_empty_database

        self.alembic_migration_helper = AlembicMigrationHelper(
            database_url, allow_migration_for_empty_database
        )

        self.eslembic_migration_helper = \
            EslembicMigrationHelper(elasticsearch_url) if elasticsearch_url \
            else None

    def is_migration_possible(self):
        alembic_migration_possible = self.alembic_migration_helper.check_migration_possible()
        eslembic_migration_possible =  \
            self.eslembic_migration_helper.check_migration_possible() if self.eslembic_migration_helper \
            else False
        return alembic_migration_possible or eslembic_migration_possible

    def migrate(self):
        if self.alembic_migration_helper.check_migration_possible():
            self.alembic_migration_helper.migrate_db()

        if self.eslembic_migration_helper and self.eslembic_migration_helper.check_migration_possible():
            self.eslembic_migration_helper.migrate_db()
