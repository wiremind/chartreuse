import logging
import os
import subprocess
import sys
import time
import urllib.parse
from collections.abc import Generator

import pytest
import sqlalchemy
from sqlalchemy import inspect

import chartreuse
from chartreuse.kubernetes_helper import KubernetesDeploymentManager, load_kubernetes_config
from chartreuse.utils.command import run_command

TEST_NAMESPACE = "chartreuse-e2e-test"
TEST_RELEASE = "e2e-test-release"

# Test clusters the e2e suite is allowed to run against
TEST_IPS_WHITELISTED = [
    "localhost",  # minikube
    "127.0.0.1",  # kind
    "kubernetes.docker.internal",  # Docker for Mac
]
TEST_NODES_WHITELISTED = [
    "minikube",
    "kind-control-plane",
    "kind",
    "kind-worker",
]


def _is_ip_whitelisted() -> bool:
    api_server = subprocess.check_output(
        "kubectl config view --minify | grep server | cut -f 2- -d ':' | tr -d ' '",
        shell=True,
        text=True,
    )
    hostname = urllib.parse.urlparse(api_server.lower().strip()).hostname
    return hostname in TEST_IPS_WHITELISTED


def _is_node_whitelisted() -> bool:
    output, *_ = run_command("kubectl get nodes -o name", return_result=True)
    cluster_nodes = [x for x in output.replace("node/", "").split("\n") if x != ""]
    return all(node in TEST_NODES_WHITELISTED for node in cluster_nodes)


@pytest.fixture(scope="session", autouse=True)
def setUpE2E() -> None:
    """
    sys.exit(1) if kubectl current context api server is not a test cluster (like kind, minikube, etc)
    """
    logging.info("[CLUSTER-CONFIG]: Making sure the tests are running against a test cluster...")
    if not _is_ip_whitelisted() and not _is_node_whitelisted():
        logging.error("Attempted to run tests with a non-test cluster, aborting!")
        sys.exit(1)


ROOT_PATH = os.path.join(os.path.dirname(chartreuse.__file__), "..", "..")
EXAMPLE_PATH = os.path.join(ROOT_PATH, "example")
HELM_CHART_PATH = os.path.join(EXAMPLE_PATH, "helm-chart", "my-example-chart")
ALEMBIC_PATH = os.path.join(EXAMPLE_PATH, "alembic")

# Calculated from deployed test helm chart + kubectl exec
POSTGRESQL_URL = "postgresql://foo:foo@localhost/foo?sslmode=prefer"


def _cluster_init(include_chartreuse: bool, pre_upgrade: bool = False) -> Generator:
    # In order to configure kubernetes
    load_kubernetes_config(use_kubeconfig=None)

    logging.getLogger().setLevel(logging.INFO)

    try:
        run_command(f"kubectl create namespace {TEST_NAMESPACE}")

        additional_args = ""
        if include_chartreuse:
            if pre_upgrade:
                additional_args = "--set chartreuse.enabled=true --set chartreuse.upgradeBeforeDeployment=true"
            else:
                additional_args = "--set chartreuse.enabled=true --set chartreuse.upgradeBeforeDeployment=false"
        run_command(
            f"""helm install --wait {TEST_RELEASE} {HELM_CHART_PATH}
            --namespace {TEST_NAMESPACE} --timeout 180s {additional_args}""",
            cwd=EXAMPLE_PATH,
        )
        run_command(
            f"""helm upgrade --wait {TEST_RELEASE} {HELM_CHART_PATH}
            --namespace {TEST_NAMESPACE} --timeout 60s {additional_args}""",
            cwd=EXAMPLE_PATH,
        )

        kubectl_port_forwardpostgresql = subprocess.Popen(
            [
                "kubectl",
                "port-forward",
                "--namespace",
                TEST_NAMESPACE,
                f"{TEST_RELEASE}-postgresql-0",
                "5432",
            ]
        )
        time.sleep(5)  # Hack to wait for k exec to be up
    except:  # noqa
        run_command(
            f"""kubectl logs --selector app.kubernetes.io/instance=e2e-test-release
            --all-containers=false --namespace {TEST_NAMESPACE} --tail 1000"""
        )
        run_command(f"kubectl delete namespace {TEST_NAMESPACE} --grace-period=1")
        raise

    yield

    kubectl_port_forwardpostgresql.kill()
    run_command(f"kubectl delete namespace {TEST_NAMESPACE} --grace-period=60")


@pytest.fixture(scope="module")
def prepare_container_image_and_helm_chart() -> None:
    # We build a dummy docker image and deploy chartreuse subchart
    run_command(
        "docker build . -f example/Dockerfile-dev --tag dummy-e2e-chartreuse-image:latest",
        cwd=ROOT_PATH,
    )
    if os.environ.get("RUN_TEST_IN_KIND"):
        run_command(
            "kind load docker-image dummy-e2e-chartreuse-image:latest",
            cwd=ROOT_PATH,
        )

    run_command(
        "helm repo add stable https://charts.helm.sh/stable",
    )
    run_command(
        "helm dep up",
        cwd=HELM_CHART_PATH,
    )

    run_command("helm repo add wiremind https://wiremind.github.io/wiremind-helm-charts")
    run_command(
        "helm install wiremind-crds wiremind/wiremind-crds --version 0.1.0",
    )


@pytest.fixture
def populate_cluster() -> Generator:
    yield from _cluster_init(include_chartreuse=False)


@pytest.fixture
def populate_cluster_with_chartreuse_post_upgrade() -> Generator:
    yield from _cluster_init(include_chartreuse=True, pre_upgrade=False)


@pytest.fixture
def populate_cluster_with_chartreuse_pre_upgrade() -> Generator:
    yield from _cluster_init(include_chartreuse=True, pre_upgrade=True)


def assert_sql_upgraded() -> None:
    assert inspect(sqlalchemy.create_engine(POSTGRESQL_URL)).get_table_names() == [
        "alembic_version",
        "upgraded",
    ]


def assert_sql_not_upgraded() -> None:
    assert not inspect(sqlalchemy.create_engine(POSTGRESQL_URL)).get_table_names() == [
        "alembic_version",
        "upgraded",
    ]


def are_pods_scaled_down() -> bool:
    return KubernetesDeploymentManager(
        release_name=TEST_RELEASE,
        namespace=TEST_NAMESPACE,
        should_load_kubernetes_config=False,
    ).is_deployment_stopped("e2e-test-release-my-test-chart")
