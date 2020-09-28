import json
import logging
from pathlib import Path
import sys

from . import Sandpiper

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

with open(Path(__file__).parent / 'config.json') as f:
    config = json.load(f)

sandpiper = Sandpiper()
sandpiper.run(config['bot_token'])
