import logging
import re
from typing import List

import discord
import discord.ext.commands as commands

from .unit_conversion import *

logger = logging.getLogger('sandpiper.unit_conversion')

conversion_pattern = re.compile(r'{(.+?)}')


class UnitConversion(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener(name='on_message')
    async def conversions(self, msg: discord.Message):
        """
        Scan a message for conversion strings.

        :param msg: Discord message to scan for conversions
        """
        if msg.author == self.bot.user:
            return

        conversion_strs = conversion_pattern.findall(msg.content)
        if not conversion_strs:
            return

        if await self.imperial_metric_conversion(msg.channel, conversion_strs):
            return

    async def imperial_metric_conversion(
            self, channel: discord.TextChannel,
            quantity_strs: List[str]) -> bool:
        """
        Convert a list of quantity strings (like "5 km") between imperial and
        metric and reply with the conversions.

        :param channel: Discord channel to send conversions message to
        :param quantity_strs: a list of strings that may be valid quantities
        """

        quantities = [q for qstr in quantity_strs
                      if (q := imperial_metric(qstr)) is not None]
        if not quantities:
            return False
        conversion = '\n'.join(f'{q[0]:.2f~P} = {q[1]:.2f~P}'
                               for q in quantities)
        await channel.send(conversion)
        return True
