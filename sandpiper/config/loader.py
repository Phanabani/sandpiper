__all__ = ["load_config"]

import json
import logging
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel
import yaml

from sandpiper.common.misc import stringify_list
from sandpiper.config.constants import CONFIG_DIR, LEGACY_CONFIG_DIR
from sandpiper.config.models import SandpiperConfig

T_Model = TypeVar("T_Model", bound=BaseModel)

logger = logging.getLogger(__name__)


def parse_json(config_path: Path) -> dict[str, Any]:
    with config_path.open() as f:
        return json.load(f)


def parse_yml(config_path: Path) -> dict[str, Any]:
    with config_path.open() as f:
        return yaml.load(f, yaml.Loader)


def try_find_config(config_dir: Path) -> Path | None:
    suffixes = ("json", "yaml", "yml")

    logger.debug(
        f"Searching for config files in path {config_dir} with suffixes {suffixes}"
    )
    config_files = [
        file
        for suffix in suffixes
        if (file := config_dir / f"config.{suffix}").exists()
    ]
    if len(config_files) == 1:
        logger.debug(f"Found config file at {config_files[0]}")
        return config_files[0]
    if len(config_files) > 1:
        raise RuntimeError(
            f"Multiple config files were found. Please use only one. Files: "
            f"{stringify_list(config_files)}"
        )
    return None


def try_get_legacy_config_file(current_config_dir) -> Path | None:
    # If a YML config exists in the legacy config location, raise an error
    for suffix in ("yml", "yaml"):
        if (LEGACY_CONFIG_DIR / f"config.{suffix}").exists():
            raise RuntimeError(
                f"YML config files must be placed in {current_config_dir}. Note that "
                f"JSON files in the legacy location ({LEGACY_CONFIG_DIR}) are "
                f"loadable for backward compatibility only."
            )

    # JSON config in the legacy location is allowed for backward compatibility
    logger.debug(f"Searching for config file in legacy location {LEGACY_CONFIG_DIR}")
    if (config_file := LEGACY_CONFIG_DIR / "config.json").exists():
        return config_file

    return None


def load_config(config_dir: Path | None = None) -> T_Model:
    config_dir = config_dir or CONFIG_DIR

    config_file = try_find_config(config_dir)
    legacy_config_file = try_get_legacy_config_file(config_dir)

    if legacy_config_file and config_file:
        raise RuntimeError(
            f"Two config files were found. Please only use one. Files: "
            f"[{legacy_config_file}, {config_file}]"
        )
    if not (legacy_config_file or config_file):
        raise RuntimeError(
            f"No config file could be found in {config_dir} or {legacy_config_file}"
        )
    if config_file is None:
        # By now, we know at least one has matched
        config_file = legacy_config_file
    logger.debug(f"Using config file {config_file}")

    match config_file.suffix:
        case ".json":
            config_obj = parse_json(config_file)
        case ".yaml" | ".yml":
            config_obj = parse_yml(config_file)
        case _:
            # Shouldn't happen
            raise ValueError("Config must be a JSON or YAML file")

    return SandpiperConfig.parse_obj(config_obj)
