import logging
from pathlib import Path

from . import Sandpiper, Config

# Load config
config_path = Path(__file__).parent / 'config.json'
bot_token, config = Config.load_json(config_path)

# Sandpiper logging
logger = logging.getLogger('sandpiper')
logger.setLevel(logging.DEBUG)
logger.addHandler(config.logging.handler)

# Discord logging
logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
logger.addHandler(config.logging.handler)

# Run bot
sandpiper = Sandpiper(config.bot)
sandpiper.run(bot_token)
