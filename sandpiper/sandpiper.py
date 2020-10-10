import logging

from discord.ext.commands import Bot

from . import Config

logger = logging.getLogger('sandpiper')


# noinspection PyMethodMayBeStatic
class Sandpiper(Bot):

    def __init__(self, config: Config.Bot):
        super().__init__(
            command_prefix=config.command_prefix,
            description=config.description
        )
        self.load_extension('sandpiper.unit_conversion')

    async def on_connect(self):
        logger.info('Client connected')

    async def on_disconnect(self):
        logger.info('Client disconnected')

    async def on_resumed(self):
        logger.info('Session resumed')

    async def on_ready(self):
        logger.info('Client started')

    async def on_error(self, event: str, *args, **kwargs):
        logger.error(f'Error in event {event}', exc_info=True)
