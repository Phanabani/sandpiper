from functools import cached_property
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Literal

from phanas_pydantic_helpers import maybe_relative_path
from pydantic import BaseModel, conint

from sandpiper.common.paths import MODULE_PATH

_logging_levels = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Logging(BaseModel):
    class Config:
        allow_mutation = False
        validate_all = False
        keep_untouched = (cached_property,)

    sandpiper_logging_level: _logging_levels = "INFO"
    discord_logging_level: _logging_levels = "WARNING"
    output_file: Path = Path("./logs/sandpiper.log")
    when: Literal["S", "M", "H", "D", "midnight"] = "midnight"
    interval: conint(ge=1) = 1
    backup_count: conint(ge=0) = 7
    format: str = "%(asctime)s %(levelname)s %(name)s | %(message)s"

    _normalize_output_file = maybe_relative_path("output_file", MODULE_PATH)

    @cached_property
    def formatter(self):
        return logging.Formatter(self.format)

    @cached_property
    def handler(self):
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        handler = TimedRotatingFileHandler(
            filename=self.output_file,
            when=self.when,
            interval=self.interval,
            backupCount=self.backup_count,
        )
        handler.setFormatter(self.formatter)
        return handler
