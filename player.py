import subprocess
import random
import threading
import os
import signal
from mode import Mode
from logger import logger
import socket
import json
import time

class Player:
    def __init__(self, app_state):
        self.app_state = app_state
        self.stop_thread = False
        self.thread = None
        self.socket_path = "/tmp/mpvsocket"
        self.thread_lock = threading.Lock()
        self.shuffle = False

    def skip(self):
        if self.app_state.current_process:
            self.app_state.current_process.send_signal(signal.SIGINT)

    def seek_forward(self):
        self.mpv_command(["seek", 30, "relative"])
        self.show_playtime()

    def seek_backward(self):
        self.mpv_command(["seek", -30, "relative"])
        self.show_playtime()

    def show_playtime(self):
        current_time = self.mpv_command(["get_property", "time-pos"])
        total_time = self.mpv_command(["get_property", "duration"])

        formatted_current = time.strftime('%H:%M:%S', time.gmtime(current_time))
        formatted_total = time.strftime('%H:%M:%S', time.gmtime(total_time))

        self.mpv_command(["show-text", f"{formatted_current} / {formatted_total}", 3000])

    def show_title(self):
        title = self.mpv_command(["get_property", "media-title"])
        self.mpv_command(["show-text", title])

    def toggle_pause(self):
        self.mpv_command(["cycle", "pause"])
        paused = self.mpv_command(["get_property", "pause"])

        symbol = "⏸" if paused else "⏵"
        self.mpv_command(["show-text", symbol])

    def mpv_command(self, command):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.connect(self.socket_path)
            s.sendall(json.dumps({"command": command}).encode() + b"\n")
            data = s.recv(1024).decode()

            for line in data.strip().splitlines():
                try:
                    resp = json.loads(line)
                    if "data" in resp or "error" in resp:
                        return resp.get("data")
                except json.JSONDecodeError:
                    continue

            return None

    def kill_player(self):
        self.stop_thread = True

        if self.app_state.current_process:
            self.app_state.current_process.send_signal(signal.SIGINT)
            self.app_state.current_process.wait()
            self.app_state.current_process = None

        if self.thread and self.thread.is_alive():
            self.thread.join()

        self.thread = None

    def play(self, shuffle=False):
        self.kill_player()
        self.shuffle = shuffle
        if shuffle:
            random.shuffle(self.app_state.files)
        self.thread = threading.Thread(target=self._play_loop, daemon=True)
        self.thread.start()

    def _play_loop(self):
        self.stop_thread = False
        while self.app_state.files and not self.stop_thread:
            with self.thread_lock:
                next_file = self.app_state.files.pop(0)

                if not self.shuffle and self.app_state.mode != Mode.YOUTUBE and self.app_state.mode != Mode.YOUTUBEPLAY:
                    with open("history.txt", "a") as out:
                        out.write(f"{next_file}\n")

                self._play_one(next_file)
                self.app_state.files.append(next_file)

                self.app_state.current_process.wait()
                self.app_state.current_process = None

    def _play_one(self, video):
            with open("log.txt", "a") as out:
                try:
                    self.app_state.current_process = subprocess.Popen([
                        "mpv",
                        video,
                        f"--input-ipc-server={self.socket_path}",
                        "--ytdl-format=best[height=360]",
                        "--idle=no",
                        "--hwdec=no"],
                        stdout=out,
                        stderr=out
                    )
                    self.show_title()
                except Exception as e:
                    logger.debug(f"Failed to start mpv: {e}")
