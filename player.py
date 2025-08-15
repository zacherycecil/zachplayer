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

        symbol = "status: paused" if paused else "status: playing"
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

    def play(self, shuffle=False, yt_id = ""):
        self.kill_player()
        self.shuffle = shuffle
        if shuffle:
            random.shuffle(self.app_state.files)
        self.thread = threading.Thread(target=self._play_loop, args=(yt_id,), daemon=True)
        self.thread.start()

    def _play_loop(self, yt_id):
        self.stop_thread = False
        while self.app_state.files and not self.stop_thread:
            with self.thread_lock:
                next_file = self.app_state.files.pop(0)

                logger.debug(f"Mode: {self.app_state.mode} - id: {yt_id}")

                if self.app_state.mode == Mode.YOUTUBEPLAY:
                    self._play_one_youtube(next_file, yt_id)

                else:

                    if not self.shuffle:
                        with open("history.txt", "a") as out:
                            out.write(f"{next_file}\n")

                    self._play_one(next_file)

                self.app_state.files.append(next_file)

                self.app_state.current_process.wait()
                self.app_state.current_process = None

    def _play_one(self, media):
            with open("log.txt", "a") as out:
                try:
                    self.app_state.current_process = subprocess.Popen([
                        "mpv",
                        media,
                        f"--input-ipc-server={self.socket_path}",
                        "--ytdl-format=best[height=360]",
                        "--idle=no",
                        "--hwdec=no",
                        "--quiet"],
                        stdout=out,
                        stderr=out
                    )
                except Exception as e:
                    logger.debug(f"Failed to start mpv: {e}")

    def _play_one_youtube(self, video, yt_id):
        with open("log.txt", "a") as out:

            cached_video = None
            for root, dirs, files in os.walk(f"channel_data/{yt_id}/videos/"):
                for file in files:
                    if video in file:
                        logger.debug(f"Found video with ID {video}")
                        cached_video = os.path.join(root, file)

            logger.debug(f"Mode: {self.app_state.mode} Cached video id: {cached_video}")

            if cached_video != None:
                try:
                    self.app_state.current_process = subprocess.Popen([
                        "mpv",
                        cached_video,
                        f"--input-ipc-server={self.socket_path}",
                        "--idle=no",
                        "--hwdec=no",
                        "--quiet"],
                        stdout=out,
                        stderr=out
                    )
                except Exception as e:
                    logger.debug(f"Failed to start mpv: {e}")
            else:
                self.app_state.current_process = subprocess.Popen([
                    "yt-dlp", "-q", "-f", "bestvideo[height<=480]+bestaudio",
                    "--merge-output-format", "mp4",
                    "-o", f"channel_data/{yt_id}/videos/%(title)s [%(id)s].%(ext)s",
                    f"https://www.youtube.com/watch?v={video}"],
                    stdout=out,
                    stderr=out
                )

                self.app_state.current_process.wait()

                downloaded_file = None
                for f in os.listdir(f"channel_data/{yt_id}/videos/"):
                    if video in f:
                        downloaded_file = os.path.join(f"channel_data/{yt_id}/videos/", f)
                        break

                self.app_state.current_process = subprocess.Popen([
                    "mpv",
                    f"{downloaded_file}",
                    f"--input-ipc-server={self.socket_path}",
                    "--quiet",
                    "--idle=no",
                    "--hwdec=no"],
                    stdout=out,
                    stderr=out
                )
