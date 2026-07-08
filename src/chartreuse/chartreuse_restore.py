import logging
import os

from .chartreuse import configure_logging
from .chartreuse_upgrade import ensure_safe_run
from .kubernetes_helper import KubernetesDeploymentManager

logger = logging.getLogger(__name__)


def main() -> None:
    """
    Restore Deployments that a pre-deployment migration (CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT)
    stopped and that the deployment itself could not scale back up.

    On that path chartreuse-upgrade intentionally skips start_pods() and relies on the
    deployment that follows to restore replicas. That works for Deployments whose chart sets
    spec.replicas, but HPA-managed ones omit it: they stay at 0 replicas and an HPA whose
    target is at 0 with minReplicas >= 1 is ScalingDisabled and never scales them back up.

    Runs as a post-deployment (e.g. ArgoCD PostSync) hook: the new pod template is already
    applied, so scaling up only ever starts new-version pods. Only Deployments still carrying
    the annotation set by stop_pods() are touched. If this program fails, the deployment is
    considered as failed: stranded workers must be visible, not a log line.
    """
    configure_logging()
    ensure_safe_run()

    release_name: str = os.environ["CHARTREUSE_RELEASE_NAME"]

    deployment_manager = KubernetesDeploymentManager(release_name=release_name, use_kubeconfig=None)
    deployment_manager.restore_stopped_pods()


if __name__ == "__main__":
    main()
