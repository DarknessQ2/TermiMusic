# 🎵 TermiMusic

A highly customizable, physics-driven terminal music player for Linux. Built for ricing environments (like custom Wayland window managers).

<p align="center">
  <img src="asset3.gifs/a" alt="TermiMusic Screenshot" width="800">
</p>

## Features
* **Physics-based Disk Animation**: The ASCII disk rotation speed reacts to the bass frequencies of the song in real-time.
* **Audio Visualizer**: Integrated CAVA visualizer with dynamic color changing.
* **High-Res Terminal Art**: Fetches YouTube thumbnails and renders them into the terminal using TrueColor ANSI blocks.
* **System Stats Module**: Real-time CPU, RAM, and Temperature monitoring.
* **Discord Rich Presence**: Let your friends know what you're listening to.
* **Audio FX**: Built-in bass boost and lo-fi filters.
* **Playlist Manager**: Save and load custom queues dynamically.

## Prerequisites
Ensure you have the following system dependencies installed (Arch Linux example):

```bash
sudo pacman -S --needed base-devel mpv cava socat python
```

> ⚠️ **Important:** The `base-devel` package (or your distro's equivalent, like `build-essential` on Ubuntu) is **mandatory**. Without it, the installation will fail with a `RuntimeError: No se encontró el compilador: 'g++'`.

## Installation

1. **Clone the repository:**
```bash
   git clone [https://github.com/DarknessQ2/TermiMusic](https://github.com/DarknessQ2/TermiMusic)
   cd TermiMusic
   ```

2. **Set up the environment and install dependencies:**
```bash
   # Create and activate a virtual environment
   python -m venv venv
   source venv/bin/activate

   # Install project dependencies
   pip install -r requirements.txt
   ```

3. **Install the package locally:**
```bash
   python3 setup.py install --user
   ```

## Usage
Simply run the command from your terminal:

```bash
termimusic
```

## Controls & Commands

### Keybindings
* **`Space`** : Play / Pause
* **`p` / `o`** : Next / Previous Track
* **`+` / `-`** : Volume Up / Down
* **`/`** : Enter Command Mode

### Command Mode
After pressing `/`, you can execute the following actions:
* **Load URL/File** : Just paste the link/path and press `Enter`.
* **`/color <0-255>`** : Change the visualizer color dynamically.
