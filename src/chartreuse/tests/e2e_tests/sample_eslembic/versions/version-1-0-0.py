"""initial migration

Version: (1, 0, 0)
Down version: None
Created datetime: 2018-10-23 13:52:58+00:00
"""

VERSION = (1, 0, 0)
DOWN_VERSION = None
DESCRIPTION = "initial migration"


def upgrade(context):
    from eslembic import op
    from eslembic.orm import EslembicModel

    class MyIndexModel(EslembicModel):
        name = "my_index"

    op.create_model(context, MyIndexModel)


def downgrade(context):
    from eslembic import op
    from eslembic.orm import EslembicModel

    class MyIndexModel(EslembicModel):
        name = "my_index"

    op.delete_model(context, MyIndexModel)


def set_data_migrations(migrations_manager):
    pass
