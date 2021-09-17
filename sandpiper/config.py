from __future__ import annotations
from functools import cached_property
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Annotated, Literal

from sandpiper.common.paths import MODULE_PATH
from sandpiper.piperfig import *

__all__ = ('SandpiperConfig',)


class SandpiperConfig(ConfigSchema):

    bot_token: str
    bot: _Bot
    logging: _Logging

    class _Bot(ConfigSchema):

        command_prefix = "!piper "
        description = (
            "A bot that makes it easier to communicate with friends around the "
            "world.\n"
            "Visit my GitHub page for more info about commands and features: "
            "https://github.com/phanabani/sandpiper#commands-and-features"
        )
        modules: _Modules

        class _Modules(ConfigSchema):

            bios: _Bios
            birthdays: _Birthdays

            class _Bios(ConfigSchema):

                allow_public_setting = False

            class _Birthdays(ConfigSchema):

                message_templates_no_age: list[str] = [
                    "Hey!! It's {name}'s birthday! Happy birthday {ping}!",

                    "{name}! It's your birthday!! Hope it's a great one "
                    "{ping}!",

                    "omg! did yall know it's {name}'s birthday?? happy "
                    "birthday {ping}! :D",

                    "I am pleased to announce... IT'S {NAME}'s BIRTHDAY!! "
                    "Happy birthday {ping}!!"
                ]
                message_templates_with_age: list[str] = [
                    "Hey!! It's {name}'s birthday! {They} turned {age} today. "
                    "Happy birthday {ping}!",

                    "{name}! It's your birthday!! I can't believe you're "
                    "already {age} ;u; Hope it's a great one "
                    "{ping}!",

                    "omg! did yall know it's {name}'s birthday?? {Theyre} "
                    "{age} now! happy birthday {ping}! :D",

                    "I am pleased to announce... IT'S {NAME}'s BIRTHDAY!! "
                    "{They} just turned {age}! Happy birthday {ping}!!"
                ]

    class _Logging(ConfigSchema):

        _logging_levels = Literal[
            'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
        ]

        sandpiper_logging_level: _logging_levels = 'INFO'
        discord_logging_level: _logging_levels = 'WARNING'
        output_file: Annotated[Path, MaybeRelativePath(MODULE_PATH)] = (
            './logs/sandpiper.log'
        )
        when: Literal['S', 'M', 'H', 'D', 'midnight'] = 'midnight'
        interval: Annotated[int, Bounded(1, None)] = 1
        backup_count: Annotated[int, Bounded(0, None)] = 7
        format = "%(asctime)s %(levelname)s %(name)s | %(message)s"

        @cached_property
        def formatter(self):
            return logging.Formatter(self.format)

        @cached_property
        def handler(self):
            handler = TimedRotatingFileHandler(
                filename=self.output_file,
                when=self.when,
                interval=self.interval,
                backupCount=self.backup_count,
            )
            handler.setFormatter(self.formatter)
            return handler


if __name__ == '__main__':
    config = SandpiperConfig({'bot_token': '<BOT_TOKEN>'})
    print(config.serialize())
