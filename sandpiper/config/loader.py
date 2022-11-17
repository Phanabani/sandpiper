import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T_Model = TypeVar("T_Model", bound=BaseModel)


def load_json(config_path: Path, model: type[T_Model]) -> T_Model:
    with config_path.open() as f:
        config_obj = json.load(f)
    return model.parse_obj(config_obj)
