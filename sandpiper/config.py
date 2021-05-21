from __future__ import annotations
from functools import cached_property
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Annotated as A, Literal

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
            "https://github.com/Hawkpath/sandpiper#commands-and-features"
        )
        commands: _Commands

        class _Commands(ConfigSchema):

            allow_public_bio_setting = False

    class _Logging(ConfigSchema):

        _logging_levels = Literal[
            'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
        ]

        sandpiper_logging_level: _logging_levels = 'INFO'
        discord_logging_level: _logging_levels = 'WARNING'
        output_file: A[Path, MaybeRelativePath(MODULE_PATH)] = (
            './logs/sandpiper.log'
        )
        when: Literal['S', 'M', 'H', 'D', 'midnight'] = 'midnight'
        interval: A[int, Bounded(1, None)] = 1
        backup_count: A[int, Bounded(0, None)] = 7
        format = "%(asctime)s|%(levelname)s|%(name)s|%(message)s"

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
