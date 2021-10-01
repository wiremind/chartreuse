# import chartreuse.chartreuse_migrate

# from .conftest import (
#     TEST_NAMESPACE,
#     TEST_RELEASE,
#     POSTGRESQL_URL,
#     SAMPLE_ALEMBIC_PATH,
#     assert_sql_upgraded,
#     are_pods_scaled_down,
# )
# from ..conftest import configure_os_environ_mock


# def test_integration_chartreuse_upgrade(populate_cluster, mocker):
#     """
#     Test chartreuse upgrade, in post-install,post-upgrade configuration
#     """
#     mocker.patch("chartreuse.utils.alembic_migration_helper.ALEMBIC_DIRECTORY_PATH", SAMPLE_ALEMBIC_PATH)
#     mocker.patch("wiremind_kubernetes.kubernetes_helper._get_namespace_from_kube", return_value=TEST_NAMESPACE)
#     configure_os_environ_mock(
#         mocker=mocker,
#         additional_environment=dict(
#             CHARTREUSE_ALEMBIC_URL=POSTGRESQL_URL,
#             CHARTREUSE_MIGRATE_CONTAINER_IMAGE=f"docker.wiremind.fr/wiremind/devops/chartreuse:latest",
#             CHARTREUSE_RELEASE_NAME=TEST_RELEASE,
#         ),
#     )

#     chartreuse.chartreuse_upgrade.main()

#     assert_sql_upgraded()
#     assert not are_pods_scaled_down()
