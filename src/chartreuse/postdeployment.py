# -*- coding: utf-8 -*-
from future.standard_library import install_aliases

install_aliases()

import os

from .utils import Chartreuse

import wiremind_kubernetes

# XXX: extract wiremind_configuration from wiremind_python to make it a standalone lib and use it?
ALLOW_MIGRATION_FOR_EMPTY_DATABASE = bool(
    os.environ.get("ALLOW_MIGRATION_FOR_EMPTY_DATABASE", "")
)
DATABASE_URL = os.environ.get("DATABASE_URL")
ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", None)


def main():
    chartreuse = Chartreuse(
        DATABASE_URL, ELASTICSEARCH_URL,
        allow_migration_for_empty_database=ALLOW_MIGRATION_FOR_EMPTY_DATABASE
    )
    if chartreuse.is_migration_possible():
        deployment_manager = wiremind_kubernetes.KubernetesDeploymentManager()
        deployment_manager.stop_pods()
        chartreuse.migrate()
        deployment_manager.start_pods()


if __name__ == "__main__":
    main()
