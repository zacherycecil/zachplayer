from enum import Enum
from mode import Mode

class AppState:
    def __init__(self):
        self.mode = Mode.TOPMENU
        self.current_process = None
        self.current_pos = 0
        self.start_pos = 0
        self.files = []
        self.root_dir = ""
        self.extensions = []

    def reset_pos(self):
        self.current_pos = 0
        self.start_pos = 0
