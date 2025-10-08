import logging
import os

from wiremind_kubernetes import KubernetesDeploymentManager

from chartreuse import get_version

from .chartreuse import Chartreuse
from .config_loader import load_multi_database_config

logger = logging.getLogger(__name__)


def ensure_safe_run() -> None:
    """
    The compatibility between the Chartreuse package and Chartreuse Helm Chart is only ensured for
    versions with the same "major.minor".
    """
    package_v: str = get_version()
    # Get "1.2" from "1.2.3"
    package_v_major_minor: list[str] = package_v.split(".", 2)[:2]

    helm_chart_v: str = os.getenv("HELM_CHART_VERSION", "")
    if not helm_chart_v:
        raise ValueError(
            "Couldn't get the Chartreuse's Helm Chart version from the env var HELM_CHART_VERSION,"
            " couldn't make sure that the package is of a compatible version, ABORTING!"
        )
    helm_chart_v_major_minor: list[str] = helm_chart_v.split(".", 2)[:2]
    if helm_chart_v_major_minor != package_v_major_minor:
        raise ValueError(
            f"Chartreuse's Helm Chart version '{helm_chart_v}' and the package's version '{package_v}' "
            f"don't have the same 'major.minor' ({helm_chart_v_major_minor} != {package_v_major_minor}),"
            " they may be incompatible. Make sure they're semver, align them and retry, ABORTING!"
        )


def validate_config_file_path() -> str:
    """
    Validate that the multi-database configuration file path is properly configured and accessible.

    Returns:
        str: The validated config file path

    Raises:
        ValueError: If environment variable is not set or path is not a file
        FileNotFoundError: If the config file doesn't exist
    """
    multi_config_path = os.environ.get("CHARTREUSE_MULTI_CONFIG_PATH")

    if not multi_config_path:
        raise ValueError("CHARTREUSE_MULTI_CONFIG_PATH environment variable is required but not set")

    if not os.path.exists(multi_config_path):
        raise FileNotFoundError(f"Multi-database configuration file not found: {multi_config_path}")

    if not os.path.isfile(multi_config_path):
        raise ValueError(f"Multi-database configuration path is not a file: {multi_config_path}")

    return multi_config_path


def main() -> None:
    """
    When put in a post-install Helm hook, if this program fails the whole release is considered as failed.
    """
    ensure_safe_run()

    # Validate and get multi-database configuration path
    multi_config_path = validate_config_file_path()

    # Use multi-database configuration
    logger.info("Using multi-database configuration from: %s", multi_config_path)

    try:
        databases_config = load_multi_database_config(multi_config_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error("Failed to load multi-database configuration: %s", e)
        raise

    ENABLE_STOP_PODS: bool = os.environ.get("CHARTREUSE_ENABLE_STOP_PODS", "true").lower() not in ("", "false", "0")
    RELEASE_NAME: str = os.environ["CHARTREUSE_RELEASE_NAME"]
    UPGRADE_BEFORE_DEPLOYMENT: bool = os.environ.get("CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT", "false").lower() not in (
        "",
        "false",
        "0",
    )
    HELM_IS_INSTALL: bool = os.environ.get("HELM_IS_INSTALL", "false").lower() not in ("", "false", "0")

    deployment_manager = KubernetesDeploymentManager(release_name=RELEASE_NAME, use_kubeconfig=None)
    chartreuse = Chartreuse(
        databases_config=databases_config,
        release_name=RELEASE_NAME,
        kubernetes_helper=deployment_manager,
    )

    if chartreuse.is_migration_needed:
        if ENABLE_STOP_PODS:
            deployment_manager.stop_pods()

        chartreuse.upgrade()

        if not ENABLE_STOP_PODS:
            return
        if UPGRADE_BEFORE_DEPLOYMENT and not HELM_IS_INSTALL:
            return

        try:
            deployment_manager.start_pods()
        except Exception:
            logger.error("Couldn't scale up new pods in chartreuse_upgrade after migration, SHOULD BE DONE MANUALLY ! ")


if __name__ == "__main__":
    main()
