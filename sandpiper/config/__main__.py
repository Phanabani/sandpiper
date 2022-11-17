import json
from pathlib import Path

from sandpiper.config import SandpiperConfig


def serialize_path(p: Path):
    return str(p)


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Path):
            return serialize_path(obj)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


if __name__ == "__main__":
    config = SandpiperConfig(bot_token="YOUR_BOT_TOKEN")
    print(json.dumps(config.dict(), cls=CustomEncoder, indent=2))
