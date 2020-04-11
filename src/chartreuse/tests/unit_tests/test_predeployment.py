import chartreuse.predeployment

from .conftest import configure_chartreuse_mock
from ..conftest import configure_os_environ_mock


def test_predeployment_detected_migration_enabled_stop_pods(mocker):
    """
    Test that pretdeployments stop pods in case of detected migration.
    """
    configure_chartreuse_mock(mocker=mocker, is_migration_needed=True)
    mocked_stop_pods = mocker.patch("chartreuse.predeployment.stop_pods")
    configure_os_environ_mock(mocker=mocker)

    chartreuse.predeployment.main()
    mocked_stop_pods.assert_called()


def test_predeployment_detected_migration_disabled_stop_pods(mocker):
    """
    Test that predeployments does not stop pods in case of detected migration but we disallow stop-pods.
    """
    configure_chartreuse_mock(mocker=mocker, is_migration_needed=True)
    configure_os_environ_mock(mocker=mocker, additional_environment=dict(CHARTREUSE_ENABLE_STOP_PODS=""))

    mocked_stop_pods = mocker.patch("chartreuse.predeployment.stop_pods")
    chartreuse.predeployment.main()
    mocked_stop_pods.assert_not_called()


def test_predeployment_no_migration_disabled_stop_pods(mocker):
    """
    Test that postdeployments does NOT stop pods in case of migration not needed.
    """
    configure_chartreuse_mock(mocker=mocker, is_migration_needed=False)
    configure_os_environ_mock(mocker=mocker)

    mocked_stop_pods = mocker.patch("chartreuse.predeployment.stop_pods")
    chartreuse.predeployment.main()
    mocked_stop_pods.assert_not_called()
