import os
import logging

from .chartreuse import Chartreuse

from wiremind_kubernetes import KubernetesDeploymentManager

logger = logging.getLogger(__name__)


def main() -> None:
    """
    When put in a post-install Helm hook, if this program fails the whole release is considered as failed.
    """
    POSTGRESQL_URL: str = os.environ["CHARTREUSE_ALEMBIC_URL"]
    ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE: bool = bool(
        os.environ["CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE"]
    )
    ALEMBIC_ADDITIONAL_PARAMETERS: str = os.environ["CHARTREUSE_ALEMBIC_ADDITIONAL_PARAMETERS"]
    ELASTICSEARCH_URL: str = os.environ["CHARTREUSE_ESLEMBIC_URL"]
    ESLEMBIC_ENABLE_CLEAN: bool = bool(os.environ["CHARTREUSE_ESLEMBIC_ENABLE_CLEAN"])
    ESLEMBIC_ENABLE_MIGRATE: bool = bool(os.environ["CHARTREUSE_ESLEMBIC_ENABLE_MIGRATE"])
    ENABLE_STOP_PODS: bool = bool(os.environ["CHARTREUSE_ENABLE_STOP_PODS"])
    RELEASE_NAME: str = os.environ["CHARTREUSE_RELEASE_NAME"]
    UPGRADE_BEFORE_DEPLOYMENT: bool = bool(os.environ["CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT"])
    HELM_IS_INSTALL: bool = bool(os.environ["HELM_IS_INSTALL"])

    deployment_manager = KubernetesDeploymentManager(release_name=RELEASE_NAME, use_kubeconfig=None)
    chartreuse = Chartreuse(
        postgresql_url=POSTGRESQL_URL,
        elasticsearch_url=ELASTICSEARCH_URL,
        alembic_allow_migration_for_empty_database=ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE,
        alembic_additional_parameters=ALEMBIC_ADDITIONAL_PARAMETERS,
        release_name=RELEASE_NAME,
        eslembic_enable_migrate=ESLEMBIC_ENABLE_MIGRATE,
        eslembic_clean_index=ESLEMBIC_ENABLE_CLEAN,
        kubernetes_helper=deployment_manager,
    )
    if chartreuse.is_migration_needed:
        if ENABLE_STOP_PODS:
            # If ever Helm has scaled up the pods that were stopped in predeployment.
            deployment_manager.stop_pods()

        # The exceptions this method raises should NEVER be caught.
        # If the migration fails, the post-install should fail and the release will fail
        # we will end up with the old release.
        chartreuse.upgrade()

        if not ENABLE_STOP_PODS:
            # Do not start pods
            return
        if UPGRADE_BEFORE_DEPLOYMENT and not HELM_IS_INSTALL:
            # Do not start pods in case of helm upgrade (not install, aka initial deployment) in "before" mode
            return

        # Scale up the new pods, only if chartreuse is:
        # in "upgrade after deployment" mode
        # or in "upgrade before deployment" mode, during initial install

        # We can fail and abort all, but if we're not that demanding we can start the pods manually
        # via mayo for example
        try:
            deployment_manager.start_pods()
        except:  # noqa: E722
            logger.error("Couldn't scale up new pods in chartreuse_upgrade after migration, SHOULD BE DONE MANUALLY ! ")


if __name__ == "__main__":
    main()
