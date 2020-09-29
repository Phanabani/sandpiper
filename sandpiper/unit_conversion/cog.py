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
            logger.debug('')
            return

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
            logger.warning('Failed to send unit conversion: ', exc_info=e)
        except discord.InvalidArgument as e:
            logger.error('Failed to send unit conversion: ', exc_info=e)
