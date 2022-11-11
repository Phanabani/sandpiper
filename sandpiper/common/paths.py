from pathlib import Path
import sys

MODULE_PATH = Path(sys.modules["sandpiper"].__file__).parent.absolute()
