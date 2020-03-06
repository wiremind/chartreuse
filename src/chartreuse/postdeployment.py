import os
import logging

from .chartreuse import Chartreuse

import wiremind_kubernetes

logger = logging.getLogger(__name__)


def main():
    """
    When put in a post-install Helm hook, if this program fails the whole release is considered as failed.
    """
    CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE = bool(
        os.environ["CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE"]
    )
    DATABASE_URL = os.environ["DATABASE_URL"]
    ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", None)
    RELEASE_NAME = os.environ["RELEASE_NAME"]
    CHARTREUSE_ESLEMBIC_ENABLE_UPGRADE = os.environ["CHARTREUSE_ESLEMBIC_ENABLE_UPGRADE"]
    CHARTREUSE_ESLEMBIC_CLEAN_INDEX = os.environ["CHARTREUSE_ESLEMBIC_CLEAN_INDEX"]

    deployment_manager = wiremind_kubernetes.KubernetesDeploymentManager(release_name=RELEASE_NAME, use_kubeconfig=None)
    chartreuse = Chartreuse(
        postgresql_url=DATABASE_URL,
        elasticsearch_url=ELASTICSEARCH_URL,
        alembic_allow_migration_for_empty_database=CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE,
        release_name=RELEASE_NAME,
        eslembic_enable_upgrade=CHARTREUSE_ESLEMBIC_ENABLE_UPGRADE,
        eslembic_clean_index=CHARTREUSE_ESLEMBIC_CLEAN_INDEX,
    )
    if chartreuse.is_migration_needed:
        # If ever Helm has scaled up the pods that were stopped in predeployment.
        deployment_manager.stop_pods()

        # The exceptions this method raises should NEVER be caught.
        # If the migration fails, the post-install should fail and the release will fail
        # we will end up with the old release.
        chartreuse.migrate()

        # After migration is done, we may need to create

        # Scale up the new pods.
        # We can fail and abort all, but if we're not that demanding we can start the pods manually
        # via mayo for example
        try:
            deployment_manager.start_pods()
        except:  # noqa: E722
            logger.error("Couldn't scale up new pods in postdeployment after migration, SHOULD BE DONE MANUALLY ! ")


if __name__ == "__main__":
    main()
