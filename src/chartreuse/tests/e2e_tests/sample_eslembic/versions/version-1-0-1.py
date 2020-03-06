"""initial migration

Version: (1, 0, 1)
Down version: None
Created datetime: 2018-10-23 13:52:58+00:00
"""

VERSION = (1, 0, 1)
DOWN_VERSION = (1, 0, 0)
DESCRIPTION = "initial migration"


def upgrade(context):
    pass


def downgrade(context):
    pass


def set_data_migrations(migrations_manager):
    from eslembic.orm import EslembicModel

    class MyIndexModel(EslembicModel):
        name = "my_index"

        @classmethod
        def generate_documents(cls):
            return ()

    migrations_manager.add_migration(MyIndexModel, load_documents=True)
