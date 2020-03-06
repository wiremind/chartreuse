import os

from chartreuse.utils import EslembicMigrationHelper


def main():
    ELASTICSEARCH_URL = os.environ["ELASTICSEARCH_URL"]
    CHARTREUSE_ESLEMBIC_CLEAN_INDEX = os.environ["CHARTREUSE_ESLEMBIC_CLEAN_INDEX"]

    eslembic_migration_helper = EslembicMigrationHelper(elasticsearch_url=ELASTICSEARCH_URL)

    eslembic_migration_helper.migrate_db()

    if CHARTREUSE_ESLEMBIC_CLEAN_INDEX == "1":
        eslembic_migration_helper.clean_index()
