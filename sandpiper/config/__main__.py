from pathlib import Path
from string import punctuation

from phanas_pydantic_helpers import create_template_from_model
import yaml

from sandpiper.config import SandpiperConfig

YAML_STR_SCALAR_TAG = "tag:yaml.org,2002:str"

dumper = yaml.SafeDumper
punctuation = set(punctuation)


def serialize_str(dumper: yaml.BaseDumper, s: str):
    if len(s) > dumper.best_width:
        # Wrap long strings
        style = ">"
    elif s[0] in punctuation or ("'" in s and '"' in s):
        # String starts with punctuation or has both types of quotes; surround
        # with double quotes
        style = '"'
    else:
        # Use default style
        style = ""
    return dumper.represent_scalar(YAML_STR_SCALAR_TAG, s, style=style)


def serialize_path(dumper: yaml.BaseDumper, p: Path):
    return dumper.represent_scalar(YAML_STR_SCALAR_TAG, str(p))


dumper.add_representer(str, serialize_str)
dumper.add_multi_representer(Path, serialize_path)


if __name__ == "__main__":
    config_template = create_template_from_model(SandpiperConfig)
    print(yaml.dump(config_template, Dumper=dumper, indent=2, sort_keys=False))
