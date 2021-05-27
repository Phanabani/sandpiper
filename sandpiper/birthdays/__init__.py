from .cog import Birthdays
from sandpiper import Sandpiper


def setup(bot: Sandpiper):
    birthdays = Birthdays(bot)
    bot.add_cog(birthdays)
