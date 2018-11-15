# -*- coding: utf-8 -*-
from future.standard_library import install_aliases

install_aliases()

import os
import sys

from .utils import AlembicMigrationHelper, stop_pods

ALLOW_MIGRATION_FOR_EMPTY_DATABASE = bool(
    os.environ.get("ALLOW_MIGRATION_FOR_EMPTY_DATABASE", "")
)
DATABASE_URL = os.environ.get("DATABASE_URL")


def main():
    alembic_migration_helper = AlembicMigrationHelper(DATABASE_URL, ALLOW_MIGRATION_FOR_EMPTY_DATABASE)
    if not alembic_migration_helper.check_migration_possible():
        sys.exit(0)
    stop_pods()


if __name__ == "__main__":
    main()
