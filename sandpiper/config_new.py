from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import *

from sandpiper.config_parser import (
    ConfigCompound, BoundedInt, OneOf, MaybeRelativePath, lazy_field
)


class SandpiperConfig(ConfigCompound):

    bot_token: str

    # TODO are these auto instantiated? should there be an annotation to
    #   explicitly mark as optional?
    bot: _Bot

    class _Bot(ConfigCompound):

        command_prefix = "!piper "
        description = (
            "A bot that makes it easier to communicate with friends around the "
            "world.\n"
            "Visit my GitHub page for more info about commands and features: "
            "https://github.com/Hawkpath/sandpiper#commands-and-features"
        )
        commands: _Commands

        class _Commands(ConfigCompound):

            allow_public_bio_setting = False

    logging: _Logging

    class _Logging(ConfigCompound):

        _logging_levels = OneOf['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

        sandpiper_logging_level: _logging_levels
        discord_logging_level: _logging_levels
        output_file: Path = './logs/sandpiper.log'
        when: OneOf['S', 'M', 'H', 'D', 'midnight'] = 'midnight'
        interval: BoundedInt[1, None] = 1
        backup_count: BoundedInt[0, None] = 7
        format = "%(asctime)s|%(levelname)s|%(name)s|%(message)s"

        @lazy_field
        def formatter(self):
            return logging.Formatter(self.format)

        @lazy_field
        def handler(self):
            handler = TimedRotatingFileHandler(
                filename=self.output_file,
                when=self.when,
                interval=self.interval,
                backupCount=self.backup_count,
            )
            handler.setFormatter(self.formatter)
            return handler
