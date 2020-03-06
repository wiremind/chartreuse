"""${description}

Version: ${version}
Down version: ${down_version}
Created datetime: ${created_datetime}
"""

VERSION = ${repr(version)}
DOWN_VERSION = ${repr(down_version)}
DESCRIPTION = ${repr(description)}


def upgrade(context):
    pass


def downgrade(context):
    pass


def set_data_migrations(migration_manager):
    pass
