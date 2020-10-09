import discord


class Embeds:

    INFO_COLOR = 0x5E5FFF
    SUCCESS_COLOR = 0x57FCA5
    ERROR_COLOR = 0xFF0000

    @classmethod
    async def info(cls, messageable: discord.abc.Messageable, message: str):
        embed = discord.Embed(
            title='Info', description=message, color=cls.INFO_COLOR)
        await messageable.send(embed=embed)

    @classmethod
    async def success(cls, messageable: discord.abc.Messageable, message: str):
        embed = discord.Embed(
            title='Success', description=message, color=cls.SUCCESS_COLOR)
        await messageable.send(embed=embed)

    @classmethod
    async def error(cls, messageable: discord.abc.Messageable, reason: str):
        embed = discord.Embed(
            title='Error', description=reason, color=cls.ERROR_COLOR)
        await messageable.send(embed=embed)
