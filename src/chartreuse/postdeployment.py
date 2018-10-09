# -*- coding: utf-8 -*-
from future.standard_library import install_aliases

install_aliases()

import os

from .utils import KubernetesHelper, AlembicMigrationHelper

ALLOW_MIGRATION_FOR_EMPTY_DATABASE = bool(
    os.environ.get("ALLOW_MIGRATION_FOR_EMPTY_DATABASE", "")
)
DATABASE_URL = os.environ.get("DATABASE_URL")


def celery_workers_start():
    """
    Start all Celery
    """
    kubernetes_helper = KubernetesHelper()
    expected_deployment_scale_dict = kubernetes_helper.get_expected_deployment_scale_dict()

    if not expected_deployment_scale_dict:
        return

    print("Starting up celery workers")
    for (name, amount) in expected_deployment_scale_dict.items():
        kubernetes_helper.scale_up_deployment(name, amount)


def main():
    alembic_migration_helper = AlembicMigrationHelper(DATABASE_URL, ALLOW_MIGRATION_FOR_EMPTY_DATABASE)
    alembic_migration_helper.migrate_db()
    celery_workers_start()


if __name__ == "__main__":
    main()
