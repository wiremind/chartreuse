import os

from typing import Dict, Union


def configure_os_environ_mock(mocker, additional_environment: Union[Dict[str, str], None] = None):

    new_environ: Dict[str, str] = dict(
        CHARTREUSE_ALEMBIC_ADDITIONAL_PARAMETERS="",
        CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE="1",
        CHARTREUSE_ALEMBIC_URL="foo",
        CHARTREUSE_ENABLE_STOP_PODS="1",
        CHARTREUSE_ESLEMBIC_ENABLE_CLEAN="1",
        CHARTREUSE_ESLEMBIC_ENABLE_MIGRATE="1",
        CHARTREUSE_ESLEMBIC_URL="foo",
        CHARTREUSE_MIGRATE_IMAGE_PULL_SECRET="foo",
        CHARTREUSE_RELEASE_NAME="foo",
        CLASSIC_K8S_CONFIG=os.environ.get("CLASSIC_K8S_CONFIG", ""),
        CHARTREUSE_UPGRADE_BEFORE_DEPLOYMENT="",
        HELM_IS_INSTALL="",
    )
    if additional_environment:
        new_environ.update(additional_environment)

    mocker.patch.dict(os.environ, new_environ)
