#!/usr/bin/env python3
"""
Hertz Forge — Playlist Mode

Run as module:
    python -m playlist_forge.main
"""

import subprocess, sys, importlib, os


def _bootstrap():
    req = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "requirements.txt")
    try:
        import numpy; import sounddevice
    except ImportError:
        print("[playlist_forge] Installing dependencies…")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install",
             "--quiet", "--user", "-r", req])
        print("[playlist_forge] Done.\n")


_bootstrap()

from .gui import App

if __name__ == "__main__":
    App().run()