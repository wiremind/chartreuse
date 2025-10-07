# Note: Not a fixture
from pytest_mock.plugin import MockerFixture


def configure_chartreuse_mock(
    mocker: MockerFixture, is_migration_needed: bool = True
) -> None:
    mocker.patch("chartreuse.chartreuse_upgrade.Chartreuse.__init__", return_value=None)
    mocker.patch(
        "chartreuse.chartreuse_upgrade.Chartreuse.is_migration_needed",
        new_callable=mocker.PropertyMock,
        return_value=is_migration_needed,
        create=True,
    )
    mocker.patch("chartreuse.chartreuse_upgrade.Chartreuse.upgrade")
    mocker.patch(
        "wiremind_kubernetes.kubernetes_helper._get_namespace_from_kube",
        return_value="foo",
    )
