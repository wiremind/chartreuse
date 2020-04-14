import os
import logging

from .chartreuse import Chartreuse

from wiremind_kubernetes import KubernetesDeploymentManager

logger = logging.getLogger(__name__)


def stop_pods(deployment_manager: KubernetesDeploymentManager):
    deployment_manager.stop_pods()


def main() -> None:
    """
    When put in a post-install Helm hook, if this program fails the whole release is considered as failed.
    """
    POSTGRESQL_URL: str = os.environ["CHARTREUSE_POSTGRESQL_URL"]
    ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE: bool = bool(
        os.environ["CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE"]
    )
    ALEMBIC_ADDITIONAL_PARAMETERS: str = os.environ["CHARTREUSE_ALEMBIC_ADDITIONAL_PARAMETERS"]
    ELASTICSEARCH_URL: str = os.environ["CHARTREUSE_ELASTICSEARCH_URL"]
    ESLEMBIC_ENABLE_CLEAN: bool = bool(os.environ["CHARTREUSE_ESLEMBIC_ENABLE_CLEAN"])
    ESLEMBIC_ENABLE_UPGRADE: bool = bool(os.environ["CHARTREUSE_ESLEMBIC_ENABLE_UPGRADE"])
    ENABLE_STOP_PODS: bool = bool(os.environ["CHARTREUSE_ENABLE_STOP_PODS"])
    RELEASE_NAME: str = os.environ["CHARTREUSE_RELEASE_NAME"]

    deployment_manager = KubernetesDeploymentManager(release_name=RELEASE_NAME, use_kubeconfig=None)
    chartreuse = Chartreuse(
        postgresql_url=POSTGRESQL_URL,
        elasticsearch_url=ELASTICSEARCH_URL,
        alembic_allow_migration_for_empty_database=ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE,
        alembic_additional_parameters=ALEMBIC_ADDITIONAL_PARAMETERS,
        release_name=RELEASE_NAME,
        eslembic_enable_upgrade=ESLEMBIC_ENABLE_UPGRADE,
        eslembic_clean_index=ESLEMBIC_ENABLE_CLEAN,
    )
    if chartreuse.is_migration_needed:
        if ENABLE_STOP_PODS:
            # If ever Helm has scaled up the pods that were stopped in predeployment.
            stop_pods(deployment_manager)

        # The exceptions this method raises should NEVER be caught.
        # If the migration fails, the post-install should fail and the release will fail
        # we will end up with the old release.
        chartreuse.migrate()

        if ENABLE_STOP_PODS:
            # Scale up the new pods.
            # We can fail and abort all, but if we're not that demanding we can start the pods manually
            # via mayo for example
            try:
                deployment_manager.start_pods()
            except:  # noqa: E722
                logger.error("Couldn't scale up new pods in postdeployment after migration, SHOULD BE DONE MANUALLY ! ")


if __name__ == "__main__":
    main()
