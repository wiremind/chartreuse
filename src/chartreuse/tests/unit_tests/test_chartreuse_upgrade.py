import chartreuse.chartreuse_upgrade

from .conftest import configure_chartreuse_mock
from ..conftest import configure_os_environ_mock


def test_chartreuse_upgrade_detected_migration_enabled_stop_pods(mocker):
    """
    Test that chartreuse_upgrades stop pods in case of detected migration.
    """
    configure_chartreuse_mock(mocker=mocker, is_migration_needed=True)
    mocked_stop_pods = mocker.patch("wiremind_kubernetes.KubernetesDeploymentManager.stop_pods")
    mocker.patch("wiremind_kubernetes.KubernetesDeploymentManager.start_pods")
    configure_os_environ_mock(mocker=mocker)

    chartreuse.chartreuse_upgrade.main()
    mocked_stop_pods.assert_called()


def test_chartreuse_upgrade_detected_migration_disabled_stop_pods(mocker):
    """
    Test that chartreuse_upgrades does not stop pods in case of detected migration but we disallow stop-pods.
    """
    configure_chartreuse_mock(mocker=mocker, is_migration_needed=True)
    mocked_stop_pods = mocker.patch("wiremind_kubernetes.KubernetesDeploymentManager.stop_pods")
    mocker.patch("wiremind_kubernetes.KubernetesDeploymentManager.start_pods")
    configure_os_environ_mock(mocker=mocker, additional_environment=dict(CHARTREUSE_ENABLE_STOP_PODS=""))

    chartreuse.chartreuse_upgrade.main()
    mocked_stop_pods.assert_not_called()


def test_chartreuse_upgrade_no_migration_disabled_stop_pods(mocker):
    """
    Test that chartreuse_upgrades does NOT stop pods in case of migration not needed.
    """
    configure_chartreuse_mock(mocker=mocker, is_migration_needed=False)
    mocked_stop_pods = mocker.patch("wiremind_kubernetes.KubernetesDeploymentManager.stop_pods")
    mocker.patch("wiremind_kubernetes.KubernetesDeploymentManager.start_pods")
    configure_os_environ_mock(mocker=mocker)

    chartreuse.chartreuse_upgrade.main()
    mocked_stop_pods.assert_not_called()
