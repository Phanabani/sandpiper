import sys
if sys.platform == 'win32':
    # Temporary fix for expired certificates on Windows
    import certifi
    import os
    os.environ['SSL_CERT_FILE'] = certifi.where()

from .config import Config
from .sandpiper import Sandpiper
