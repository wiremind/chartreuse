# -*- coding: utf-8 -*-
from future.standard_library import install_aliases

install_aliases()

import os
import logging

from . import Chartreuse

import wiremind_kubernetes

logger = logging.getLogger(__name__)

# XXX: extract wiremind_configuration from wiremind_python to make it a standalone lib and use it?
ALLOW_MIGRATION_FOR_EMPTY_DATABASE = bool(
    os.environ.get("ALLOW_MIGRATION_FOR_EMPTY_DATABASE", "")
)
DATABASE_URL = os.environ.get("DATABASE_URL")
ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", None)


def main():
    """
    When put in a post-install Helm hook, if this program fails the whole release is considered as failed.
    """
    deployment_manager = wiremind_kubernetes.KubernetesDeploymentManager()
    chartreuse = Chartreuse(
        DATABASE_URL, ELASTICSEARCH_URL,
        allow_migration_for_empty_database=ALLOW_MIGRATION_FOR_EMPTY_DATABASE
    )
    if chartreuse.is_migration_possible():
        # If ever Helm has scaled up the pods that were stopped in predeployment.
        deployment_manager.stop_pods()

        # The exceptions this method raises should NEVER be caught.
        # If the migration fails, the post-install should fail and the release will fail
        # we will end up with the old release.
        chartreuse.migrate()

        # Scale up the new pods.
        # We can fail and abort all, but if we're not that demanding we can start the pods manually
        # via mayo for example
        try:
            deployment_manager.start_pods()
        except:  # noqa: E722
            logger.error("Couldn't scale up new pods in postdeployment after migration, SHOULD BE DONE MANUALLY ! ")


if __name__ == "__main__":
    main()
