"""
Kubernetes helpers to stop, start and restore the application's Deployments around a database
migration.

Trimmed port of wiremind_kubernetes.KubernetesDeploymentManager (a library being
decommissioned): only what chartreuse uses survived — ExpectedDeploymentScale-driven
scale down/up with HPA disabling, plus the stopped-by annotation and restore logic.
Depends only on the official kubernetes client.
"""

import functools
import logging
import os
import pprint
import time
from collections.abc import Callable, Generator
from typing import Any

import kubernetes

logger = logging.getLogger(__name__)

HPA_ID_PREFIX = "wm--disabled--kube"
# Set by stop_pods() on every Deployment it scales down, cleared by start_pods() and
# restore_stopped_pods(). Allows telling "stopped by us" apart from "deliberately scaled to 0".
STOPPED_ANNOTATION = "wiremind.io/stopped-by"


def load_kubernetes_config(use_kubeconfig: bool | None = None) -> None:
    """
    Load kubernetes configuration in memory, either from incluster method or from kubeconfig.
    :param use_kubeconfig:
        If True: Use ~/.kube/config file to authenticate.
        If False: use kubernetes built-in incluster mechanism.
        If None, will try to load built-in incluster mechanism, then try config file.
        Defaults to None.
    """
    if os.environ.get("CLASSIC_K8S_CONFIG"):
        # We are in a Kind cluster for E2E test! Never use in cluster config.
        kubernetes.config.load_kube_config()
        return

    if use_kubeconfig is True:
        kubernetes.config.load_kube_config()
    elif use_kubeconfig is False:
        kubernetes.config.load_incluster_config()
    elif use_kubeconfig is None:
        if os.path.exists(kubernetes.config.incluster_config.SERVICE_TOKEN_FILENAME):
            kubernetes.config.load_incluster_config()
        else:
            kubernetes.config.load_kube_config()
    logger.debug("Kubernetes configuration successfully set.")


def retry_kubernetes_request(function: Callable) -> Callable:
    """
    Decorator that retries a failed Kubernetes API request if needed and ignores 404
    """

    @functools.wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return function(*args, **kwargs)
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404:
                logger.warning("Not found, ignoring.")
                return
            logger.error(e)
            logger.info("Retrying in 5 seconds...")
            time.sleep(5)
            return function(*args, **kwargs)

    return wrapper


def retry_kubernetes_request_no_ignore(function: Callable) -> Callable:
    """
    Decorator that retries a failed Kubernetes API request if needed and do NOT ignore 404 (raise if 404)
    """

    @functools.wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return function(*args, **kwargs)
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404:
                raise
            logger.error(e)
            logger.info("Retrying in 5 seconds...")
            time.sleep(5)
            return function(*args, **kwargs)

    return wrapper


def _get_namespace_from_kube() -> str:
    return open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()


