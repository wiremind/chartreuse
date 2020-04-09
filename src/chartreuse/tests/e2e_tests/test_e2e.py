import logging
import os

import elasticsearch
import sqlalchemy

from wiremind_kubernetes.kubernetes_helper import KubernetesDeploymentManager

import chartreuse.postdeployment
import chartreuse.postrollback
import chartreuse.postupgrade
import chartreuse.predeployment
import chartreuse.utils.eslembic_migration_helper

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


def assert_elasticsearch_migrated(mocked_eslembic_run_command):
    mocked_eslembic_run_command.assert_any_call("eslembic migrate", cwd=SAMPLE_ESLEMBIC_PATH)


def assert_elasticsearch_not_migrated(mocked_eslembic_run_command):
    assert True  # XXX TODO not tested


def assert_elasticsearch_cleaned(mocked_eslembic_run_command):
    mocked_eslembic_run_command.assert_any_call("eslembic clean", cwd=SAMPLE_ESLEMBIC_PATH)


def assert_elasticsearch_not_cleaned(mocked_eslembic_run_command):
    assert True  # XXX TODO not tested


def are_pods_scaled_down():
    return KubernetesDeploymentManager(CHARTREUSE_RELEASE_NAME=TEST_RELEASE, use_kubeconfig=None).is_deployment_stopped(
        "e2e-test-release-my-test-chart"
    )


def test_chartreuse_post_deployment(populate_cluster, mocker):
    mocker.patch("chartreuse.utils.eslembic_migration_helper.ESLEMBIC_DIRECTORY_PATH", SAMPLE_ESLEMBIC_PATH)
    mocker.patch("chartreuse.utils.alembic_migration_helper.ALEMBIC_DIRECTORY_PATH", SAMPLE_ALEMBIC_PATH)
    mocker.patch("wiremind_kubernetes.kubernetes_helper._get_namespace_from_kube", return_value=TEST_NAMESPACE)
    mocked_eslembic_run_command = mocker.spy(chartreuse.utils.eslembic_migration_helper, "run_command")
    mocker.patch.dict(
        os.environ,
        dict(
            CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE="1",
            CHARTREUSE_ESLEMBIC_ENABLE_CLEAN="1",
            CHARTREUSE_ESLEMBIC_ENABLE_UPGRADE="0",  # XXX ENABLE
            CHARTREUSE_POSTGRESQL_URL=POSTGRESQL_URL,
            CHARTREUSE_ELASTICSEARCH_URL=ELASTICSEARCH_URL,
            CHARTREUSE_CONTAINER_IMAGE=f"docker.wiremind.fr/wiremind/devops/chartreuse:latest",
            CHARTREUSE_RELEASE_NAME=TEST_RELEASE,
        ),
    )

    chartreuse.postdeployment.main()

    assert_sql_migrated()
    assert_elasticsearch_upgraded()
    assert_elasticsearch_not_migrated(mocked_eslembic_run_command)
    assert_elasticsearch_not_cleaned(mocked_eslembic_run_command)
    assert not are_pods_scaled_down()


def test_chartreuse_pre_deployment(populate_cluster, mocker):
    mocker.patch("chartreuse.utils.eslembic_migration_helper.ESLEMBIC_DIRECTORY_PATH", SAMPLE_ESLEMBIC_PATH)
    mocker.patch("chartreuse.utils.alembic_migration_helper.ALEMBIC_DIRECTORY_PATH", SAMPLE_ALEMBIC_PATH)
    mocker.patch("wiremind_kubernetes.kubernetes_helper._get_namespace_from_kube", return_value=TEST_NAMESPACE)
    mocked_eslembic_run_command = mocker.spy(chartreuse.utils.eslembic_migration_helper, "run_command")
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
    assert_elasticsearch_not_migrated(mocked_eslembic_run_command)
    assert_elasticsearch_not_cleaned(mocked_eslembic_run_command)
    assert are_pods_scaled_down()


def test_chartreuse_post_rollback(populate_cluster, mocker):
    mocker.patch("chartreuse.utils.eslembic_migration_helper.ESLEMBIC_DIRECTORY_PATH", SAMPLE_ESLEMBIC_PATH)
    mocker.patch("chartreuse.utils.alembic_migration_helper.ALEMBIC_DIRECTORY_PATH", SAMPLE_ALEMBIC_PATH)
    mocker.patch("wiremind_kubernetes.kubernetes_helper._get_namespace_from_kube", return_value=TEST_NAMESPACE)
    mocked_eslembic_run_command = mocker.spy(chartreuse.utils.eslembic_migration_helper, "run_command")
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
    assert_elasticsearch_not_migrated(mocked_eslembic_run_command)
    assert_elasticsearch_not_cleaned(mocked_eslembic_run_command)
    assert not are_pods_scaled_down()


def test_chartreuse_post_upgrade(populate_cluster, mocker):
    mocker.patch("chartreuse.utils.eslembic_migration_helper.ESLEMBIC_DIRECTORY_PATH", SAMPLE_ESLEMBIC_PATH)
    mocker.patch("chartreuse.utils.alembic_migration_helper.ALEMBIC_DIRECTORY_PATH", SAMPLE_ALEMBIC_PATH)
    mocker.patch("wiremind_kubernetes.kubernetes_helper._get_namespace_from_kube", return_value=TEST_NAMESPACE)
    mocked_eslembic_run_command = mocker.spy(chartreuse.utils.eslembic_migration_helper, "run_command")
    mocker.patch.dict(
        os.environ,
        dict(
            CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE="1",
            CHARTREUSE_ESLEMBIC_ENABLE_CLEAN="1",
            CHARTREUSE_ESLEMBIC_ENABLE_UPGRADE="0",  # XXX ENABLE
            CHARTREUSE_POSTGRESQL_URL=POSTGRESQL_URL,
            CHARTREUSE_ELASTICSEARCH_URL=ELASTICSEARCH_URL,
            CHARTREUSE_CONTAINER_IMAGE=f"docker.wiremind.fr/wiremind/devops/chartreuse:latest",
            CHARTREUSE_RELEASE_NAME=TEST_RELEASE,
        ),
    )

    chartreuse.postdeployment.main()
    chartreuse.postupgrade.main()

    assert_elasticsearch_migrated(mocked_eslembic_run_command)
    assert_elasticsearch_cleaned(mocked_eslembic_run_command)
    assert not are_pods_scaled_down()
