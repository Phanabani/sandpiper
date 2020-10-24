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

        conversion_strs = await self.convert_time(msg.channel, conversion_strs)
        await self.convert_imperial_metric(msg.channel, conversion_strs)

    async def convert_time(self, channel: discord.TextChannel,
                           time_strs: List[str]) -> List[str]:
        """
        Convert a list of time strings (like "5:45 PM") to different users'
        timezones and reply with the conversions.

        :param channel: Discord channel to send conversions message to
        :param time_strs: a list of strings that may be valid times
        :returns: a list of strings that could not be converted
        """
        pass

    async def convert_imperial_metric(
            self, channel: discord.TextChannel,
            quantity_strs: List[str]) -> List[str]:
        """
        Convert a list of quantity strings (like "5 km") between imperial and
        metric and reply with the conversions.

        :param channel: Discord channel to send conversions message to
        :param quantity_strs: a list of strings that may be valid quantities
        :returns: a list of strings that could not be converted
        """

        conversions = []
        failed = []
        for qstr in quantity_strs:
            q = imperial_metric(qstr)
            if q is not None:
                conversions.append(f'{q[0]:.2f~P} = {q[1]:.2f~P}')
            else:
                failed.append(qstr)

        if conversions:
            await channel.send('\n'.join(conversions))

        return failed
