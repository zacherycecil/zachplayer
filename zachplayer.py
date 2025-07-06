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

current_process = None
v_process = None

selector = DefaultSelector()

numbers = InputDevice('/dev/input/by-id/usb-Corsair_Corsair_Gaming_SCIMITAR_PRO_RGB_Mouse_1702D025AF7B08095F6DDFD2F5001C07-event-kbd')
clicks = InputDevice('/dev/input/by-id/usb-Corsair_Corsair_Gaming_SCIMITAR_PRO_RGB_Mouse_1702D025AF7B08095F6DDFD2F5001C07-event-mouse')

selector.register(numbers, EVENT_READ)
selector.register(clicks, EVENT_READ)

path = "/nfs/_TV480p"
all_tv = [f for f in pathlib.Path("/nfs/_TV480p").rglob("*") if f.suffix.lower() in [".mp4", ".avi", ".mkv"]]
all_songs = [f for f in pathlib.Path("/nfs/_Opus").rglob("*") if f.suffix.lower() in [".opus"]]
all_movies = [f for f in pathlib.Path("/nfs/_Movies").rglob("*") if f.suffix.lower() in [".mp4", ".avi", ".mkv"]]

with open("playlists/allsongs.m3u", "w") as f:
    for song in all_songs:
        f.write(str(song) + "\n")

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
    "Radio": lambda: play_random("opus", all_songs)
}

class Mode(Enum):
    PLAYING = 1
    TOPMENU = 2
    BROWSE = 3
    PLAYINGSELECTION = 4

mode = Mode.TOPMENU

# HELPER FUNCTIONS

def top_menu():
    global start_pos, current_pos, mode

    os.system('cls' if os.name == 'nt' else 'clear')
    mode = Mode.TOPMENU

    print("\n" * 6, end="")
    subprocess.run(['figlet', '-w', f'{col}', '-c', 'zachplayer'])
    print("\n" * 3, end="")

    menu_labels = list(menu.keys())
    for i, label in enumerate(menu_labels):
        if i==current_pos: print(f"\033[1m▶ {label} ◄\033\n[0m".center(col+7))
        else: print(f"{label.center(col)}\n")

def refresh_screen():
    global mode, start_pos, current_pos, files
    mode = Mode.BROWSE
    os.system('cls' if os.name == 'nt' else 'clear')
    if current_pos-start_pos>row-6 and len(files)-start_pos>10: start_pos+=1
    if current_pos-6<start_pos and start_pos>0: start_pos-=1

    print(f"\n\n\n\n\tCurrent Folder: {pathlib.Path(path).name}\n")
    for i in range(start_pos, min(start_pos+row-4, len(files))):
        if i==current_pos: print(f"\t\033[1m▶ {files[i].name}\033[0m")
        else: print(f"\t  {files[i].name}")

def get_list(path):
    global files
    files = []
    for f in os.scandir(path):
        files.append(f)

def skip_video():
    send_cvlc_stdin('next')

def send_cvlc_stdin(string):
    current_process.stdin.write(f'{string}\n'.encode())
    current_process.stdin.flush()
    with open("zachlog.txt", "w") as f:
        return f.readline()

def navigate(direction, media_files):
    global current_pos
    if direction == "up" and current_pos > 0: current_pos-=1
    elif direction == "down" and current_pos < len(media_files)-1: current_pos+=1

def watch_song_change():
    global current_process, mode
    while(mode == Mode.PLAYING):
        send_cvlc_stdin("get_title")

def kill_player():
    global current_process
    if current_process:
        current_process.send_signal(signal.SIGINT)
        current_process.wait()
        current_process = None

def play_videos(videos):
    global mode, current_process
    show_loading()
    kill_player()
    mode = Mode.PLAYING
    with open("zachlog.txt", "w") as out:
        current_process = subprocess.Popen([
            "cvlc",
            "--freetype-font=\"DejaVu Sans\"",
            "--freetype-background-color=0x000000",
            "--freetype-background-opacity=255",
            "--intf", "rc",
            "--play-and-exit",
            "--avcodec-hw=none"] + videos,
            stdin=subprocess.PIPE,
            stdout=out, stderr=out)

def play_music(songs):
    global mode, current_process
    if mode is not Mode.PLAYING: mode = Mode.PLAYINGSELECTION
    kill_player()
    os.system('cls' if os.name == 'nt' else 'clear')
    with open("zachlog.txt", "w") as out:
        current_process = subprocess.Popen([
            "cvlc",
            "--intf", "rc",
            "--loop",
            "--avcodec-hw=none"] + songs,
            stdin=subprocess.PIPE,
            stdout=out, stderr=out)


def play_random(media, files):
    global current_process, all_files
    random.shuffle(files)
    mode = Mode.PLAYING
    if media == "opus": play_music(files)
    elif media == "videos": play_videos(files)

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
    refresh_screen()

# INPUT FUNCTIONS

def scroll_up():
    global mode, files
    if mode == Mode.TOPMENU:
        navigate("up", menu)
        top_menu()
    elif mode == Mode.BROWSE:
        navigate("up", files)
        refresh_screen()
    elif mode in [Mode.PLAYING, Mode.PLAYINGSELECTION]:
        send_cvlc_stdin("seek +30")

def scroll_down():
    global mode, files
    if mode == Mode.TOPMENU:
        navigate("down", menu)
        top_menu()
    elif mode == Mode.BROWSE:
        navigate("down", files)
        refresh_screen()
    elif mode in [Mode.PLAYING, Mode.PLAYINGSELECTION]:
        send_cvlc_stdin("seek -30")

def left_click():
    global mode, start_pos, current_pos, files, current_process
    if mode in [Mode.PLAYING, Mode.PLAYINGSELECTION]: toggle_pause()
    elif mode==Mode.BROWSE:
        if files[current_pos].is_dir():
            open_menu(files[current_pos].path)

        elif files[current_pos].is_file():
            ext = pathlib.Path(files[current_pos]).suffix
            if ext == ".opus":
                play_music(files[current_pos:] + files[:current_pos])
            elif ext == ".mp4" or ext == ".mkv" or ext == ".avi":
                play_videos(files[current_pos:] + files[:current_pos])
    elif mode == Mode.TOPMENU:
        list(menu.values())[current_pos]()

def right_click():
    global mode, start_pos, current_pos, path, files, current_process
    if mode == Mode.BROWSE:
        open_menu(os.path.dirname(root_dir))
    elif mode == Mode.PLAYING:
        skip_video()
    elif mode == Mode.PLAYINGSELECTION:
        open_menu(root_dir)

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

