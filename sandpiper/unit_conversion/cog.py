import logging
import re
from typing import List

import discord
import discord.ext.commands as commands

from ..common.embeds import Embeds
from .time_conversion import *
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

        conversion_strs = await self.convert_time(msg, conversion_strs)
        await self.convert_imperial_metric(msg.channel, conversion_strs)

    async def convert_time(self, msg: discord.Message,
                           time_strs: List[str]) -> List[str]:
        """
        Convert a list of time strings (like "5:45 PM") to different users'
        timezones and reply with the conversions.

        :param msg: Discord message that triggered the conversion
        :param time_strs: a list of strings that may be valid times
        :returns: a list of strings that could not be converted
        """

        user_data = self.bot.get_cog('UserData')
        if user_data is None:
            # User data cog couldn't be retrieved, so consider all conversions
            # failed
            return time_strs

        try:
            localized_times, failed = convert_time_to_user_timezones(
                user_data, msg.author.id, msg.guild, time_strs
            )
        except UserTimezoneUnset:
            cmd_prefix = self.bot.command_prefix(self.bot, msg)[-1]
            await Embeds.error(
                msg.channel,
                f"You haven't set your timezone yet. Type "
                f"`{cmd_prefix}help timezone set` for more info."
            )
            return time_strs

        if localized_times:
            output = []
            for tz_name, times in localized_times:
                times = ' | '.join(f'`{time.strftime(time_format)}`'
                                   for time in times)
                output.append(f'**{tz_name}**: {times}')
            await msg.channel.send('\n'.join(output))

        return failed

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
                conversions.append(f'`{q[0]:.2f~P}` = `{q[1]:.2f~P}`')
            else:
                failed.append(qstr)

        if conversions:
            await channel.send('\n'.join(conversions))

        return failed
