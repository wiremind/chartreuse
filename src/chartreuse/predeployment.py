import os
import logging

from .chartreuse import Chartreuse

import wiremind_kubernetes

logger = logging.getLogger(__name__)


def main():
    """
    When put in a pre-install Helm hook, if this program fails (exit code !=0) the whole release is considered
     as failed.
    """
    POSTGRESQL_URL: str = os.environ["CHARTREUSE_POSTGRESQL_URL"]
    ELASTICSEARCH_URL: str = os.environ["CHARTREUSE_ELASTICSEARCH_URL"]
    RELEASE_NAME: str = os.environ["CHARTREUSE_RELEASE_NAME"]
    ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE: bool = bool(
        os.environ["CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE"]
    )

    deployment_manager = wiremind_kubernetes.KubernetesDeploymentManager(release_name=RELEASE_NAME, use_kubeconfig=None)
    chartreuse = Chartreuse(
        postgresql_url=POSTGRESQL_URL,
        elasticsearch_url=ELASTICSEARCH_URL,
        release_name=RELEASE_NAME,
        alembic_allow_migration_for_empty_database=ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE,
        eslembic_clean_index=False,
        eslembic_enable_upgrade=False,
    )
    if chartreuse.is_migration_needed:
        # pre-upgrade (pre-install) hook = predeployment.py FAILS means that the Helm release had failed
        # Helm will try to rollback and will run the hook post-rollback = postrollback at the end.
        # This hook will try to start the pods that were stopped manually (actions not managed by Helm)
        # in this script
        deployment_manager.stop_pods()


if __name__ == "__main__":
    main()
