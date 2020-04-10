import logging
import os

import elasticsearch
import sqlalchemy

import chartreuse.postdeployment
import chartreuse.postrollback
import chartreuse.postupgrade
import chartreuse.predeployment
import chartreuse.utils.eslembic_migration_helper
from wiremind_kubernetes.kubernetes_helper import KubernetesDeploymentManager, KubernetesHelper

from .conftest import E2E_TESTS_PATH, TEST_NAMESPACE, TEST_RELEASE

# Calculated from deployed test helm chart + kubectl exec
ELASTICSEARCH_URL = "http://localhost:9200"
POSTGRESQL_URL = f"postgresql://foo:foo@localhost/foo?sslmode=prefer"

SAMPLE_ESLEMBIC_PATH = os.path.join(E2E_TESTS_PATH, "sample_eslembic")
SAMPLE_ALEMBIC_PATH = os.path.join(E2E_TESTS_PATH, "sample_alembic")


logging.getLogger().setLevel(logging.INFO)


def assert_sql_migrated():
    assert sqlalchemy.create_engine(POSTGRESQL_URL).table_names() == ["alembic_version", "migrated"]


def assert_sql_not_migrated():
    assert not sqlalchemy.create_engine(POSTGRESQL_URL).table_names() == ["alembic_version", "migrated"]


def assert_elasticsearch_upgraded():
    es: elasticsearch.Elasticsearch = elasticsearch.Elasticsearch([ELASTICSEARCH_URL])
    assert "my_index-0" in es.indices.get("*").keys()


def assert_elasticsearch_not_upgraded():
    es: elasticsearch.Elasticsearch = elasticsearch.Elasticsearch([ELASTICSEARCH_URL])
    assert "my_index-0" not in es.indices.get("*").keys()


def assert_elasticsearch_migrating():
    # Only test that a job has been created with post-upgrade chartreuse command
    client_batchv1_api = KubernetesHelper(use_kubeconfig=None).client_batchv1_api
    job = client_batchv1_api.read_namespaced_job(
        namespace=TEST_NAMESPACE, name=f"{TEST_RELEASE}-chartreuse-post-upgrade"
    )
    env = job.spec.template.spec.containers[0].env
    assert env[0].to_dict() == {"name": "ELASTICSEARCH_URL", "value": ELASTICSEARCH_URL, "value_from": None}
    assert env[1].to_dict() == {"name": "CHARTREUSE_ESLEMBIC_ENABLE_CLEAN", "value": "1", "value_from": None}


def are_pods_scaled_down():
    return KubernetesDeploymentManager(release_name=TEST_RELEASE, use_kubeconfig=None).is_deployment_stopped(
        "e2e-test-release-my-test-chart"
    )


def test_chartreuse_post_deployment(populate_cluster, mocker):
    mocker.patch("chartreuse.utils.eslembic_migration_helper.ESLEMBIC_DIRECTORY_PATH", SAMPLE_ESLEMBIC_PATH)
    mocker.patch("chartreuse.utils.alembic_migration_helper.ALEMBIC_DIRECTORY_PATH", SAMPLE_ALEMBIC_PATH)
    mocker.patch("wiremind_kubernetes.kubernetes_helper._get_namespace_from_kube", return_value=TEST_NAMESPACE)
    mocker.patch.dict(
        os.environ,
        dict(
            CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE="1",
            CHARTREUSE_ESLEMBIC_ENABLE_CLEAN="1",
            CHARTREUSE_ESLEMBIC_ENABLE_UPGRADE="0",  # XXX ENABLE
            CHARTREUSE_POSTGRESQL_URL=POSTGRESQL_URL,
            CHARTREUSE_ELASTICSEARCH_URL=ELASTICSEARCH_URL,
            CHARTREUSE_POST_UPGRADE_CONTAINER_IMAGE=f"docker.wiremind.fr/wiremind/devops/chartreuse:latest",
            CHARTREUSE_RELEASE_NAME=TEST_RELEASE,
        ),
    )

    chartreuse.postdeployment.main()

    assert_sql_migrated()
    assert_elasticsearch_upgraded()
    assert not are_pods_scaled_down()


def test_chartreuse_pre_deployment(populate_cluster, mocker):
    mocker.patch("chartreuse.utils.eslembic_migration_helper.ESLEMBIC_DIRECTORY_PATH", SAMPLE_ESLEMBIC_PATH)
    mocker.patch("chartreuse.utils.alembic_migration_helper.ALEMBIC_DIRECTORY_PATH", SAMPLE_ALEMBIC_PATH)
    mocker.patch("wiremind_kubernetes.kubernetes_helper._get_namespace_from_kube", return_value=TEST_NAMESPACE)
    mocker.patch.dict(
        os.environ,
        dict(
            CHARTREUSE_POSTGRESQL_URL=POSTGRESQL_URL,
            CHARTREUSE_ELASTICSEARCH_URL=ELASTICSEARCH_URL,
            CHARTREUSE_RELEASE_NAME=TEST_RELEASE,
            CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE="1",
        ),
    )

    chartreuse.predeployment.main()

    assert_sql_not_migrated()
    assert_elasticsearch_not_upgraded()
    assert are_pods_scaled_down()


def test_chartreuse_post_rollback(populate_cluster, mocker):
    mocker.patch("chartreuse.utils.eslembic_migration_helper.ESLEMBIC_DIRECTORY_PATH", SAMPLE_ESLEMBIC_PATH)
    mocker.patch("chartreuse.utils.alembic_migration_helper.ALEMBIC_DIRECTORY_PATH", SAMPLE_ALEMBIC_PATH)
    mocker.patch("wiremind_kubernetes.kubernetes_helper._get_namespace_from_kube", return_value=TEST_NAMESPACE)
    mocker.patch.dict(
        os.environ,
        dict(
            CHARTREUSE_POSTGRESQL_URL=POSTGRESQL_URL,
            CHARTREUSE_ELASTICSEARCH_URL=ELASTICSEARCH_URL,
            CHARTREUSE_RELEASE_NAME=TEST_RELEASE,
        ),
    )

    chartreuse.postrollback.main()

    assert_sql_not_migrated()
    assert_elasticsearch_not_upgraded()
    assert not are_pods_scaled_down()


def test_chartreuse_post_upgrade(populate_cluster, mocker):
    mocker.patch("chartreuse.utils.eslembic_migration_helper.ESLEMBIC_DIRECTORY_PATH", SAMPLE_ESLEMBIC_PATH)
    mocker.patch("chartreuse.utils.alembic_migration_helper.ALEMBIC_DIRECTORY_PATH", SAMPLE_ALEMBIC_PATH)
    mocker.patch("wiremind_kubernetes.kubernetes_helper._get_namespace_from_kube", return_value=TEST_NAMESPACE)
    mocker.patch.dict(
        os.environ,
        dict(
            CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE="1",
            CHARTREUSE_ESLEMBIC_ENABLE_CLEAN="1",
            CHARTREUSE_ESLEMBIC_ENABLE_UPGRADE="0",  # XXX ENABLE
            CHARTREUSE_POSTGRESQL_URL=POSTGRESQL_URL,
            CHARTREUSE_ELASTICSEARCH_URL=ELASTICSEARCH_URL,
            CHARTREUSE_POST_UPGRADE_CONTAINER_IMAGE=f"docker.wiremind.fr/wiremind/devops/chartreuse:latest",
            CHARTREUSE_RELEASE_NAME=TEST_RELEASE,
        ),
    )

    chartreuse.postdeployment.main()
    chartreuse.postupgrade.main()

    assert_elasticsearch_migrating()
    assert not are_pods_scaled_down()
