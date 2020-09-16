import logging
import time

from wiremind_kubernetes.kubernetes_helper import KubernetesHelper

from .conftest import (
    TEST_NAMESPACE,
    TEST_RELEASE,
    are_pods_scaled_down,
    assert_elasticsearch_upgraded,
    assert_sql_upgraded,
)

logger = logging.getLogger(__name__)


def assert_elasticsearch_migrated():
    # Only test that a job has been created with post-upgrade chartreuse command
    client_batchv1_api = KubernetesHelper(should_load_kubernetes_config=False).client_batchv1_api
    job = client_batchv1_api.read_namespaced_job(namespace=TEST_NAMESPACE, name=f"{TEST_RELEASE}-chartreuse-migrate")
    assert job.status.succeeded == 1


def wait_for_job_to_be_finished():
    client_batchv1_api = KubernetesHelper(should_load_kubernetes_config=False).client_batchv1_api

    for _ in range(1, 10):
        job = client_batchv1_api.read_namespaced_job(
            namespace=TEST_NAMESPACE, name=f"{TEST_RELEASE}-chartreuse-migrate"
        )
        if not job.status.succeeded == 1:
            logger.info("Waiting for migrate job to be finished...")
            time.sleep(5)
        else:
            # OK!
            return
        assert job.status.succeeded == 1


def test_chartreuse_blackbox_post_upgrade(populate_cluster_with_chartreuse_post_upgrade, mocker):
    """
    Test chartreuse considered as a blackbox, in post-install,post-upgrade configuration
    """
    wait_for_job_to_be_finished()
    assert_sql_upgraded()
    assert_elasticsearch_upgraded()
    assert_elasticsearch_migrated()
    assert not are_pods_scaled_down()


def test_chartreuse_blackbox_pre_upgrade(populate_cluster_with_chartreuse_pre_upgrade, mocker):
    """
    Test chartreuse considered as a blackbox, in pre-upgrade configuration
    """
    time.sleep(10)  # Hack to wait for everything to be finished (like pods to be ready)
    wait_for_job_to_be_finished()
    assert_sql_upgraded()
    assert_elasticsearch_upgraded()
    assert_elasticsearch_migrated()
    assert not are_pods_scaled_down()
