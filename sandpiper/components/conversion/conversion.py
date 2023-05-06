from __future__ import annotations

from decimal import Decimal
import logging
from typing import NoReturn, TYPE_CHECKING

import discord
import regex

from sandpiper.common.component import Component
from sandpiper.common.countries import get_country_flag_emoji_from_timezone
from sandpiper.common.embeds import *
from sandpiper.common.misc import RuntimeMessages
from sandpiper.common.time import time_format
from sandpiper.components.conversion.raw_quantity import RawQuantity
from sandpiper.components.conversion.time_conversion import (
    convert_time_to_user_timezones,
)
import sandpiper.components.conversion.unit_conversion as unit_conversion
from sandpiper.components.user_data import DatabaseUnavailable

if TYPE_CHECKING:
    from sandpiper import Sandpiper

logger = logging.getLogger(__name__)

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

        matches = conversion_pattern.findall(msg.content)
        if not matches:
            return

        raw_quantities = [RawQuantity(*m) for m in matches]
        raw_quantities = await self.convert_time(msg, raw_quantities)
        await self.convert_measurements(msg.channel, raw_quantities)

    async def convert_time(
        self, msg: discord.Message, raw_quantities: list[RawQuantity]
    ) -> list[RawQuantity]:
        """
        Convert a list of time strings (like "5:45 PM") to different users'
        timezones and reply with the conversions.

        :param msg: Discord message that triggered the conversion
        :param raw_quantities: a list of `RawQuantity`s that may be valid times
        :returns: a list of `RawQuantity`s that could not be converted
        """

        user_data = self.sandpiper.components.user_data
        if user_data is None:
            # User data component couldn't be retrieved, so consider all
            # conversions failed
            return raw_quantities

        try:
            db = await user_data.get_database()
        except DatabaseUnavailable:
            return raw_quantities

        runtime_msgs = RuntimeMessages()
        conversion_output = await convert_time_to_user_timezones(
            db, msg.author.id, msg.guild, raw_quantities, runtime_msgs=runtime_msgs
        )

        if runtime_msgs.exceptions:
            # Send embed with any errors that happened during conversion
            await ErrorEmbed([str(e) for e in runtime_msgs.exceptions], join="\n").send(
                msg.channel
            )
            return conversion_output.failed

        # Send successful conversions
        output = []
        input_timezones_seen = set()
        for conversion in conversion_output.conversions:
            # There may be multiple input timezones
            # We will group them under a header of that timezone name
            if (
                conversion.is_explicit_input_timezone
                and conversion.input_timezone not in input_timezones_seen
            ):
                if len(input_timezones_seen) > 0:
                    output.append("")
                output.append(f"Using timezone **{conversion.input_timezone.zone}**")
                input_timezones_seen.add(conversion.input_timezone)

            # Print the converted times for each timezone on a new line
            times = "  |  ".join(
                f"`{t.strftime(time_format)}`" for t in conversion.datetimes
            )
            flag = get_country_flag_emoji_from_timezone(conversion.timezone)
            output.append(f"{flag}  **{conversion.timezone.zone}**  -  {times}")

        if output:
            await msg.channel.send("\n".join(output[:-1]))

        return conversion_output.failed

    async def convert_measurements(
        self, channel: discord.TextChannel, raw_quantities: list[RawQuantity]
    ) -> NoReturn:
        """
        Convert a list of quantity strings (like "5 km") between imperial and
        metric and reply with the conversions.

        :param channel: Discord channel to send conversions message to
        :param raw_quantities: a list of `RawQuantity`s that may be valid
            quantities
        :returns: a list of strings that could not be converted
        """

        conversions = []
        failed: list[RawQuantity] = []
        runtime_msgs = RuntimeMessages()
        for raw_quantity in raw_quantities:
            q = unit_conversion.convert_measurement(
                raw_quantity.quantity, raw_quantity.suffix, runtime_msgs=runtime_msgs
            )
            if isinstance(q, tuple):
                # We parsed as a quantity and got a conversion
                conversions.append(f"`{q[0]:.2f~P}` = `{q[1]:.2f~P}`")
            elif isinstance(q, Decimal):
                # We parsed as dimensionless and got a numeric type back
                conversions.append(f"`{raw_quantity.quantity}` = `{q}`")
            else:
                failed.append(RawQuantity(raw_quantity.quantity, raw_quantity.suffix))

        if runtime_msgs.exceptions:
            # Send embed with any errors that happened during conversion
            await ErrorEmbed([str(e) for e in runtime_msgs.exceptions], join="\n").send(
                channel
            )

        if conversions:
            await channel.send("\n".join(conversions))
