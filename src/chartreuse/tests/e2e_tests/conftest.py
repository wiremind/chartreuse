import logging
import os
import subprocess
import time

import pytest

import chartreuse
from wiremind_kubernetes.tests.e2e_tests.conftest import create_namespace, setUpE2E  # noqa: F401
from wiremind_kubernetes.utils import run_command

test_logger = logging.getLogger(__name__)

TEST_NAMESPACE = "chartreuse-e2e-test"
TEST_RELEASE = "e2e-test-release"

ABSOLUTE_PATH = os.path.dirname(os.path.join((os.path.abspath(chartreuse.__file__))))
E2E_TESTS_PATH = os.path.join(ABSOLUTE_PATH, "tests/e2e_tests")
ROOT_PATH = os.path.join(ABSOLUTE_PATH, "..", "..")
TEST_CHART = os.path.join(E2E_TESTS_PATH, "helm_chart/my-test-chart")


@pytest.fixture
def populate_cluster():
    run_command(f"kubectl create namespace {TEST_NAMESPACE}")

    run_command(f"kubectl apply -f customResourceDescription-expecteddeploymentscales.yaml", cwd=f"{ROOT_PATH}")

    run_command(
        f"helm upgrade --install --debug --wait {TEST_RELEASE} {TEST_CHART} --namespace {TEST_NAMESPACE} --timeout 1800s",
        cwd=ABSOLUTE_PATH,
    )

    kubectl_exec_postgresql = subprocess.Popen(
        ["kubectl", "port-forward", "--namespace", TEST_NAMESPACE, f"{TEST_RELEASE}-postgresql-0", "5432"]
    )
    kubectl_exec_elasticsearch = subprocess.Popen(
        ["kubectl", "port-forward", "--namespace", TEST_NAMESPACE, "elasticsearch-master-0", "9200"]
    )
    time.sleep(5)  # Hack to wait for k exec to be up

    yield

    kubectl_exec_postgresql.kill()
    kubectl_exec_elasticsearch.kill()
    run_command(f"kubectl delete namespace {TEST_NAMESPACE} --grace-period=1")
