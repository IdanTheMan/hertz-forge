import os
import sys

# ensure project root is on sys.path for hertz_forge imports
_root = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
if _root not in sys.path:
    sys.path.insert(0, _root)

from .app import App

__all__ = ["App"]