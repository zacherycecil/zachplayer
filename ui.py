import subprocess
import os
from mode import Mode
import pathlib
from collections import deque
from logger import logger

class EmptyFileError(Exception):
    pass

class UI:
    def __init__(self, app_state, controller):
        self.app_state = app_state
        self.controller = controller
        col, row = os.get_terminal_size()
        self.col = int(col)
        self.row = int(row)
        self.max_items = int(self.row * 0.65)
        self.scroll_padding = int(self.row * 0.2)

        self.menu = {
            "Cable TV": lambda: self.controller.cable_tv(),
            "Guide": lambda: self.controller.guide(),
            "Jukebox": lambda: self.controller.jukebox(),
            "Radio": lambda: self.controller.radio(),
            "DVDs": lambda: self.controller.dvds(),
            "YouTube": lambda: self.controller.youtube(),
            "History": lambda: self.controller.history(),
        }

    def draw(self):
        match self.app_state.mode:
            case Mode.TOPMENU:
                self.top_menu()
            case Mode.BROWSE:
                self.refresh_screen()
            case Mode.HISTORY:
                self.show_history()
            case Mode.YOUTUBE:
                self.show_youtube()

    # HELPERS

    def fit_name_to_screen(self, name):
        if len(name) <= self.col-27:
            return name
        else:
            return name[:self.col-24] + "..."

    def print_screen(self, lines):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n".join(lines))

    # RENDERING

    def top_menu(self):

        screen = []
        screen.append("\n" * 4)
        title = subprocess.run(['figlet', '-w', f'{self.col}', '-c', 'zachplayer'], capture_output=True, text=True)
        screen.append(f"{title.stdout}\n")

        menu_labels = list(self.menu.keys())
        for i, label in enumerate(menu_labels):
            if i == self.app_state.current_pos:
                screen.append(f" \033[1m▶ {label} ◄\033\n[0m".center(self.col+7))
            else:
                screen.append(f"{label.center(self.col)}\n")
        self.print_screen(screen)

    def refresh_screen(self):
        state = self.app_state
        logger.debug(f"UI.draw called with mode={state.mode}, root_dir={state.root_dir}")
        logger.debug(f"current_pos={state.current_pos}, start_pos={state.start_pos}, len(files)={len(state.files)}")
        screen = []
        screen.append(f"\n\n\n\n\tCurrent Folder: {pathlib.Path(state.root_dir).name}\n")

        for i in range(state.start_pos, min(state.start_pos + self.max_items, len(state.files))):
            file_name = self.fit_name_to_screen(state.files[i].name)
            if i == state.current_pos:
                screen.append(f"\t\033[1m▶ {file_name}\033[0m")
            else:
                screen.append(f"\t  {file_name}")

        self.print_screen(screen)

    def show_history(self):

        screen = []
        screen.append(f"\n\n\n\n\t\033[1mHistory\033[0m\n")
        try:
            if os.path.getsize("history.txt") == 0:
                raise EmptyFileError()
            with open("history.txt", "r") as f:
                for line in deque(f, maxlen=10):
                    screen.append("\t" + self.fit_name_to_screen(line))

        except (FileNotFoundError, EmptyFileError):
            print("\tNo video history.")

        finally:
            self.print_screen(screen)

    def music_display(self):

        screen = []
        screen.append(f" \033[1mNow Playing\033\n[0m".center(self.col+7))
        screen.append(title.center(self.col))
        size = self.row // 0.6
        art = subprocess.run(
            ['chafa', '-s',  f'{size}x{size}', os.path.join(self.app_state.root_dir, "cover.jpg")],
            capture_output=True,
            text=True
        )
        screen.append(art.stdout)
        self.print_screen(screen)

    def show_youtube(self):
        state = self.app_state
        screen = []
        screen.append(f"\n\n\n\n\tYouTube Channels:\n")

        state.files.sort()

        for i in range(state.start_pos, min(state.start_pos + self.max_items, len(state.files))):
            file_name = self.fit_name_to_screen(state.files[i])
            file_name = file_name.lstrip("@")
            if i == state.current_pos:
                screen.append(f"\t\033[1m▶ {file_name}\033[0m")
            else:
                screen.append(f"\t  {file_name}")

        self.print_screen(screen)

    def show_loading(self):
        screen = []
        screen.append("\n"*(self.row//2))
        screen.append("Loading...".center(self.col))
        self.print_screen(screen)
