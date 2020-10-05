import logging

import discord.ext.commands as commands

logger = logging.getLogger('sandpiper.bios')


class Bios(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

