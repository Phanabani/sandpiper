import logging

import discord.ext.commands as commands

from .database import Database

logger = logging.getLogger('sandpiper.user_database')


class UserData(commands.Cog):

    database: Database

    def __init__(self, bot: commands.Bot):
        # TODO how should the database adapter be passed?
        self.bot = bot
