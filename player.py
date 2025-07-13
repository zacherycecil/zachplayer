import subprocess
import random
import threading
import os
import signal

class Player:
    def __init__(self, app_state):
        self.app_state = app_state
        self.stop_thread = False
        self.thread = None
        self.thread_lock = threading.Lock()
        self.shuffle = False
        self.audio_args = ["--intf", "rc", "--play-and-exit", "--avcodec-hw=none"]
        self.video_args = [
            "--freetype-font=DejaVu Sans",
            "--freetype-background-color=0x000000",
            "--freetype-background-opacity=255",
            "--intf", "rc",
            "--play-and-exit",
            "--avcodec-hw=none"
        ]

    def skip(self):
        if self.app_state.current_process:
            self.app_state.current_process.send_signal(signal.SIGINT)

    def seek_forward(self):
        self.send_cvlc_stdin("seek +30")

    def seek_backward(self):
        self.send_cvlc_stdin("seek -30")

    def toggle_pause(self):
        self.send_cvlc_stdin("pause")

    def send_cvlc_stdin(self, string):
        if self.app_state.current_process and self.app_state.current_process.stdin:
            self.app_state.current_process.stdin.write(f'{string}\n'.encode())
            self.app_state.current_process.stdin.flush()

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

                if not self.shuffle:
                    with open("history.txt", "a") as out:
                        out.write(f"{next_file.name}\n")

                self._play_one(next_file)
                self.app_state.files.append(next_file)

                self.app_state.current_process.wait()
                self.app_state.current_process = None

    def _play_one(self, path):
        _, ext = os.path.splitext(path)
        args = ""

        if ext.lower() == ".opus":
            args = self.audio_args
        elif ext.lower() in [".mkv", ".mp4", ".avi"]:
            args = self.video_args
        else:
            return

        with open("log.txt", "a") as out:
            self.app_state.current_process = subprocess.Popen(
                ["cvlc"] + args + [path],
                stdin=subprocess.PIPE,
                stdout=out,
                stderr=out
            )
