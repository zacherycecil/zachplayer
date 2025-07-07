import subprocess
import os
import sys
import random
import signal
import time
import evdev
from evdev import InputDevice, categorize, ecodes
from selectors import DefaultSelector, EVENT_READ
import pathlib
from enum import Enum
from collections import deque
import threading
import traceback

def log_uncaught_exceptions(exctype, value, tb):
    with open("log.txt", "a") as f:
        traceback.print_exception(exctype, value, tb, file=f)

sys.excepthook = log_uncaught_exceptions

current_process = None

selector = DefaultSelector()

numbers = InputDevice('/dev/input/by-id/usb-Corsair_Corsair_Gaming_SCIMITAR_PRO_RGB_Mouse_1702D025AF7B08095F6DDFD2F5001C07-event-kbd')
clicks = InputDevice('/dev/input/by-id/usb-Corsair_Corsair_Gaming_SCIMITAR_PRO_RGB_Mouse_1702D025AF7B08095F6DDFD2F5001C07-event-mouse')

selector.register(numbers, EVENT_READ)
selector.register(clicks, EVENT_READ)

path = "/nfs/_TV480p"
all_tv = [f for f in pathlib.Path("/nfs/_TV480p").rglob("*") if f.suffix.lower() in [".mp4", ".avi", ".mkv"]]
all_songs = [f for f in pathlib.Path("/nfs/_Opus").rglob("*") if f.suffix.lower() in [".opus"]]
all_movies = [f for f in pathlib.Path("/nfs/_Movies").rglob("*") if f.suffix.lower() in [".mp4", ".avi", ".mkv"]]

files = []
root_dir = []

current_pos = 0
start_pos = 0

current_song = ""

col, row = os.get_terminal_size()

menu = {
    "Cable TV": lambda: play_random("videos", all_tv),
    "Guide": lambda: open_menu("/nfs/_TV480p"),
    "Jukebox": lambda: open_menu("/nfs/_Opus"),
    "DVDs": lambda: open_menu("/nfs/_Movies"),
    "Radio": lambda: play_random("opus", all_songs),
    "History": lambda: show_history(),
}

class EmptyFileError(Exception):
    pass

class Mode(Enum):
    VIDEO = 1
    TOPMENU = 2
    BROWSE = 3
    VIDEOSHUFFLE = 4
    MUSIC = 5
    MUSICSHUFFLE = 6
    HISTORY = 7

mode = Mode.TOPMENU

play_modes = [Mode.VIDEO, Mode.VIDEOSHUFFLE, Mode.MUSIC, Mode.MUSICSHUFFLE]

# HELPER FUNCTIONS

def top_menu():
    global start_pos, current_pos, mode

    os.system('cls' if os.name == 'nt' else 'clear')
    mode = Mode.TOPMENU

    print("\n" * 5, end="")
    subprocess.run(['figlet', '-w', f'{col}', '-c', 'zachplayer'])
    print("\n" * 3, end="")

    menu_labels = list(menu.keys())
    for i, label in enumerate(menu_labels):
        if i==current_pos: print(f" \033[1m▶ {label} ◄\033\n[0m".center(col+7))
        else: print(f"{label.center(col)}\n")

def refresh_screen(path):
    global mode, start_pos, current_pos, files, root_dir
    mode = Mode.BROWSE
    os.system('cls' if os.name == 'nt' else 'clear')
    if current_pos-start_pos>row-18 and len(files)-start_pos>18: start_pos+=1
    elif current_pos-6<start_pos and start_pos>0: start_pos-=1

    print(f"\n\n\n\n\tCurrent Folder: {pathlib.Path(path).name}\n")
    for i in range(start_pos, min(start_pos+row-10, len(files))):
        file_name = fit_name_to_screen(files[i].name)
        if i==current_pos: print(f"\t\033[1m▶ {file_name}\033[0m")
        else: print(f"\t  {file_name}")

def show_history():
    global mode
    os.system('cls' if os.name == 'nt' else 'clear')
    mode = Mode.HISTORY
    print(f"\n\n\n\n\t\033[1mHistory\033[0m\n")
    try:
        if os.path.getsize("history.txt") == 0:
            raise EmptyFileError()
        with open("history.txt", "r") as f:
            for line in deque(f, maxlen=10):
                print("\t" + fit_name_to_screen(line), flush=True)
    except (FileNotFoundError, EmptyFileError):
        print("\tNo video history.")

def fit_name_to_screen(name):
    if len(name) <= col-24:
        return name
    else:
        return name[:col-24] + "..."

def get_list(path):
    global files
    files = []
    for f in os.scandir(path):
        files.append(f)

def skip():
    send_cvlc_stdin('next')

def timeskip(direction):
    if direction == "forward":
        send_cvlc_stdin("seek +30")
    elif direction == "backward":
        send_cvlc_stdin("seek -30")

def send_cvlc_stdin(string):
    global current_process
    current_process.stdin.write(f'{string}\n'.encode())
    current_process.stdin.flush()
    time.sleep(0.05)
    with open("log.txt", "r") as f:
        for line in reversed(f.readlines()):
            if line and line.strip() != ">":
                return line.replace(">", "").strip()

def navigate(direction, media_files):
    global current_pos, start_pos
    if direction == "up":
        if current_pos > 0:
            current_pos-=1
        else:
            current_pos = len(media_files)-1
            start_pos = len(media_files) - 18
    elif direction == "down":
        if current_pos < len(media_files)-1:
            current_pos+=1
        else:
            current_pos=0
            start_pos = 0

