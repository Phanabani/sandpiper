import certifi
import os
os.environ['SSL_CERT_FILE'] = certifi.where()

from .unit_conversion import *
