from __future__ import annotations
import json
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Tuple, Union

DEFAULTS = {
  "bot": {
    "command_prefix": "!piper ",
    "description": "A bot that makes it easier to communicate with friends around the world."
  },

  "logging": {
    "output_file": "./logs/sandpiper.log",
    "when": "midnight",
    "interval": 1,
    "backup_count": 7,
    "format": "%(asctime)s:%(levelname)s:%(name)s: %(message)s"
  }
}


class ConfigError(Exception):
    pass


def get_default(config: Dict[str, Any], category: str, key: str):
    try:
        return config[category][key]
    except KeyError:
        return DEFAULTS[category][key]


class Config:

    __slots__ = ['bot', 'logging']

    class _Bot:

        __slots__ = ['command_prefix', 'description']

        command_prefix: str
        description: str

        def __init__(self, config: Dict[str, Any]):
            """Parse bot-specific config"""

            self.command_prefix = get_default(config, 'bot', 'command_prefix')
            if not isinstance(self.command_prefix, str):
                raise ConfigError('bot.command_prefix must be a string')

            self.description = get_default(config, 'bot', 'description')
            if not isinstance(self.description, str):
                raise ConfigError('bot.description must be a string')

    class _Logging:

        __slots__ = ['output_path', 'when', 'interval', 'backup_count',
                     'format', 'formatter', 'handler']

        output_path: Path
        when: str
        interval: int
        backup_count: int
        format: str
        formatter: logging.Formatter
        handler: TimedRotatingFileHandler

        _allowed_whens = ('S', 'M', 'H', 'D', 'midnight')

        def __init__(self, config: Dict[str, Any]):
            """Parse logging-specific config"""

            output_file = get_default(config, 'logging', 'output_file')
            if not isinstance(output_file, str):
                raise ConfigError('logging.output_file must be a string')
            output_file = Path(output_file)
            if not output_file.is_absolute():
                output_file = Path(__file__).parent / output_file
            if not output_file.parent.exists():
                raise ConfigError(f"logging.output_file's parent directory "
                                  f"does not exist ({output_file.parent})")
            self.output_path = output_file

            self.when = get_default(config, 'logging', 'when')
            if self.when not in self._allowed_whens:
                raise ConfigError(f"logging.when must be one of "
                                  f"{self._allowed_whens!r}")

            self.interval = get_default(config, 'logging', 'interval')
            if not isinstance(self.interval, int) or self.interval < 1:
                raise ConfigError('logging.interval must be an integer greater '
                                  'than 0')

            self.backup_count = get_default(config, 'logging', 'backup_count')
            if not isinstance(self.backup_count, int) or self.backup_count < 0:
                raise ConfigError('logging.backup_count must be an integer '
                                  'greater than or equal to 0')

            self.format = get_default(config, 'logging', 'format')
            if not isinstance(self.format, str):
                raise ConfigError('logging.format must be a string')

            self.formatter = logging.Formatter(self.format)
            self.handler = TimedRotatingFileHandler(
                filename=self.output_path,
                when=self.when,
                interval=self.interval,
                backupCount=self.backup_count,
            )
            self.handler.setFormatter(self.formatter)

    def __init__(self, config: Dict[str, Any]):
        """Parse config"""
        self.bot = self._Bot(config)
        self.logging = self._Logging(config)

    @classmethod
    def load_json(cls, config_path: Union[Path, str]) -> Tuple[str, Config]:
        """
        Load bot config from a json file.

        :param config_path: Path to the json file
        :returns: A tuple of (bot_token, config). For security reasons, the
            bot token isn't loaded into the config object.
        """

        with open(config_path) as f:
            config_json: Dict[str, Any] = json.load(f)

        if 'bot_token' not in config_json:
            raise ConfigError('bot_token missing')
        bot_token = config_json['bot_token']
        # Delete bot_token from dict just in case
        del config_json['bot_token']

        config = Config(config_json)
        return bot_token, config
