# -*- coding: utf-8 -*-
from future.standard_library import install_aliases

install_aliases()

import os
import time

from wiremind_kubernetes import KubernetesHelper

from .utils import AlembicMigrationHelper

ALLOW_MIGRATION_FOR_EMPTY_DATABASE = bool(
    os.environ.get("ALLOW_MIGRATION_FOR_EMPTY_DATABASE", "")
)
DATABASE_URL = os.environ.get("DATABASE_URL")


def celery_workers_stop():
    """
    SQL migration implies that every worker should be restarted.
    We stop every worker before applying migration
    """
    kubernetes_helper = KubernetesHelper()
    celery_deployment_list = kubernetes_helper.get_deployment_name_to_be_stopped_list()

    if not celery_deployment_list:
        return

    print("Shutting down celery workers")
    for celery_deployment_name in celery_deployment_list:
        kubernetes_helper.scale_down_deployment(celery_deployment_name)

    # Make sure to wait for actual stop (can be looong)
    for retry in range(360): # 1 hour
        time.sleep(10)
        stopped = 0
        for celery_deployment_name in celery_deployment_list:
            if kubernetes_helper.is_deployment_stopped(celery_deployment_name):
                stopped += 1
        if stopped == len(celery_deployment_list):
            break
        else:
            print("Celery workers not stopped yet. Waiting...")
    print("Celery workers have been stopped.")


def main():
    AlembicMigrationHelper(DATABASE_URL, ALLOW_MIGRATION_FOR_EMPTY_DATABASE)
    # AlembicMigrationHelper exits 0 if no migration is needed
    celery_workers_stop()


if __name__ == "__main__":
    main()
