import logging

import discord

from .unit_conversion import *

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class Sandpiper(discord.Client):

    async def on_ready(self):
        logger.info('Sandpiper client started')

    async def on_message(self, msg: discord.Message):
        guild: discord.Guild = msg.guild
        channel: discord.TextChannel = msg.channel
        perms = channel.permissions_for(guild.me)
        if not perms.send_messages:
            return

        await self.mentioned_me(msg)
        await self.unit_conversions(msg)

    async def mentioned_me(self, msg):
        """
        What to do when a user mentions me

        :param msg: message with self mention
        :return: ``False`` if not mentioned
        """

        if self.user not in msg.mentions:
            return False

        await msg.channel.send('hi :)')

    async def unit_conversions(self, msg: discord.Message):
        """
        Scan a message for quantities like {5 km}, and reply with their
        conversions to either imperial or metric.

        :param msg: discord message to scan for quantities
        :return: ``False`` if no quantities were found
        """

        quantity_strs = quantity_pattern.findall(msg.content)
        if not quantity_strs:
            return False
        quantities = [q for qstr in quantity_strs
                      if (q := imperial_metric(qstr)) is not None]
        # I'm not specifying a precision here for the input because it will
        # often be an integer, and will raise a ValueError if I try to format
        # its precision
        conversion = '\n'.join([f'{q[0]:~P} = {q[1]:.2f~P}'
                                for q in quantities])
        if not conversion:
            return

        try:
            await msg.channel.send(conversion)
        except discord.HTTPException as e:
            logger.warning('when sending conversion embed: ', exc_info=e)
        except discord.InvalidArgument as e:
            logger.error('when sending conversion embed:', exc_info=e)
