# ZachPlayer

A minimalist, mouse-only media player built for Raspberry Pi. ZachPlayer is designed for simple, distraction-free playback of music and video files with real-time CLI visuals and flexible control via mouse gestures. No keyboard required.

## Features

- ✪ **Audio & Video Playback** using `cvlc`
- 🔌 **Mouse-Only Control** via `evdev` (clicks + scroll)
- 📂 **Top Menu + Modes**:
  - **File Picker** – browse and choose media manually
  - **Random Play** – shuffle and loop through your playlist
- 🎨 **Simple Terminal UI**, custom-drawn using Python (not curses)

## Getting Started

### Requirements

- Python 3.9+
- VLC (`cvlc`)
- `evdev` (for input handling)

## Usage

From the project directory:

```bash
python3 zachplayer.py
```

Control the player using your mouse:

| Action       | Behavior                             |
| ------------ | ------------------------------------ |
| Left Click   | Select or play / pause               |
| Right Click  | Toggle between random & picker       |
| Scroll Wheel | Navigate list or skip 30sec in media |
| Middle Click | Return to Top Menu                   |

## File Structure

```text
.
├── zachplayer.py          # Main entry point
├── controller.py          # Handles playback commands
├── state.py               # AppState object to store playback/UI state
├── ui.py                  # Terminal UI drawing logic
├── event_handler.py       # Mouse click reader
├── player.py              # CVLC player
├── logger.py              # Python logger to log file
├── mode.py                # Mode enum
├── input_devices.txt      # Device filtering for evdev
├── history.txt            # (Optional) Tracks playback history
├── log.txt                # Debug log
├── youtube_list.txt       # (Planned) YouTube playlist state
```

## Planned Features

- 📺 **YouTube Mode**\
  Automatically fetch and play the latest videos from a list of subscribed channels using `yt-dlp`.

## Known Limitations

- No GUI – this is strictly CLI-based.
- Not optimized for high-resolution video.
- No built-in playlist editor (random mode is automatic).
- Requires configuration to match your mouse device in `input_devices.txt`.

## Author

**Zachery**\
Built as a custom project for Raspberry Pi media playback with a unique focus on mouse-only interaction.

