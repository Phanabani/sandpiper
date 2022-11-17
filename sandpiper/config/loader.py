__all__ = ["load_config"]

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel
import yaml

T_Model = TypeVar("T_Model", bound=BaseModel)


def parse_json(config_path: Path) -> dict[str, Any]:
    with config_path.open() as f:
        return json.load(f)


def parse_yml(config_path: Path) -> dict[str, Any]:
    with config_path.open() as f:
        return yaml.load(f, yaml.Loader)


def load_config(config_path: Path, model: type[T_Model]) -> T_Model:
    match config_path.suffix:
        case ".json":
            config_obj = parse_json(config_path)
        case ".yaml" | ".yml":
            config_obj = parse_yml(config_path)
        case _:
            raise ValueError("Config must be a JSON or YAML file")

    return model.parse_obj(config_obj)
