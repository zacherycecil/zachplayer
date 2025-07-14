# ZachPlayer

A minimalist, mouse-only media player built for Raspberry Pi. ZachPlayer is designed for simple, distraction-free playback of music and video files with real-time CLI visuals and flexible control via mouse gestures. No keyboard required.

## Features

- ✪ **Audio & Video Playback** using `cvlc`
- 🔌 **Mouse-Only Control** via `evdev` (clicks + scroll)
- 📂 **Two Modes**:
  - **File Picker** – browse and choose media manually
  - **Random Play** – shuffle and loop through your playlist
- 🎧 **Live CLI Visualization** using `cava`
- 🧠 **Smart Playback Logic**:
  - Seamless looping and shuffling
  - Per-filetype `cvlc` argument handling (e.g. better support for `.opus`)
- 🎨 **Simple Terminal UI**, custom-drawn using Python (not curses)
- 💾 **State Tracking** with a centralized `AppState` class
- ⚗️ Built-in support for future features like YouTube channel playback

## Getting Started

### Requirements

- Raspberry Pi (tested on Pi 4)
- Linux (Raspberry Pi OS or similar)
- Python 3.9+
- VLC (`cvlc`)
- `cava` (for visualization)
- `evdev` (for input handling)
- `yt-dlp` (optional, for future YouTube support)

### Install Dependencies

```bash
sudo apt update
sudo apt install vlc cava python3-evdev
pip install yt-dlp
```

## Usage

From the project directory:

```bash
python3 zachplayer.py
```

Control the player using your mouse:

| Action       | Behavior                       |
| ------------ | ------------------------------ |
| Left Click   | Select / play / toggle modes   |
| Right Click  | Toggle between random & picker |
| Scroll Wheel | Navigate list or seek          |

## File Structure

```text
.
├── zachplayer.py          # Main entry point
├── controller.py          # Handles playback commands
├── state.py               # AppState object to store playback/UI state
├── ui.py                  # Terminal UI drawing logic
├── input_devices.txt      # Device filtering for evdev
├── history.txt            # (Optional) Tracks playback history
├── log.txt                # Debug log
├── youtube_list.txt       # (Planned) YouTube playlist state
├── /channel_data/         # (Planned) Per-channel video ID caching
```

## Planned Features

- 📺 **YouTube Mode**\
  Automatically fetch and play the latest videos from a list of subscribed channels using `yt-dlp`. Skips previously watched videos and builds a temp playlist on the fly.

- 🧹 **Swap File Cleaner**\
  Developer utility to remove Vim `.swp/.swo` files during active development.

- ⌨️ **Fallback Keyboard Controls**\
  Basic support for keyboards as an alternative control method.

## Known Limitations

- No GUI – this is strictly CLI-based.
- Not optimized for high-resolution video.
- No built-in playlist editor (random mode is automatic).
- Requires configuration to match your mouse device in `input_devices.txt`.

## License

MIT License — do whatever you want, just don't blame me if it breaks.

## Author

**Zachery**\
Built as a custom project for Raspberry Pi media playback with a unique focus on mouse-only interaction.

