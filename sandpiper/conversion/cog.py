import logging
import re
from typing import *

import discord
import discord.ext.commands as commands

from sandpiper.common.embeds import Embeds
from sandpiper.common.time import time_format
from sandpiper.conversion.time_conversion import *
import sandpiper.conversion.unit_conversion as unit_conversion
from sandpiper.user_data import DatabaseUnavailable, UserData

logger = logging.getLogger('sandpiper.unit_conversion')

conversion_pattern = re.compile(
    r'{'
    r'(?P<quantity>.+?)'
    r'(?: ?> ?(?P<to_unit>.+?))?'
    r'}'
)


class Conversion(commands.Cog):

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
        await self.convert_measurements(msg.channel, conversion_strs)

    async def convert_time(
            self, msg: discord.Message, time_strs: List[Tuple[str, str]]
    ) -> List[Tuple[str, str]]:
        """
        Convert a list of time strings (like "5:45 PM") to different users'
        timezones and reply with the conversions.

        :param msg: Discord message that triggered the conversion
        :param time_strs: a list of strings that may be valid times
        :returns: a list of strings that could not be converted
        """

        user_data: UserData = self.bot.get_cog('UserData')
        if user_data is None:
            # User data cog couldn't be retrieved, so consider all conversions
            # failed
            return time_strs

        try:
            db = await user_data.get_database()
        except DatabaseUnavailable:
            return time_strs

        localized_times, failed, runtime_msgs = await convert_time_to_user_timezones(
            db, msg.author.id, msg.guild, time_strs
        )
        if runtime_msgs.exceptions:
            await Embeds.error(
                msg.channel, '\n'.join(str(e) for e in runtime_msgs.exceptions)
            )
            return time_strs

        if localized_times:
            output = runtime_msgs.info
            for tz_name, times in localized_times:
                times = ' | '.join(
                    f'`{time.strftime(time_format)}`' for time in times
                )
                output.append(f'**{tz_name}**: {times}')
            await msg.channel.send('\n'.join(output))

        return failed

    async def convert_measurements(
            self, channel: discord.TextChannel,
            quantity_strs: List[str]
    ) -> List[Tuple[str, str]]:
        """
        Convert a list of quantity strings (like "5 km") between imperial and
        metric and reply with the conversions.

        :param channel: Discord channel to send conversions message to
        :param quantity_strs: a list of strings that may be valid quantities
        :returns: a list of strings that could not be converted
        """

        conversions = []
        failed: List[Tuple[str, str]] = []
        for qstr, unit in quantity_strs:
            q = unit_conversion.convert_measurement(qstr, unit)
            if q is not None:
                conversions.append(f'`{q[0]:.2f~P}` = `{q[1]:.2f~P}`')
            else:
                failed.append((qstr, unit))

        if conversions:
            await channel.send('\n'.join(conversions))

        return failed
