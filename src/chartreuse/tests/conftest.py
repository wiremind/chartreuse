import os

from pytest_mock.plugin import MockerFixture


def configure_os_environ_mock(mocker: MockerFixture, additional_environment: dict[str, str] | None = None) -> None:
    new_environ: dict[str, str] = {
        "CHARTREUSE_ALEMBIC_ADDITIONAL_PARAMETERS": "",
        "CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE": "1",
        "CHARTREUSE_ALEMBIC_URL": "foo",
        "CHARTREUSE_ENABLE_STOP_PODS": "1",
        "CHARTREUSE_MIGRATE_IMAGE_PULL_SECRET": "foo",
        "CHARTREUSE_RELEASE_NAME": "foo",
        "RUN_TEST_IN_KIND": os.environ.get("RUN_TEST_IN_KIND", ""),
        "CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT": "",
        "HELM_IS_INSTALL": "",
        "CHARTREUSE_MULTI_CONFIG_PATH": "/mock/config.yaml",
        # Add Kubernetes environment variables to prevent config loading
        "KUBERNETES_SERVICE_HOST": "localhost",
        "KUBERNETES_SERVICE_PORT": "443",
    }
    if additional_environment:
        new_environ.update(additional_environment)

    mocker.patch.dict(os.environ, new_environ)

    # Mock the file operations for the config path
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.path.isfile", return_value=True)

    # Mock the open operation for kubernetes token file
    mock_open = mocker.mock_open(read_data="mock-token")
    mocker.patch("builtins.open", mock_open)

    # Mock the config loader
    mock_config = [
        {
            "name": "default",
            "alembic_directory_path": "/app/alembic",
            "alembic_config_file_path": "alembic.ini",
            "url": "foo",
            "allow_migration_for_empty_database": True,
            "additional_parameters": "",
        }
    ]
    mocker.patch("chartreuse.chartreuse_upgrade.load_multi_database_config", return_value=mock_config)


def configure_chartreuse_mock(
    mocker: MockerFixture,
    is_migration_needed: bool,
) -> None:
    """
    Configure a mock for Chartreuse object.
    """
    mock_chartreuse = mocker.MagicMock()
    mock_chartreuse.is_migration_needed = is_migration_needed
    mocker.patch("chartreuse.chartreuse_upgrade.Chartreuse", return_value=mock_chartreuse)

    # Mock KubernetesDeploymentManager in all the right places
    mock_kdm = mocker.MagicMock()
    mocker.patch("wiremind_kubernetes.KubernetesDeploymentManager", return_value=mock_kdm)
    mocker.patch("chartreuse.chartreuse_upgrade.KubernetesDeploymentManager", return_value=mock_kdm)

    # Also mock the kubernetes config loading to prevent the config errors
    mocker.patch("kubernetes.config.load_incluster_config")
    mocker.patch("wiremind_kubernetes.kube_config.load_kubernetes_config")
