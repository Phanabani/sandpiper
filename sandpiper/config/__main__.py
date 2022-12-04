from pathlib import Path

import yaml

from sandpiper.config import SandpiperConfig

YAML_STR_SCALAR_TAG = "tag:yaml.org,2002:str"

dumper = yaml.SafeDumper


def serialize_path(dumper: yaml.BaseDumper, p: Path):
    return dumper.represent_scalar(YAML_STR_SCALAR_TAG, str(p))


dumper.add_multi_representer(Path, serialize_path)


if __name__ == "__main__":
    config = SandpiperConfig(bot_token="YOUR_BOT_TOKEN")
    print(yaml.dump(config.dict(), Dumper=dumper, indent=2, sort_keys=False))
