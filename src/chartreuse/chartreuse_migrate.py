import os

from chartreuse.utils import EslembicMigrationHelper


def main():
    ELASTICSEARCH_URL: str = os.environ["CHARTREUSE_ESLEMBIC_URL"]
    ESLEMBIC_ENABLE_CLEAN: bool = bool(os.environ["CHARTREUSE_ESLEMBIC_ENABLE_CLEAN"])
    ESLEMBIC_ENABLE_MIGRATE = bool(os.environ["CHARTREUSE_ESLEMBIC_ENABLE_MIGRATE"])

    eslembic_migration_helper = EslembicMigrationHelper(elasticsearch_url=ELASTICSEARCH_URL)

    if ESLEMBIC_ENABLE_MIGRATE:
        eslembic_migration_helper.migrate_db()

    if ESLEMBIC_ENABLE_CLEAN:
        eslembic_migration_helper.clean_index()
