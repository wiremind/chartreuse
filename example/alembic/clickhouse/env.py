import logging

from alembic import context
from sqlalchemy import engine_from_config, pool

# inspired by https://github.com/xzkostyan/clickhouse-sqlalchemy-alembic-example/blob/main/simple/migrations/env.py

config = context.config
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)
for key in list(logging.root.manager.loggerDict.keys()):
    if "alembic" in key:
        logging.getLogger(key).disabled = False

from cyrillic.models import ClickhouseBase  # noqa: E402

target_metadata = ClickhouseBase.metadata

# Currently there is an issue in clickhouse-sqlalchemy https://github.com/xzkostyan/clickhouse-sqlalchemy/pull/369
# makes Alembic mimic what clickhouse_sqlalchemy.alembic is expecting (designed for Alembic 1.5.8)
# https://github.com/sqlalchemy/alembic/blob/rel_1_5_8/alembic/util/sqla_compat.py#L180
from alembic.util import sqla_compat  # noqa: E402

sqla_compat._reflect_table = lambda inspector, table, include_cols: inspector.reflect_table(table, None)
# patch before next import
from clickhouse_sqlalchemy.alembic.dialect import include_object, patch_alembic_version  # noqa: E402

REPLICATION = True


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    if REPLICATION:
        kwargs = {
            "cluster": "wm",
            "table_path": "/clickhouse/tables/wm/wiremind/alembic_version",
            "replica_name": "{replica}",
        }
    else:
        kwargs = {}

    with context.begin_transaction():
        patch_alembic_version(context, **kwargs)
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object)

        if REPLICATION:
            kwargs = {
                "cluster": "wm",
                "table_path": "/clickhouse/tables/wm/wiremind/alembic_version",
                "replica_name": "{replica}",
            }
        else:
            kwargs = {}

        with context.begin_transaction():
            patch_alembic_version(context, **kwargs)
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
