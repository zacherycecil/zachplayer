import subprocess
import random
import threading

class Player:
    def __init__(self, app_state):
        self.app_state = app_state
        self.thread = None
        self.audio_args = ["--intf", "rc", "--play_and_exit", "--avcodec-hw=none"]
        self.video_args = [
            "--freetype-font=\"DejaVu Sans\"",
            "--freetype-background-color=0x000000",
            "--freetype-background-opacity=255",
            "--intf", "rc",
            "--play-and-exit",
            "--avcodec-hw=none"
        ]

    def skip(self):
        self.send_cvlc_stdin('next')

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
        if self.app_state.current_process:
            self.app_state.current_process.send_signal(signal.SIGINT)
            self.app_state.current_process.wait()
            self.app_state.current_process = None

    def play(self, shuffle=False):
        self.kill_player()
        if shuffle:
            random.shuffle(self.app_state.files)
        self.thread = threading.Thread(target=self._play_loop, daemon=True)
        self.thread.start()

    def _play_loop(self):
        while self.app_state.files:
            next_file = self.app_state.files.pop(0)
            self._play_one(next_file)
            self.app_state.files.append(next_file)

            self.app_state.current_process.wait()
            self.app_state.current_process = None

    def _play_one(self, path):
        self.kill_player()
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
