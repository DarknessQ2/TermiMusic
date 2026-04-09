# 🎵 TermiMusic

A highly customizable, physics-driven terminal music player for Linux. Built for ricing environments (like custom Wayland window managers).

![TermiMusic Screenshot](/assets/aset1.png)

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
\`\`\`bash
sudo pacman -S mpv cava socat python
\`\`\`

## Installation

1. Clone the repository:
\`\`\`bash
git clone https://github.com/DarknessQ2/TermiMusic
cd TermiMusic
\`\`\`

2. Install via Python (Using PIP or PIPX):
\`\`\`bash
# If your environment is externally managed, use pipx:
pipx install .

# Or using standard pip (in a venv or with break-system-packages if preferred)
pip install .
\`\`\`

## Usage
Simply run the command from anywhere in your terminal:
\`\`\`bash
termimusic
\`\`\`

### Controls & Commands
* `Space`: Play/Pause
* `p` / `o`: Next / Previous Track
* `+` / `-`: Volume Up / Down
* `/`: Enter Command Mode

**In Command Mode:**
* Load URL/File: Just paste the link and press Enter.
* `/color <0-255>`: Change visualizer color.
* `/fx <bass|lofi|clear>`: Apply audio filters.
* `/loop <song|list|off>`: Toggle loop mode.
* `/save <name>`: Save current queue as a playlist.
* `/play <name>`: Load a saved playlist.
