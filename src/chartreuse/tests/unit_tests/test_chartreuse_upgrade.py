import chartreuse.chartreuse_upgrade
import pytest

from chartreuse import get_version

from ..conftest import configure_os_environ_mock
from .conftest import configure_chartreuse_mock


def test_chartreuse_upgrade_detected_migration_enabled_stop_pods(mocker):
    """
    Test that chartreuse_upgrades stop pods in case of detected migration.
    """
    configure_chartreuse_mock(mocker=mocker, is_migration_needed=True)
    mocked_stop_pods = mocker.patch("wiremind_kubernetes.KubernetesDeploymentManager.stop_pods")
    mocker.patch("wiremind_kubernetes.KubernetesDeploymentManager.start_pods")
    configure_os_environ_mock(mocker=mocker, additional_environment={"HELM_CHART_VERSION": get_version()})

    chartreuse.chartreuse_upgrade.main()
    mocked_stop_pods.assert_called()


def test_chartreuse_upgrade_detected_migration_disabled_stop_pods(mocker):
    """
    Test that chartreuse_upgrades does not stop pods in case of detected migration but we disallow stop-pods.
    """
    configure_chartreuse_mock(mocker=mocker, is_migration_needed=True)
    mocked_stop_pods = mocker.patch("wiremind_kubernetes.KubernetesDeploymentManager.stop_pods")
    mocker.patch("wiremind_kubernetes.KubernetesDeploymentManager.start_pods")
    configure_os_environ_mock(
        mocker=mocker, additional_environment=dict(CHARTREUSE_ENABLE_STOP_PODS="", HELM_CHART_VERSION=get_version())
    )

    chartreuse.chartreuse_upgrade.main()
    mocked_stop_pods.assert_not_called()


def test_chartreuse_upgrade_no_migration_disabled_stop_pods(mocker):
    """
    Test that chartreuse_upgrades does NOT stop pods in case of migration not needed.
    """
    configure_chartreuse_mock(mocker=mocker, is_migration_needed=False)
    mocked_stop_pods = mocker.patch("wiremind_kubernetes.KubernetesDeploymentManager.stop_pods")
    mocker.patch("wiremind_kubernetes.KubernetesDeploymentManager.start_pods")
    configure_os_environ_mock(mocker=mocker, additional_environment={"HELM_CHART_VERSION": get_version()})

    chartreuse.chartreuse_upgrade.main()
    mocked_stop_pods.assert_not_called()


@pytest.mark.parametrize(
    "helm_chart_version, package_version, should_raise",
    [
        (None, "1.2.3", True),
        ("", "1.2.9", True),
        ("1.2.4", "1.2.4", False),
        ("1.2.9", "1.2.7", False),
        ("1.2.1", "1.2.9", False),
        ("2.0.0", "", True),
        ("2.0.0", "2.2.3", True),
        ("2.2.0", "1.8.5", True),
    ],
)
def test_chartreuse_upgrade_compatibility_check(mocker, helm_chart_version, package_version, should_raise):
    """
    Test that chartreuse_upgrade deals as expected with compatibility with the package version and the
    Helm Chart version.
    """
    mocker.patch("chartreuse.chartreuse_upgrade.get_version", return_value=package_version)
    additional_environment = {"HELM_CHART_VERSION": helm_chart_version} if helm_chart_version is not None else {}
    configure_os_environ_mock(mocker=mocker, additional_environment=additional_environment)
    configure_chartreuse_mock(mocker=mocker, is_migration_needed=False)

    if should_raise:
        with pytest.raises(Exception) as excinfo:
            chartreuse.chartreuse_upgrade.main()
            assert "ABORTING!" in str(excinfo.value)
    else:
        chartreuse.chartreuse_upgrade.main()
