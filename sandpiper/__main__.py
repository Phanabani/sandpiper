import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from . import Sandpiper, Config

LOGS_PATH = Path(__file__).parent / 'logs'
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')

# Sandpiper logging
logger = logging.getLogger('sandpiper')
logger.setLevel(logging.DEBUG)
handler = TimedRotatingFileHandler(LOGS_PATH / 'sandpiper.log',
                                   when='midnight', backupCount=7)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Discord logging
logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = TimedRotatingFileHandler(LOGS_PATH / 'sandpiper.log',
                                   when='midnight', backupCount=7)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Run bot
config_path = Path(__file__).parent / 'config.json'
bot_token, config = Config.load_json(config_path)
sandpiper = Sandpiper(config)
sandpiper.run(bot_token)
