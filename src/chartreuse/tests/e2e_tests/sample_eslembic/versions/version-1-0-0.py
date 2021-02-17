"""initial migration

Version: (1, 0, 0)
Down version: None
Created datetime: 2018-10-23 13:52:58+00:00
"""
from eslembic.orm import EslembicModel
from eslembic import op

VERSION = (1, 0, 0)
DOWN_VERSION = None
DESCRIPTION = "initial migration"


class MyIndexModel(EslembicModel):
    name = "my_index"


def upgrade(context):
    new_mapping = {"properties": {"id": {"type": "integer"}}}
    op.create_model(context, MyIndexModel, new_mapping=new_mapping)


def downgrade(context):
    op.delete_model(context, MyIndexModel)


def set_data_migrations(migrations_manager):
    pass
