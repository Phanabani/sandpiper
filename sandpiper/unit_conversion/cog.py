import logging

import discord
import discord.ext.commands as commands

from .unit_conversion import *

logger = logging.getLogger('sandpiper')


class UnitConversion(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener(name='on_message')
    async def unit_conversions(self, msg: discord.Message):
        """
        Scan a message for quantities like {5 km}, and reply with their
        conversions to either imperial or metric.

        :param msg: discord message to scan for quantities
        :return: ``False`` if no quantities were found
        """

        if msg.author == self.bot.user:
            return

        quantity_strs = quantity_pattern.findall(msg.content)
        if not quantity_strs:
            return

        perms = msg.channel.permissions_for(msg.guild.me)
        if not perms.send_messages:
            logger.debug(f'Lacking send_messages permission '
                         f'(guild: {msg.guild} channel: {msg.channel})')
            return

        # Create output strings for all quantities encountered in the message
        quantities = [q for qstr in quantity_strs
                      if (q := imperial_metric(qstr)) is not None]
        if not quantities:
            return
        conversion = '\n'.join([f'{q[0]:.2f~P} = {q[1]:.2f~P}'
                                for q in quantities])

        try:
            await msg.channel.send(conversion)
        except discord.HTTPException as e:
            logger.warning('Failed to send unit conversion: ', exc_info=e)
        except discord.InvalidArgument as e:
            logger.error('Failed to send unit conversion: ', exc_info=e)
