from collections import Callable
from pathlib import Path
from typing import Any

from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from sandpiper.user_data.models import Base

__all__ = ['run_with_migration_context', 'run_migrations']

config_path = Path(__file__, '../alembic.ini').resolve().absolute()
config = Config(str(config_path))
script = ScriptDirectory.from_config(config)
context = EnvironmentContext(config, script)

target_metadata = Base.metadata


async def run_with_migration_context(
        engine: AsyncEngine, fn: Callable[[MigrationContext], Any]
):
    def do(connection):
        migration_ctx = MigrationContext.configure(connection)
        return fn(migration_ctx)

    async with engine.begin() as conn:
        conn: AsyncConnection
        return await conn.run_sync(do)


def _do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        connection: AsyncConnection
        await connection.run_sync(_do_run_migrations)
