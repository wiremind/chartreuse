# -*- coding: utf-8 -*-
from future.standard_library import install_aliases

install_aliases()

import os
import time

from wiremind_kubernetes import KubernetesHelper

from .utils import AlembicMigrationHelper, celery_workers_stop

ALLOW_MIGRATION_FOR_EMPTY_DATABASE = bool(
    os.environ.get("ALLOW_MIGRATION_FOR_EMPTY_DATABASE", "")
)
DATABASE_URL = os.environ.get("DATABASE_URL")


def main():
    AlembicMigrationHelper(DATABASE_URL, ALLOW_MIGRATION_FOR_EMPTY_DATABASE)
    # AlembicMigrationHelper exits 0 if no migration is needed
    celery_workers_stop()


if __name__ == "__main__":
    main()
