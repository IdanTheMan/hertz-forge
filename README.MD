

# Hertz Forge

Brainwave Entrainment Sound Generator with binaural beats, amplitude modulation,
bilateral panning and frequency modulation.

[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
![Python](https://img.shields.io/badge/python-3.9+-brightgreen)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

## One-Line Install

Copy and paste into Windows Run:

```
powershell -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/IdanTheMan/hertz-forge/main/install.ps1 | iex"

or

powershell -WindowStyle Hidden -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/IdanTheMan/hertz-forge/main/install.ps1 | iex"
```

This will:
- Download Hertz Forge to `%APPDATA%\HertzForge`
- Install Python 3 if missing (via winget)
- Install dependencies (`numpy`, `sounddevice`)
- Create a desktop shortcut
- Launch the app

## Manual Install

```bash
git clone https://github.com/IdanTheMan/hertz-forge.git
cd hertz-forge
pip install -r requirements.txt
python run.py
```

## Features

| Feature | Description |
|---|---|
| **Carrier Frequency** | 40–1000 Hz with sine, triangle, sawtooth, or square wave |
| **Brainwave Frequency** | 0–100 Hz δ θ α β γ |
| **Amplitude Modulation** | Pulse depth from flat to full on/off |
| **Bilateral Panning** | Crossfade at envelope trough for spatial effects |
| **Binaural Beats** | Pure sine tones L/R, amplitude-modulated with carrier envelope |
| **Frequency Modulation** | Sweep range around carrier frequency |
| **WAV Export** | Custom duration (HH:MM:SS), saves stereo WAV |
| **Live Updates** | All parameter changes apply instantly to audio |

## Requirements

- Windows 10 / 11
- Python 3.9+
- Audio output device

Dependencies are listed in `requirements.txt` and installed automatically.

## Project Structure

```
hertz-forge/
├── README.md
├── requirements.txt
├── install.ps1
├── run.py
├── run_playlist.py
├── hertz_forge/
│   ├── __init__.py
│   ├── constants.py
│   ├── audio.py
│   ├── widgets.py
│   ├── gui.py
│   └── main.py
└── playlist_forge/
    ├── __init__.py
    ├── config.py              ← NEW — save/load/naming
    ├── engine.py
    ├── main.py
    ├── gui/                   ← was gui.py, now a package
    │   ├── __init__.py        ← exports App (drop-in replacement)
    │   ├── app.py             ← App class + __init__, run, _quit
    │   ├── style.py           ← StyleMixin
    │   ├── helpers.py         ← HelperMixin (labels, scroll, dividers)
    │   ├── build.py           ← BuildMixin (_build layout)
    │   ├── playlist_ui.py     ← PlaylistMixin (containers, rows, collapse)
    │   ├── row_ui.py          ← RowMixin (slot creation, body, advanced)
    │   ├── interactions.py    ← InteractionMixin (drag-drop, config save/load)
    │   └── transport.py       ← TransportMixin (play, stop, transitions, tick, save WAV)
```

## Usage

### Running

```bash
# Direct
python run.py
python run_playlist.py

# As module
python -m hertz_forge.main
python -m playlist_forge.main
```


### Exporting WAV

1. Set the export duration using the HH:MM:SS spinners (or click a preset)
2. Click **Export…**
3. Choose a save location
4. Wait for the status bar to confirm




