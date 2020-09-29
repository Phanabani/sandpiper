import logging
from pathlib import Path
import sys

from . import Sandpiper, Config

logger = logging.getLogger('sandpiper')

logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

config_path = Path(__file__).parent / 'config.json'
bot_token, config = Config.load_json(config_path)

sandpiper = Sandpiper(config)
sandpiper.run(bot_token)
