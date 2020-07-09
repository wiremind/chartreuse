import logging
import os
import subprocess
import time

import elasticsearch
import pytest
import sqlalchemy
from wiremind_kubernetes.kube_config import load_kubernetes_config
from wiremind_kubernetes.kubernetes_helper import KubernetesDeploymentManager, KubernetesHelper
from wiremind_kubernetes.tests.e2e_tests.conftest import create_namespace, setUpE2E  # noqa: F401
from wiremind_kubernetes.utils import run_command

import chartreuse

TEST_NAMESPACE = "chartreuse-e2e-test"
TEST_RELEASE = "e2e-test-release"

ABSOLUTE_PATH = os.path.dirname(os.path.join(os.path.abspath(chartreuse.__file__)))
E2E_TESTS_PATH = os.path.join(ABSOLUTE_PATH, "tests/e2e_tests")
ROOT_PATH = os.path.join(ABSOLUTE_PATH, "..", "..")
TEST_CHART = os.path.join(E2E_TESTS_PATH, "helm_chart/my-test-chart")

# Calculated from deployed test helm chart + kubectl exec
ELASTICSEARCH_URL = "http://localhost:9200"
POSTGRESQL_URL = f"postgresql://foo:foo@localhost/foo?sslmode=prefer"

SAMPLE_ESLEMBIC_PATH = os.path.join(E2E_TESTS_PATH, "sample_eslembic")
SAMPLE_ALEMBIC_PATH = os.path.join(E2E_TESTS_PATH, "sample_alembic")


def _cluster_init(include_chartreuse: bool, pre_upgrade: bool = False):
    # In order to configure kubernetes
    load_kubernetes_config(use_kubeconfig=None)

    logging.getLogger().setLevel(logging.INFO)

    if include_chartreuse:
        # We build a dummy docker image and deploy chartreuse subchart
        run_command(
            f"docker build . -f {E2E_TESTS_PATH}/Dockerfile --tag dummy-e2e-chartreuse-image:latest --build-arg PYPI_PASSWORD_READONLY={os.environ['PYPI_PASSWORD_READONLY']}",
            cwd=ROOT_PATH,
        )
        if os.environ.get("CLASSIC_K8S_CONFIG"):
            run_command(
                "kind load docker-image dummy-e2e-chartreuse-image:latest", cwd=ROOT_PATH,
            )

    run_command(
        f"helm repo add stable https://kubernetes-charts.storage.googleapis.com/", cwd=TEST_CHART,
    )
    run_command(
        f"helm repo add elastic https://helm.elastic.co", cwd=TEST_CHART,
    )
    run_command(
        f"helm dep up", cwd=TEST_CHART,
    )

    run_command(f"kubectl apply -f {E2E_TESTS_PATH}/CustomResourceDefinition-expecteddeploymentscales.yaml",)

    try:
        run_command(f"kubectl create namespace {TEST_NAMESPACE}")

        additional_args = ""
        if include_chartreuse:
            if pre_upgrade:
                additional_args = "--set chartreuse.enabled=true --set chartreuse.upgradeBeforeDeployment=true"
            else:
                additional_args = "--set chartreuse.enabled=true --set chartreuse.upgradeBeforeDeployment=false"
        run_command(
            f"helm upgrade --install --wait {TEST_RELEASE} {TEST_CHART} --namespace {TEST_NAMESPACE} --timeout 1200s {additional_args}",
            cwd=ABSOLUTE_PATH,
        )
        run_command(
            f"helm upgrade --install --wait {TEST_RELEASE} {TEST_CHART} --namespace {TEST_NAMESPACE} --timeout 1200s {additional_args}",
            cwd=ABSOLUTE_PATH,
        )

        kubectl_port_forwardpostgresql = subprocess.Popen(
            ["kubectl", "port-forward", "--namespace", TEST_NAMESPACE, f"{TEST_RELEASE}-postgresql-0", "5432"]
        )
        kubectl_port_forwardelasticsearch = subprocess.Popen(
            ["kubectl", "port-forward", "--namespace", TEST_NAMESPACE, f"{TEST_RELEASE}-elasticsearch-hot-0", "9200"]
        )
        time.sleep(5)  # Hack to wait for k exec to be up
    except:  # noqa
        run_command(
            f"kubectl logs --selector app.kubernetes.io/instance=e2e-test-release --all-containers=false --namespace {TEST_NAMESPACE} --tail 1000"
        )
        run_command(f"kubectl delete namespace {TEST_NAMESPACE} --grace-period=1")
        raise

    yield

    kubectl_port_forwardpostgresql.kill()
    kubectl_port_forwardelasticsearch.kill()
    run_command(f"kubectl delete namespace {TEST_NAMESPACE} --grace-period=1")


@pytest.fixture
def populate_cluster():
    yield from _cluster_init(include_chartreuse=False)


@pytest.fixture
def populate_cluster_with_chartreuse_post_upgrade():
    yield from _cluster_init(include_chartreuse=True, pre_upgrade=False)


@pytest.fixture
def populate_cluster_with_chartreuse_pre_upgrade():
    yield from _cluster_init(include_chartreuse=True, pre_upgrade=True)


def assert_sql_upgraded():
    assert sqlalchemy.create_engine(POSTGRESQL_URL).table_names() == ["alembic_version", "upgraded"]


def assert_sql_not_upgraded():
    assert not sqlalchemy.create_engine(POSTGRESQL_URL).table_names() == ["alembic_version", "upgraded"]


def assert_elasticsearch_upgraded():
    es: elasticsearch.Elasticsearch = elasticsearch.Elasticsearch([ELASTICSEARCH_URL])
    assert "my_index-0" in es.indices.get("*").keys()


def assert_elasticsearch_not_upgraded():
    es: elasticsearch.Elasticsearch = elasticsearch.Elasticsearch([ELASTICSEARCH_URL])
    assert "my_index-0" not in es.indices.get("*").keys()


def assert_elasticsearch_migrating():
    # Only test that a job has been created with post-upgrade chartreuse command
    client_batchv1_api = KubernetesHelper(should_load_kubernetes_config=False).client_batchv1_api
    job = client_batchv1_api.read_namespaced_job(namespace=TEST_NAMESPACE, name=f"{TEST_RELEASE}-chartreuse-migrate")
    env = job.spec.template.spec.containers[0].env
    assert env[0].to_dict() == {"name": "CHARTREUSE_ESLEMBIC_URL", "value": ELASTICSEARCH_URL, "value_from": None}
    assert env[1].to_dict() == {"name": "CHARTREUSE_ESLEMBIC_ENABLE_CLEAN", "value": "1", "value_from": None}


def are_pods_scaled_down():
    return KubernetesDeploymentManager(
        release_name=TEST_RELEASE, namespace=TEST_NAMESPACE, should_load_kubernetes_config=False
    ).is_deployment_stopped("e2e-test-release-my-test-chart")
