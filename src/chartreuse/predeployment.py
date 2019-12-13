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
    When put in a pre-install Helm hook, if this program fails (exit code !=0) the whole release is considered
     as failed.
    """
    deployment_manager = wiremind_kubernetes.KubernetesDeploymentManager()
    chartreuse = Chartreuse(
        DATABASE_URL, ELASTICSEARCH_URL,
        allow_migration_for_empty_database=ALLOW_MIGRATION_FOR_EMPTY_DATABASE
    )
    if chartreuse.is_migration_possible():
        # pre-upgrade (pre-install) hook = predeployment.py FAILS means that the Helm release had failed
        # Helm will try to rollback and will run the hook post-rollback = postrollback at the end.
        # This hook will try to start the pods that were stopped manually (actions not managed by Helm)
        # in this script
        deployment_manager.stop_pods()


if __name__ == "__main__":
    main()
