import logging
import os
from typing import List

from wiremind_kubernetes import KubernetesDeploymentManager

from chartreuse import get_version

from .chartreuse import Chartreuse

logger = logging.getLogger(__name__)


def ensure_safe_run() -> None:
    """
    The compatibility between the Chartreuse package and Chartreuse Helm Chart is only ensured for
    versions with the same "major.minor".
    """
    package_v: str = get_version()
    # Get "1.2" from "1.2.3"
    package_v_major_minor: List[str] = package_v.split(".", 2)[:2]

    helm_chart_v: str = os.getenv("HELM_CHART_VERSION", "")
    if not helm_chart_v:
        raise ValueError(
            "Couldn't get the Chartreuse's Helm Chart version from the env var HELM_CHART_VERSION,"
            " couldn't make sure that the package is of a compatible version, ABORTING!"
        )
    helm_chart_v_major_minor: List[str] = helm_chart_v.split(".", 2)[:2]
    if helm_chart_v_major_minor != package_v_major_minor:
        raise ValueError(
            f"Chartreuse's Helm Chart version '{helm_chart_v}' and the package's version '{package_v}' "
            f"don't have the same 'major.minor' ({helm_chart_v_major_minor} != {package_v_major_minor}),"
            " they may be incompatible. Make sure they're semver, align them and retry, ABORTING!"
        )


def main() -> None:
    """
    When put in a post-install Helm hook, if this program fails the whole release is considered as failed.
    """
    ensure_safe_run()
    ALEMBIC_DIRECTORY_PATH: str = os.environ.get("CHARTREUSE_ALEMBIC_DIRECTORY_PATH", "/app/alembic")
    ALEMBIC_CONFIG_FILE_PATH: str = os.environ.get("CHARTREUSE_ALEMBIC_CONFIG_FILE_PATH", "alembic.ini")
    POSTGRESQL_URL: str = os.environ["CHARTREUSE_ALEMBIC_URL"]
    ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE: bool = bool(
        os.environ["CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE"]
    )
    ALEMBIC_ADDITIONAL_PARAMETERS: str = os.environ["CHARTREUSE_ALEMBIC_ADDITIONAL_PARAMETERS"]
    ENABLE_STOP_PODS: bool = bool(os.environ["CHARTREUSE_ENABLE_STOP_PODS"])
    RELEASE_NAME: str = os.environ["CHARTREUSE_RELEASE_NAME"]
    UPGRADE_BEFORE_DEPLOYMENT: bool = bool(os.environ["CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT"])
    HELM_IS_INSTALL: bool = bool(os.environ["HELM_IS_INSTALL"])

    deployment_manager = KubernetesDeploymentManager(release_name=RELEASE_NAME, use_kubeconfig=None)
    chartreuse = Chartreuse(
        alembic_directory_path=ALEMBIC_DIRECTORY_PATH,
        alembic_config_file_path=ALEMBIC_CONFIG_FILE_PATH,
        postgresql_url=POSTGRESQL_URL,
        alembic_allow_migration_for_empty_database=ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE,
        alembic_additional_parameters=ALEMBIC_ADDITIONAL_PARAMETERS,
        release_name=RELEASE_NAME,
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
