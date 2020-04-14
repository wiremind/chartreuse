import os

from typing import Dict, Union


def configure_os_environ_mock(mocker, additional_environment: Union[Dict[str, str], None] = None):

    new_environ: Dict[str, str] = dict(
        CHARTREUSE_ALEMBIC_ADDITIONAL_PARAMETERS="",
        CHARTREUSE_ALEMBIC_ALLOW_MIGRATION_FOR_EMPTY_DATABASE="1",
        CHARTREUSE_ELASTICSEARCH_URL="foo",
        CHARTREUSE_ENABLE_STOP_PODS="1",
        CHARTREUSE_ESLEMBIC_ENABLE_CLEAN="1",
        CHARTREUSE_ESLEMBIC_ENABLE_UPGRADE="1",
        CHARTREUSE_POSTGRESQL_URL="foo",
        CHARTREUSE_RELEASE_NAME="foo",
    )
    if additional_environment:
        new_environ.update(additional_environment)

    mocker.patch.dict(os.environ, new_environ)