def watch_media_change():
    global current_process, mode
    try:
        with open("history.txt", "a+") as f:
            while(mode == Mode.VIDEO):
                playing = send_cvlc_stdin("is_playing")
                if playing == "1":
                    time.sleep(5)
                    cvlc_out = send_cvlc_stdin("get_title")
                    f.seek(0)
                    lines = f.readlines()
                    if len(lines) == 0 or cvlc_out != lines[-1].strip():
                        f.write(cvlc_out + "\n")
                time.sleep(90)
            while(mode == Mode.MUSIC or mode == Mode.MUSICSHUFFLE):
                send_cvlc_stdin("get_title")
                time.sleep(3)
    except Exception:
        with open("log.txt", "a") as f:
            f.write("Exception:\n")
            traceback.print_exc(file=f)
            watch_media_change()

def kill_player():
    global current_process
    if current_process:
        current_process.send_signal(signal.SIGINT)
        current_process.wait()
        current_process = None

def play_selected(media, media_files):
    global mode
    if media == "opus":
        mode = Mode.MUSIC
        play_music(media_files)
    elif media == "videos":
        mode = Mode.VIDEO
        play_videos(media_files)
        thread = threading.Thread(target=watch_media_change, daemon=True)
        thread.start()

def play_videos(videos):
    global mode, current_process
    show_loading()
    kill_player()
    with open("log.txt", "a") as out:
        current_process = subprocess.Popen([
            "cvlc",
            "--freetype-font=\"DejaVu Sans\"",
            "--freetype-background-color=0x000000",
            "--freetype-background-opacity=255",
            "--intf", "rc",
            "--play-and-exit",
            "--aout=alsa",
            "--alsa-audio-device=default",
            "--avcodec-hw=none"] + videos,
            stdin=subprocess.PIPE,
            stdout=out, stderr=out)

def play_music(songs):
    global mode, current_process
    kill_player()
    os.system('cls' if os.name == 'nt' else 'clear')
    with open("log.txt", "a") as out:
        current_process = subprocess.Popen([
            "cvlc",
            "--intf", "rc",
            "--loop",
            "--avcodec-hw=none"] + songs,
            stdin=subprocess.PIPE,
            stdout=out, stderr=out)

def play_random(media, media_files):
    global mode
    random.shuffle(media_files)
    if media == "opus":
        play_music(media_files)
        mode = Mode.MUSICSHUFFLE
    elif media == "videos":
        play_videos(media_files)
        mode = Mode.VIDEOSHUFFLE

def toggle_pause():
    global current_process
    current_process.stdin.write(b'pause\n')
    current_process.stdin.flush()

def show_loading():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n"*(row//2), end="")
    print("Loading...".center(col))

def open_menu(path):
    global current_pos, root_dir, start_pos, mode
    root_dir = path
    mode = Mode.BROWSE
    current_pos = 0
    start_pos = 0

    kill_player()
    get_list(path)
    refresh_screen(path)

# INPUT FUNCTIONS

def scroll_up():
    global mode, files, root_dir
    if mode == Mode.TOPMENU:
        navigate("up", menu)
        top_menu()
    elif mode == Mode.BROWSE:
        navigate("up", files)
        refresh_screen(root_dir)
    elif mode in play_modes:
        timeskip("forward")

def scroll_down():
    global mode, files
    if mode == Mode.TOPMENU:
        navigate("down", menu)
        top_menu()
    elif mode == Mode.BROWSE:
        navigate("down", files)
        refresh_screen(root_dir)
    elif mode in play_modes:
        timeskip("backward")

def left_click():
    global mode, current_pos, files
    if mode in play_modes: toggle_pause()
    elif mode==Mode.BROWSE:
        if files[current_pos].is_dir():
            open_menu(files[current_pos].path)

        elif files[current_pos].is_file():
            ext = pathlib.Path(files[current_pos]).suffix
            media_files = files[current_pos:] + files[:current_pos]

            if ext == ".opus":
                play_selected("opus", media_files)
            elif ext == ".mp4" or ext == ".mkv" or ext == ".avi":
                play_selected("videos", media_files)

    elif mode == Mode.TOPMENU:
        list(menu.values())[current_pos]()
    elif mode == Mode.HISTORY:
        top_menu()

def right_click():
    global mode, root_dir
    if mode == Mode.BROWSE:
        open_menu(os.path.dirname(root_dir))
    elif mode in [Mode.VIDEOSHUFFLE, Mode.MUSICSHUFFLE]:
        skip()
    elif mode in [Mode.VIDEO, Mode.MUSIC]:
        open_menu(root_dir)
    elif mode == Mode.HISTORY:
        top_menu()

def middle_click():
    global current_pos, start_pos
    kill_player()
    current_pos = 0
    start_pos = 0
    top_menu()

# COMMANDS AND EVENT READ

top_menu()

while True:
    for key, mask in selector.select():
        device = key.fileobj
        for event in device.read():
            if event.type == ecodes.EV_KEY:
                if event.value == 1:  # key down only
                    if event.code in [ecodes.BTN_LEFT]:
                        left_click()
                    elif event.code in [ecodes.BTN_RIGHT]:
                        right_click()
                    elif event.code in [ecodes.BTN_MIDDLE]:
                        middle_click()

            elif event.type == ecodes.EV_REL:
                if event.code == ecodes.REL_WHEEL:
                    if event.value > 0:
                        scroll_up()
                    elif event.value < 0:
                        scroll_down()

