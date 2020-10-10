from typing import Iterable, Tuple

import discord

FieldType = Tuple[str, str, bool]


class Embeds:

    INFO_COLOR = 0x5E5FFF
    SUCCESS_COLOR = 0x57FCA5
    ERROR_COLOR = 0xFF0000

    @classmethod
    async def info(cls, messageable: discord.abc.Messageable,
                   message: str = None, fields: Iterable[FieldType] = None):
        """
        Sends an info embed. At least one of ``message`` or ``fields`` must be
        supplied.

        :param messageable: A messageable interface to send the embed to
        :param message: An info message
        :param fields: An iterable of fields to add to the embed where each
            field is a tuple of shape (name, value, inline)
        """
        embed = discord.Embed(title='Info',
                              description=message or discord.Embed.Empty,
                              color=cls.INFO_COLOR)
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
        await messageable.send(embed=embed)

    @classmethod
    async def success(cls, messageable: discord.abc.Messageable, message: str):
        """
        Sends a success embed.

        :param messageable: A messageable interface to send the embed to
        :param message: The success message
        """
        embed = discord.Embed(
            title='Success', description=message, color=cls.SUCCESS_COLOR)
        await messageable.send(embed=embed)

    @classmethod
    async def error(cls, messageable: discord.abc.Messageable, message: str):
        """
        Sends an error embed.

        :param messageable: A messageable interface to send the embed to
        :param message: The error message
        """
        embed = discord.Embed(
            title='Error', description=message, color=cls.ERROR_COLOR)
        await messageable.send(embed=embed)
