import os

from pytest_mock.plugin import MockerFixture


def configure_os_environ_mock(
    mocker: MockerFixture, additional_environment: dict[str, str] | None = None
) -> None:
    new_environ: dict[str, str] = dict(
        CHARTREUSE_ALEMBIC_ADDITIONAL_PARAMETERS="",
        CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE="1",
        CHARTREUSE_ALEMBIC_URL="foo",
        CHARTREUSE_ENABLE_STOP_PODS="1",
        CHARTREUSE_MIGRATE_IMAGE_PULL_SECRET="foo",
        CHARTREUSE_RELEASE_NAME="foo",
        RUN_TEST_IN_KIND=os.environ.get("RUN_TEST_IN_KIND", ""),
        CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT="",
        HELM_IS_INSTALL="",
    )
    if additional_environment:
        new_environ.update(additional_environment)

    mocker.patch.dict(os.environ, new_environ)
