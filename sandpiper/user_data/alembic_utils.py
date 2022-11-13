__all__ = ["get_current_heads", "stamp", "upgrade"]

from collections.abc import Callable
import logging
from pathlib import Path
from typing import Any

from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from sandpiper.user_data.models import Base

logger = logging.getLogger(__name__)

config_path = Path(__file__, "../alembic.ini").resolve().absolute()
config = Config(str(config_path))
script = ScriptDirectory.from_config(config)
context = EnvironmentContext(config, script)

target_metadata = Base.metadata


async def _run_sync(engine: AsyncEngine, fn: Callable[[AsyncConnection], Any]):
    async with engine.begin() as connection:
        connection: AsyncConnection
        try:
            return await connection.run_sync(fn)
        except Exception as e:
            logger.error("Unhandled exception in Alembic run_sync", exc_info=e)
            raise


async def get_current_heads(engine: AsyncEngine) -> tuple[str]:
    def fn(connection: AsyncConnection):
        migration_ctx = MigrationContext.configure(connection)
        return migration_ctx.get_current_heads()

    return await _run_sync(engine, fn)


async def stamp(engine: AsyncEngine, revision: str):
    def fn(connection: AsyncConnection):
        migration_ctx = MigrationContext.configure(connection)
        return migration_ctx.stamp(script, revision)

    await _run_sync(engine, fn)


async def upgrade(engine: AsyncEngine, revision: str):
    def do_upgrade(rev, context):
        return script._upgrade_revs(revision, rev)

    def fn(connection: AsyncConnection):
        context.configure(connection, target_metadata=target_metadata, fn=do_upgrade)
        with context.begin_transaction():
            context.run_migrations()

    await _run_sync(engine, fn)
