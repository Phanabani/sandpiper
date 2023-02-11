__all__ = [
    "SimpleEmbed",
    "SuccessEmbed",
    "WarningEmbed",
    "ErrorEmbed",
    "InfoEmbed",
    "SpecialEmbed",
]

from typing import Optional, Union, cast

import discord
from discord import Interaction, InteractionResponse

T_Field = tuple[str, str, bool]


class SimpleEmbed:

    title = ""
    color = 0x000000

    def __init__(
        self,
        msg: Union[None, str, list[str]] = None,
        fields: list[T_Field] = None,
        *,
        title: Optional[str] = None,
        color: Optional[int] = None,
        join: str = "\n",
    ):
        """
        :param msg: the message to add to the embed. May be a list of str
            which will be joined upon sending.
        :param fields: an iterable of fields to add to the embed where each
            field is a tuple of shape (name, value, inline)
        :param title: the title of the embed. If None, it will use the class's
            default title.
        :param join: the string to join multiple messages with
        """
        if msg is None:
            msg = []
        elif isinstance(msg, str):
            msg = [msg]
        elif not isinstance(msg, list):
            raise TypeError("message must be None or of type (str, list[str])")
        self.message_parts: list[str] = msg

        if fields is None:
            fields = []
        elif not isinstance(fields, list):
            raise TypeError("fields must be None or of type list")
        self.fields: list[T_Field] = fields

        if title is not None:
            self.title = title

        if color is not None:
            self.color = color

        self.join_str = join

    def append(self, msg: str):
        """
        Add another string to the embed's message.
        """
        if not isinstance(msg, str):
            raise TypeError("msg must be of type str")
        self.message_parts.append(msg)

    async def send(self, messageable: discord.abc.Messageable | Interaction):
        """
        Send the embed to `messageable`.

        :param messageable: a messageable interface to send the embed to
        """
        desc = None
        if self.message_parts:
            desc = self.join_str.join(self.message_parts)

        embed = discord.Embed(title=self.title, description=desc, color=self.color)

        if self.fields:
            for name, value, inline in self.fields:
                embed.add_field(name=name, value=value, inline=inline)

        if isinstance(messageable, Interaction):
            response = cast(InteractionResponse, messageable.response)
            await response.send_message(embed=embed)
        else:
            await messageable.send(embed=embed)


class SuccessEmbed(SimpleEmbed):
    color = 0x57FCA5
    title = "Success"


class WarningEmbed(SimpleEmbed):
    color = 0xE7D900
    title = "Warning"


class ErrorEmbed(SimpleEmbed):
    color = 0xFF0000
    title = "Error"


class InfoEmbed(SimpleEmbed):
    color = 0x5E5FFF
    title = "Info"


class SpecialEmbed(SimpleEmbed):
    color = 0xF656F1
    title = "Announcement"
