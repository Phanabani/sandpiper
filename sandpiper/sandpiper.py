import logging

from discord.ext.commands import Bot

from . import Config

logger = logging.getLogger('sandpiper')


# noinspection PyMethodMayBeStatic
class Sandpiper(Bot):

    def __init__(self, config: Config):
        super().__init__(
            command_prefix=config.command_prefix,
            description=config.description
        )

    async def on_ready(self):
        logger.info('Sandpiper client started')
