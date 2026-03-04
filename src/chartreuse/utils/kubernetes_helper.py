import logging
from pathlib import Path
from typing import Any

import kubernetes
import kubernetes.client
from kubernetes.client.exceptions import ApiException

logger = logging.getLogger(__name__)

EXPECTED_DEPLOYMENT_SCALE_GVP = {
    "group": "wiremind.io",
    "version": "v1",
    "plural": "expecteddeploymentscales",
}
PREVIOUS_REPLICAS_ANNOTATION = "chartreuse.wiremind.io/previous-replicas"


def _run_in_cluster() -> bool:
    return Path("/var/run/secrets/kubernetes.io/serviceaccount/token").is_file()


def _get_namespace_from_kube() -> str:
    namespace_path = Path("/var/run/secrets/kubernetes.io/serviceaccount/namespace")
    if namespace_path.is_file():
        return namespace_path.read_text(encoding="utf-8").strip()
    return "default"


def load_kubernetes_config(*, use_kubeconfig: bool | None = None) -> None:
    if use_kubeconfig is True:
        kubernetes.config.load_kube_config()
        return

    if use_kubeconfig is False:
        kubernetes.config.load_incluster_config()
        return

    if _run_in_cluster():
        try:
            kubernetes.config.load_incluster_config()
            return
        except kubernetes.config.config_exception.ConfigException:
            logger.debug("Could not load in-cluster config, falling back to kubeconfig.")

    kubernetes.config.load_kube_config()


class KubernetesDeploymentManager:
    def __init__(
        self,
        *,
        release_name: str,
        namespace: str | None = None,
        use_kubeconfig: bool | None = None,
        should_load_kubernetes_config: bool = True,
    ):
        self.release_name = release_name
        self.namespace = namespace or _get_namespace_from_kube()
        self.use_kubeconfig = use_kubeconfig
        self.should_load_kubernetes_config = should_load_kubernetes_config
        self._clients_initialized = False
        self.client_appsv1_api: kubernetes.client.AppsV1Api | None = None
        self.client_custom_objects_api: kubernetes.client.CustomObjectsApi | None = None

    def _ensure_clients_initialized(self) -> None:
        if self._clients_initialized:
            return

        if self.should_load_kubernetes_config:
            load_kubernetes_config(use_kubeconfig=self.use_kubeconfig)

        self.client_appsv1_api = kubernetes.client.AppsV1Api()
        self.client_custom_objects_api = kubernetes.client.CustomObjectsApi()
        self._clients_initialized = True

    def _release_label_selectors(self) -> list[str]:
        if not self.release_name:
            return []
        return [
            f"release={self.release_name}",
            f"app.kubernetes.io/instance={self.release_name}",
        ]

    def _list_release_deployments(self) -> list[Any]:
        self._ensure_clients_initialized()
        assert self.client_appsv1_api is not None
        deployments: dict[str, Any] = {}
        selectors = self._release_label_selectors() or [""]
        for selector in selectors:
            kwargs = {"namespace": self.namespace}
            if selector:
                kwargs["label_selector"] = selector
            for deployment in self.client_appsv1_api.list_namespaced_deployment(**kwargs).items:
                deployment_name = deployment.metadata.name
                if deployment_name:
                    deployments[deployment_name] = deployment
        return list(deployments.values())

    def _set_deployment_replicas(self, *, deployment_name: str, replicas: int) -> None:
        self._ensure_clients_initialized()
        assert self.client_appsv1_api is not None
        self.client_appsv1_api.patch_namespaced_deployment_scale(
            namespace=self.namespace,
            name=deployment_name,
            body={"spec": {"replicas": replicas}},
        )

    def _set_deployment_annotation(self, *, deployment_name: str, key: str, value: str) -> None:
        self._ensure_clients_initialized()
        assert self.client_appsv1_api is not None
        self.client_appsv1_api.patch_namespaced_deployment(
            namespace=self.namespace,
            name=deployment_name,
            body={"metadata": {"annotations": {key: value}}},
        )

    def _get_expected_deployment_scales(self) -> dict[str, int]:
        self._ensure_clients_initialized()
        assert self.client_custom_objects_api is not None
        scales: dict[str, int] = {}
        selectors = self._release_label_selectors() or [""]
        for selector in selectors:
            kwargs: dict[str, Any] = {
                "group": EXPECTED_DEPLOYMENT_SCALE_GVP["group"],
                "version": EXPECTED_DEPLOYMENT_SCALE_GVP["version"],
                "plural": EXPECTED_DEPLOYMENT_SCALE_GVP["plural"],
                "namespace": self.namespace,
            }
            if selector:
                kwargs["label_selector"] = selector

            try:
                resources = self.client_custom_objects_api.list_namespaced_custom_object(**kwargs)
            except ApiException as exc:
                if exc.status in {403, 404}:
                    logger.debug("ExpectedDeploymentScale custom resource is unavailable: %s", exc)
                    return {}
                raise

            for item in resources.get("items", []):
                spec = item.get("spec", {})
                deployment_name = spec.get("deploymentName") or item.get("metadata", {}).get("name")
                expected_scale = spec.get("expectedScale")
                if isinstance(deployment_name, str) and isinstance(expected_scale, int):
                    scales[deployment_name] = expected_scale
        return scales

    def stop_pods(self) -> None:
        for deployment in self._list_release_deployments():
            deployment_name = deployment.metadata.name
            current_replicas = deployment.spec.replicas or 0
            if current_replicas == 0:
                continue

            self._set_deployment_annotation(
                deployment_name=deployment_name,
                key=PREVIOUS_REPLICAS_ANNOTATION,
                value=str(current_replicas),
            )
            self._set_deployment_replicas(deployment_name=deployment_name, replicas=0)

    def start_pods(self) -> None:
        expected_scales = self._get_expected_deployment_scales()
        for deployment in self._list_release_deployments():
            deployment_name = deployment.metadata.name
            current_replicas = deployment.spec.replicas or 0

            wanted_replicas = expected_scales.get(deployment_name)
            if wanted_replicas is None:
                annotations = deployment.metadata.annotations or {}
                previous_replicas = annotations.get(PREVIOUS_REPLICAS_ANNOTATION)
                if previous_replicas and previous_replicas.isdigit():
                    wanted_replicas = int(previous_replicas)

            if wanted_replicas is None or wanted_replicas == 0 or current_replicas == wanted_replicas:
                continue

            self._set_deployment_replicas(deployment_name=deployment_name, replicas=wanted_replicas)

    def is_deployment_stopped(self, deployment_name: str) -> bool:
        self._ensure_clients_initialized()
        assert self.client_appsv1_api is not None
        deployment = self.client_appsv1_api.read_namespaced_deployment(
            namespace=self.namespace,
            name=deployment_name,
        )
        wanted_replicas = deployment.spec.replicas or 0
        replicas = deployment.status.replicas or 0
        ready_replicas = deployment.status.ready_replicas or 0
        available_replicas = deployment.status.available_replicas or 0
        return wanted_replicas == 0 and replicas == 0 and ready_replicas == 0 and available_replicas == 0
