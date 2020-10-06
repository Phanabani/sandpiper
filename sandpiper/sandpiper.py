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
        self.load_extension('sandpiper.user_info')

    async def on_ready(self):
        logger.info('Sandpiper client started')