class KubernetesDeploymentManager:
    """
    Scale down/up all Deployments that should be stopped/started when doing database
    migration/maintenance (alembic, dump, etc). Each managed Deployment must define an
    ExpectedDeploymentScale.

    Usage:
    manager = KubernetesDeploymentManager(release_name="my-release", use_kubeconfig=None)
    manager.stop_pods()
    do_something('wololo')
    manager.start_pods()
    """

    SCALE_DOWN_MAX_WAIT_TIME: int = 3600

    def __init__(
        self,
        release_name: str,
        use_kubeconfig: bool | None = False,
        namespace: str | None = None,
        should_load_kubernetes_config: bool = True,
    ):
        if should_load_kubernetes_config:
            load_kubernetes_config(use_kubeconfig=use_kubeconfig)
        self.release_name = release_name
        self.namespace = namespace if namespace else _get_namespace_from_kube()
        self.client_appsv1_api = kubernetes.client.AppsV1Api()
        self.client_corev1_api = kubernetes.client.CoreV1Api()
        self.client_autoscalingv2_api = kubernetes.client.AutoscalingV2Api()
        self.client_custom_objects_api = kubernetes.client.CustomObjectsApi()

    def get_deployment_scale(self, deployment_name: str) -> kubernetes.client.V1Scale:
        logger.debug("Getting deployment scale for %s", deployment_name)
        return self.client_appsv1_api.read_namespaced_deployment_scale(deployment_name, self.namespace)

    @retry_kubernetes_request
    def scale_down_deployment(self, deployment_name: str) -> None:
        body = self.get_deployment_scale(deployment_name)
        logger.debug("Deleting all Pods for %s", deployment_name)
        body.spec.replicas = 0
        self.client_appsv1_api.patch_namespaced_deployment_scale(deployment_name, self.namespace, body)
        logger.debug("Done deleting.")

    @retry_kubernetes_request
    def scale_up_deployment(self, deployment_name: str, pod_amount: int) -> None:
        body = self.get_deployment_scale(deployment_name)
        logger.debug("Recreating backend Pods for %s", deployment_name)
        body.spec.replicas = pod_amount
        self.client_appsv1_api.patch_namespaced_deployment_scale(deployment_name, self.namespace, body)
        logger.debug("Done recreating.")

    @retry_kubernetes_request_no_ignore
    def _get_pods_from_deployment(self, deployment_name: str) -> list:
        logger.debug("Asking if Deployment %s is stopped", deployment_name)
        labels = self.client_appsv1_api.read_namespaced_deployment(
            deployment_name, self.namespace
        ).spec.selector.match_labels

        try:
            return self.client_corev1_api.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=",".join(["{}={}".format(*kv) for kv in labels.items()]),
            ).items
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404:
                return []
            else:
                raise

    def is_deployment_stopped(self, deployment_name: str) -> bool:
        try:
            pod_list: list = self._get_pods_from_deployment(deployment_name)
        except kubernetes.client.rest.ApiException as e:
            if e.status == 404:
                logger.warning("Not found, ignoring.")
                return True
            raise

        current_scale = 0
        for pod in pod_list:
            if pod.status.phase not in ("Failed"):
                current_scale += 1

        if current_scale > 0:
            logger.info("%s Deployment has %s living replicas", deployment_name, current_scale)
            return False
        return True

    def get_deployment_hpa(self, *, deployment_name: str) -> Generator:
        for hpa in self.client_autoscalingv2_api.list_namespaced_horizontal_pod_autoscaler(self.namespace).items:
            if hpa.spec.scale_target_ref.kind == "Deployment" and hpa.spec.scale_target_ref.name == deployment_name:
                yield hpa

    def patch_deployment_hpa(self, *, hpa_name: str, body: Any) -> None:
        self.client_autoscalingv2_api.patch_namespaced_horizontal_pod_autoscaler(
            name=hpa_name, namespace=self.namespace, body=body
        )

    @retry_kubernetes_request
    def annotate_deployment(self, deployment_name: str, annotations: dict[str, str | None]) -> None:
        """
        Add or update annotations on a Deployment. A None value removes the annotation.
        """
        body = {"metadata": {"annotations": annotations}}
        self.client_appsv1_api.patch_namespaced_deployment(deployment_name, self.namespace, body)

    @retry_kubernetes_request_no_ignore
    def _get_expected_deployment_scale_dict(self) -> dict[int, dict[str, int]]:
        """
        Return a dict of expected deployment scale:
        {
            0: {  # priority
                # key: Deployment name, only if it has an associated eds
                # value: expected Deployment Scale (replicas)
                "my-deployment": 3,
                "my-other-deployment": 42
            },
            1: {
                "my-third-deployment": 17,
            },
        }
        """
        logger.debug("Getting Expected Deployment Scale list")
        eds_list: list[dict[str, Any]] = []
        release_label_keys = ["app.kubernetes.io/instance", "release"]

        for release_label_key in release_label_keys:
            logger.debug(f"Getting Expected Deployment Scale list with the release label key {release_label_key}")
            try:
                eds_list.extend(
                    self.client_custom_objects_api.list_namespaced_custom_object(
                        namespace=self.namespace,
                        group="wiremind.io",
                        version="v1",
                        plural="expecteddeploymentscales",
                        label_selector=f"{release_label_key}={self.release_name}",
                    )["items"]
                )
            except kubernetes.client.rest.ApiException as e:
                if e.status != 404:
                    raise

        eds_dict: dict[int, dict[str, int]] = {}
        for eds in eds_list:
            deployment_name: str = eds["spec"]["deploymentName"]
            expected_scale: int = eds["spec"]["expectedScale"]
            priority: int = eds["spec"].get("priority", 0)

            if priority not in eds_dict:
                eds_dict[priority] = {}

            eds_dict[priority][deployment_name] = expected_scale

        logger.debug("Deployments are %s", pprint.pformat(eds_dict))
        return eds_dict

    @retry_kubernetes_request
    def disable_hpa(self, *, deployment_name: str) -> None:
        for hpa in self.get_deployment_hpa(deployment_name=deployment_name):
            # Tell the hpa to manage a non-existing Deployment
            hpa.spec.scale_target_ref.name = f"{HPA_ID_PREFIX}-{deployment_name}"
            self.patch_deployment_hpa(hpa_name=hpa.metadata.name, body=hpa)

    @retry_kubernetes_request
    def re_enable_hpa(self, *, deployment_name: str) -> None:
        for hpa in self.get_deployment_hpa(deployment_name=f"{HPA_ID_PREFIX}-{deployment_name}"):
            hpa.spec.scale_target_ref.name = deployment_name
            self.patch_deployment_hpa(hpa_name=hpa.metadata.name, body=hpa)

    def _are_deployments_stopped(self, deployment_dict: dict[str, int]) -> bool:
        for deployment_name in deployment_dict:
            if not self.is_deployment_stopped(deployment_name):
                return False
        return True

    def _stop_deployments(self, deployment_dict: dict[str, int]) -> None:
        """
        Scale down a dict (deployment_name, expected_scale) of Deployments.
        """
        for deployment_name in deployment_dict:
            self.annotate_deployment(deployment_name, {STOPPED_ANNOTATION: self.release_name})
        for _ in range(self.SCALE_DOWN_MAX_WAIT_TIME):
            for deployment_name in deployment_dict:
                self.disable_hpa(deployment_name=deployment_name)
                self.scale_down_deployment(deployment_name)
            if self._are_deployments_stopped(deployment_dict):
                break
            time.sleep(1)
        else:
            raise Exception("Timed out waiting for pods to be deleted: aborting.")

    def stop_pods(self) -> None:
        """
        Scale to 0 all deployments for which an ExpectedDeploymentScale links to.
        stop all deployments, then wait for actual stop, by priority (descending order):
        Example: stop all deployments with priority 1, then all deployments with priority 0
        """
        expected_deployment_scale_dict: dict[int, dict[str, int]] = self._get_expected_deployment_scale_dict()

        logger.info("Scaling down application Deployments...")
        if not expected_deployment_scale_dict:
            logger.info("No Deployments to scale down")
            return

        priorities: list[int] = sorted(expected_deployment_scale_dict, reverse=True)
        for priority in priorities:
            priority_dict: dict[str, int] = expected_deployment_scale_dict[priority]
            if len(priority_dict):
                self._stop_deployments(priority_dict)
        logger.info("Done scaling down application Deployments.")

    def start_pods(self) -> None:
        """
        Start all Pods that should be started
        """
        expected_deployment_scale_dict: dict[int, dict[str, int]] = self._get_expected_deployment_scale_dict()

        logger.info("Scaling up application Deployments...")
        if not expected_deployment_scale_dict:
            logger.info("No Deployments to scale up")
            return

        scaled: bool = False
        for priority_dict in expected_deployment_scale_dict.values():
            if len(priority_dict):
                scaled = True
                for name, expected_scale in priority_dict.items():
                    self.re_enable_hpa(deployment_name=name)
                    self.scale_up_deployment(name, expected_scale)
                    self.annotate_deployment(name, {STOPPED_ANNOTATION: None})
        if scaled:
            logger.info("Done scaling up application Deployments")
        else:
            logger.info("No Deployments to scale up")

    def restore_stopped_pods(self) -> None:
        """
        Restore Deployments that stop_pods() scaled down and that nothing scaled back up since.

        Only Deployments still carrying STOPPED_ANNOTATION are touched, so a Deployment
        deliberately scaled to zero outside of stop_pods() is left alone.

        Meant to run after the deployment that follows a stop_pods() without start_pods()
        (CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT): that deployment restores spec.replicas of
        Deployments that define it in their chart, but HPA-managed ones omit it, and an HPA
        whose target is at 0 replicas with minReplicas >= 1 is ScalingDisabled and will never
        scale it back up.
        """
        expected_deployment_scale_dict: dict[int, dict[str, int]] = self._get_expected_deployment_scale_dict()

        logger.info("Restoring Deployments left stopped...")
        restored: list[str] = []
        for priority in sorted(expected_deployment_scale_dict):
            for name, expected_scale in expected_deployment_scale_dict[priority].items():
                try:
                    deployment = self.client_appsv1_api.read_namespaced_deployment(name, self.namespace)
                except kubernetes.client.rest.ApiException as e:
                    if e.status == 404:
                        continue
                    raise
                if STOPPED_ANNOTATION not in (deployment.metadata.annotations or {}):
                    continue
                self.re_enable_hpa(deployment_name=name)
                if not deployment.spec.replicas:
                    target_scale = expected_scale
                    if target_scale < 1 and any(self.get_deployment_hpa(deployment_name=name)):
                        # Any scale >= 1 re-arms the HPA, which then enforces its own minReplicas
                        target_scale = 1
                    if target_scale > 0:
                        self.scale_up_deployment(name, target_scale)
                self.annotate_deployment(name, {STOPPED_ANNOTATION: None})
                restored.append(name)
        if restored:
            logger.info("Done restoring stopped Deployments: %s", ", ".join(restored))
        else:
            logger.info("No stopped Deployments to restore")
