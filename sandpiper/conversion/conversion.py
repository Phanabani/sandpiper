from decimal import Decimal
import logging
from typing import NoReturn, TYPE_CHECKING

import discord
import regex

from sandpiper.common.IANA import get_country_flag_emoji_from_timezone
from sandpiper.common.component import Component
from sandpiper.common.embeds import *
from sandpiper.common.misc import RuntimeMessages
from sandpiper.common.time import time_format
from sandpiper.conversion.time_conversion import *
import sandpiper.conversion.unit_conversion as unit_conversion
from sandpiper.user_data import DatabaseUnavailable

if TYPE_CHECKING:
    from sandpiper import Sandpiper

logger = logging.getLogger("sandpiper.unit_conversion")

conversion_pattern = regex.compile(
    # Skip anything inside a code block
    r"(?<!\\)`+(?s:.*?)`+(*SKIP)(*FAIL)|"
    # Match a {conversion block}
    r"{ *"
    r"(?P<quantity>[^>]+?) *"
    r"(?:> *(?P<out_unit>\S.*?) *)?"
    r"}"
)


class Conversion(Component):
    def __init__(self, sandpiper: Sandpiper):
        super().__init__(sandpiper)
        self.sandpiper.add_listener("on_message", self.conversions)

    async def conversions(self, msg: discord.Message):
        """
        Scan a message for conversion strings.

        :param msg: Discord message to scan for conversions
        """
        if msg.author == self.sandpiper.user:
            return

        conversion_strs = conversion_pattern.findall(msg.content)
        if not conversion_strs:
            return

        conversion_strs = await self.convert_time(msg, conversion_strs)
        await self.convert_measurements(msg.channel, conversion_strs)

    async def convert_time(
        self, msg: discord.Message, time_strs: list[tuple[str, str]]
    ) -> list[tuple[str, str]]:
        """
        Convert a list of time strings (like "5:45 PM") to different users'
        timezones and reply with the conversions.

        :param msg: Discord message that triggered the conversion
        :param time_strs: a list of strings that may be valid times
        :returns: a list of strings that could not be converted
        """

        user_data = self.sandpiper.components.user_data
        if user_data is None:
            # User data component couldn't be retrieved, so consider all conversions
            # failed
            return time_strs

        try:
            db = await user_data.get_database()
        except DatabaseUnavailable:
            return time_strs

        runtime_msgs = RuntimeMessages()
        converted_times, failed = await convert_time_to_user_timezones(
            db, msg.author.id, msg.guild, time_strs, runtime_msgs=runtime_msgs
        )

        if runtime_msgs.exceptions:
            # Send embed with any errors that happened during conversion
            await ErrorEmbed([str(e) for e in runtime_msgs.exceptions], join="\n").send(
                msg.channel
            )
            return failed

        if converted_times:
            # Send successful conversions
            output = []
            for timezone_in, conversions in converted_times:
                # There may be multiple input timezones
                # We will group them under a header of that timezone name
                if timezone_in is not None:
                    # But if no input timezone was specified, don't print any
                    # header
                    output.append(f"Using timezone **{timezone_in}**")

                for timezone_out, times in conversions:
                    # Print the converted times for each timezone on a new line
                    times = "  |  ".join(
                        f"`{time.strftime(time_format)}`" for time in times
                    )
                    flag = get_country_flag_emoji_from_timezone(timezone_out)
                    output.append(f"{flag}  **{timezone_out}**  -  {times}")

                output.append("")

            await msg.channel.send("\n".join(output[:-1]))

        return failed

    async def convert_measurements(
        self, channel: discord.TextChannel, quantity_strs: list[tuple[str, str]]
    ) -> NoReturn:
        """
        Convert a list of quantity strings (like "5 km") between imperial and
        metric and reply with the conversions.

        :param channel: Discord channel to send conversions message to
        :param quantity_strs: a list of strings that may be valid quantities
        :returns: a list of strings that could not be converted
        """

        conversions = []
        failed: list[tuple[str, str]] = []
        runtime_msgs = RuntimeMessages()
        for qstr, unit in quantity_strs:
            q = unit_conversion.convert_measurement(
                qstr, unit, runtime_msgs=runtime_msgs
            )
            if isinstance(q, tuple):
                # We parsed as a quantity and got a conversion
                conversions.append(f"`{q[0]:.2f~P}` = `{q[1]:.2f~P}`")
            elif isinstance(q, Decimal):
                # We parsed as dimensionless and got a numeric type back
                conversions.append(f"`{qstr}` = `{q}`")
            else:
                failed.append((qstr, unit))

        if runtime_msgs.exceptions:
            # Send embed with any errors that happened during conversion
            await ErrorEmbed([str(e) for e in runtime_msgs.exceptions], join="\n").send(
                channel
            )

        if conversions:
            await channel.send("\n".join(conversions))
