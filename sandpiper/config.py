from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Tuple, Union

DEFAULT_COMMAND_PREFIX = '!piper '
DEFAULT_DESCRIPTION = 'A bot that makes it easier to communicate with friends around the world.'


class Config:

    __slots__ = ['command_prefix', 'description']

    def __init__(self, command_prefix: str, description: str):
        self.command_prefix = command_prefix
        self.description = description

    @classmethod
    def load_json(cls, config_path: Union[Path, str]) -> Tuple[str, Config]:
        """
        Load bot config info from a json file.

        :param config_path: Path to the json file
        :returns: A tuple of (bot_token, config). For security reasons, the
            bot token isn't loaded into the config object.
        """
        with open(config_path) as f:
            config_json: Dict[str, Any] = json.load(f)
        bot_token = config_json['bot_token']
        config = Config(
            command_prefix=config_json.get('command_prefix', DEFAULT_COMMAND_PREFIX),
            description=config_json.get('description', DEFAULT_DESCRIPTION)
        )
        return bot_token, config
