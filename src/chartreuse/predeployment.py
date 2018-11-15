# -*- coding: utf-8 -*-
from future.standard_library import install_aliases

install_aliases()

import os

from .utils import AlembicMigrationHelper, stop_pods

ALLOW_MIGRATION_FOR_EMPTY_DATABASE = bool(
    os.environ.get("ALLOW_MIGRATION_FOR_EMPTY_DATABASE", "")
)
DATABASE_URL = os.environ.get("DATABASE_URL")


def main():
    AlembicMigrationHelper(DATABASE_URL, ALLOW_MIGRATION_FOR_EMPTY_DATABASE)
    # AlembicMigrationHelper exits 0 if no migration is needed
    stop_pods()


if __name__ == "__main__":
    main()
