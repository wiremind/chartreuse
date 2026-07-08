import pytest
from pytest_mock.plugin import MockerFixture

import chartreuse.chartreuse_restore

from ..conftest import configure_os_environ_mock


def _configure_deployment_manager_mock(mocker: MockerFixture) -> "MockerFixture":
    mocked_kdm = mocker.MagicMock()
    mocker.patch("chartreuse.chartreuse_restore.KubernetesDeploymentManager", return_value=mocked_kdm)
    mocker.patch(
        "chartreuse.kubernetes_helper._get_namespace_from_kube",
        return_value="foo",
    )
    return mocked_kdm


def test_chartreuse_restore_restores_stopped_pods(mocker: MockerFixture) -> None:
    """
    Test that chartreuse_restore restores the Deployments that stop_pods left at 0 replicas.
    """
    mocked_kdm = _configure_deployment_manager_mock(mocker)
    mocker.patch("chartreuse.chartreuse_upgrade.get_version", return_value="5.0.0")
    configure_os_environ_mock(mocker=mocker, additional_environment={"HELM_CHART_APP_VERSION": "5.0.0"})

    chartreuse.chartreuse_restore.main()

    mocked_kdm.restore_stopped_pods.assert_called_once()


def test_chartreuse_restore_incompatible_helm_chart_version(mocker: MockerFixture) -> None:
    """
    Test that chartreuse_restore aborts before touching anything when the package and the
    Helm Chart don't have the same major.minor.
    """
    mocked_kdm = _configure_deployment_manager_mock(mocker)
    mocker.patch("chartreuse.chartreuse_upgrade.get_version", return_value="5.1.0")
    configure_os_environ_mock(mocker=mocker, additional_environment={"HELM_CHART_APP_VERSION": "5.0.0"})

    with pytest.raises(ValueError):
        chartreuse.chartreuse_restore.main()

    mocked_kdm.restore_stopped_pods.assert_not_called()


def test_chartreuse_restore_failure_is_fatal(mocker: MockerFixture) -> None:
    """
    Test that a restore failure propagates: the Job must fail so the deployment is marked
    as failed, instead of leaving workers silently stranded at 0 replicas.
    """
    mocked_kdm = _configure_deployment_manager_mock(mocker)
    mocked_kdm.restore_stopped_pods.side_effect = Exception("boom")
    mocker.patch("chartreuse.chartreuse_upgrade.get_version", return_value="5.0.0")
    configure_os_environ_mock(mocker=mocker, additional_environment={"HELM_CHART_APP_VERSION": "5.0.0"})

    with pytest.raises(Exception, match="boom"):
        chartreuse.chartreuse_restore.main()
