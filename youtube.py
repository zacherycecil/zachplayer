import subprocess
import os
import threading
from logger import logger

lock = threading.Lock()

def on_channel_selected(channel_id, state):
    global lock
    first_id = fetch_first_video_id(channel_id)
    cached_id = read_cached_id(channel_id)

    with lock:
        state.files = [f"https://www.youtube.com/watch?v={first_id}"]

    if first_id != cached_id:
        logger.debug(f"New ID detected for channel {channel_id}: {first_id}, starting update.")
        thread = threading.Thread(target=fetch_video_ids, args=(channel_id, state, cached_id,))
        thread.start()
    else:
        logger.debug(f"No new videos for channel {channel_id}. Cached ID {cached_id} found, quitting.")

    with lock:
        try:
            if cached_id != None:
                state.files.extend([f"https://www.youtube.com/watch?v={item}" for item in read_cached_ids(channel_id)])
            state.files = list(dict.fromkeys(state.files))
        except FileNotFoundError as e:
            logger.debug("no channel file found")

def read_cached_id(channel_id):
    channel_file = os.path.join("channel_data", channel_id.lstrip("@") + ".txt")
    try:
        with open(channel_file, "r") as f:
            return f.readline().strip()
    except FileNotFoundError:
        return None

def read_cached_ids(channel_id):
    channel_file = os.path.join("channel_data", channel_id.lstrip("@") + ".txt")
    try:
        with open(channel_file, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return None

def fetch_first_video_id(channel_id):
    cmd = ["yt-dlp", "--get-id", "--playlist-end", "1", f"https://www.youtube.com/{channel_id}/videos"]
    result = subprocess.check_output(cmd, text=True).strip()
    return result

def fetch_video_ids(channel_id, state, cached_id):
    global lock
    to_add = []
    proc = subprocess.Popen(["yt-dlp", "--get-id", "--playlist-end", "10", f"https://www.youtube.com/{channel_id}/videos"],
        stdout=subprocess.PIPE, text=True
    )

    for line in proc.stdout:
        to_add.append(line.strip())

    to_add = to_add[1:]

    urls = [f"https://www.youtube.com/watch?v={item}" for item in to_add]

    channel_file = os.path.join("channel_data", channel_id.lstrip("@") + ".txt")
    try:
        with open(channel_file, "r") as f:
            existing_lines = f.readlines()
    except FileNotFoundError:
        existing_lines = []

    with open(channel_file, "w") as f:
        saved_ids = state.files
        state.files = []
        for line in to_add:
            if line == cached_id:
                logger.debug(f"Found cached ID {cached_id} while writing, stopping early.")
                break
            with lock:
                state.files = state.files + [f"https://www.youtube.com/watch?v={line}"]
            logger.debug(f"Adding ID: {line}")
            f.write(line + "\n")
        f.writelines(existing_lines)
        state.files = state.files + saved_ids
