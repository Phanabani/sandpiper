from .cog import Birthdays
from sandpiper import Sandpiper


def setup(bot: Sandpiper):
    config = bot.modules_config.birthdays
    birthdays = Birthdays(
        bot, message_templates_no_age=config.message_templates_no_age,
        message_templates_with_age=config.message_templates_with_age
    )
    bot.add_cog(birthdays)
