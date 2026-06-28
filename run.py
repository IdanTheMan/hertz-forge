#!/usr/bin/env python3
import os
import sys
import subprocess


def _bootstrap():
    req = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "requirements.txt")
    try:
        import numpy; import sounddevice
    except ImportError:
        print("[hertz_forge] Installing dependencies…")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install",
             "--user", "-r", req])
        print("[hertz_forge] Done.\n")


_bootstrap()

from hertz_forge.gui import App

if __name__ == "__main__":
    App().run()