from pathlib import Path
import sys

DEFAULT_LOGS_PATH = Path(sys.modules['sandpiper'].__file__).parent / 'logs'
