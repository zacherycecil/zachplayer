from state import AppState
from ui import UI
from mode import Mode
import pathlib
import os
from logger import logger
import youtube as yt
import toml

class Controller:
    def __init__(self, app_state, player):
        self.app_state = app_state
        self.ui = UI(app_state, self)
        self.player = player

    # MENU FUNCTIONS

    def random(self, path, extensions):
        self.ui.show_loading()
        self.app_state.mode = Mode.RANDOM
        media = self.update_lib(path, extensions)
        self.app_state.files = media
        self.player.play(shuffle=True)

    def selection(self, path):
        self.app_state.mode = Mode.BROWSE
        self.app_state.reset_pos()
        self.app_state.files = self.get_list(path)
        self.app_state.root_dir = path
        self.ui.draw()

    def youtube(self):
        self.app_state.mode = Mode.YOUTUBE
        self.app_state.reset_pos()
        with open("youtube_list.txt") as f:
            self.app_state.files = [line.strip() for line in f if line.strip()]
        self.app_state.files.sort(key=lambda s: s.casefold())
        self.ui.draw()

    def history(self):
        self.app_state.mode = Mode.HISTORY
        self.ui.draw()

    # CONTROLS

    def scroll_up(self):
        mode = self.app_state.mode

        match mode:
            case Mode.TOPMENU:
                self.app_state.current_pos = (self.app_state.current_pos - 1) % len(self.ui.menu)
                self.ui.draw()

            case Mode.BROWSE:
                self.navigate_up()
                self.ui.draw()

            case m if m in [Mode.PLAYING, Mode.RANDOM, Mode.YOUTUBEPLAY]:
                self.player.seek_forward()

            case Mode.YOUTUBE:
                self.navigate_up()
                self.ui.draw()

    def scroll_down(self):
        mode = self.app_state.mode

        match mode:
            case Mode.TOPMENU:
                self.app_state.current_pos = (self.app_state.current_pos + 1) % len(self.ui.menu)
                self.ui.draw()

            case Mode.BROWSE:
                self.navigate_down()
                self.ui.draw()

            case m if m in [Mode.PLAYING, Mode.RANDOM, Mode.YOUTUBEPLAY]:
                self.player.seek_backward()

            case Mode.YOUTUBE:
                self.navigate_down()
                self.ui.draw()

    def left_click(self):
        mode = self.app_state.mode
        state = self.app_state

        match mode:
            case Mode.TOPMENU:
                list(self.ui.menu.values())[state.current_pos]()

            case Mode.BROWSE:
                selection = state.files[state.current_pos]
                if selection.is_dir():
                    state.reset_pos()
                    state.root_dir = selection
                    state.files = self.get_list(selection)
                    state.files = [file for file in state.files if file.name.lower() != "cover.jpg"]
                    self.ui.draw()

                elif selection.is_file():
                    self.app_state.mode = Mode.PLAYING
                    state.files = state.files[state.current_pos:] + state.files[:state.current_pos]
                    state.files = [file.path for file in state.files]
                    self.player.play()
                    self.ui.show_loading()

            case m if m in [Mode.PLAYING, Mode.YOUTUBEPLAY, Mode.RANDOM]:
                self.player.toggle_pause()

            case Mode.HISTORY:
                mode = Mode.TOPMENU
                self.ui.draw()

            case Mode.YOUTUBE:
                self.app_state.mode = Mode.YOUTUBEPLAY
                self.ui.show_loading()
                channel_id = state.files[state.current_pos]
                logger.debug("selected channel " + channel_id)
                self.ui.show_loading_msg("Fetching newest video IDs...")
                yt.on_channel_selected(channel_id, state)
                self.ui.show_loading()
                self.player.play(yt_id=channel_id)

    def right_click(self):
        state = self.app_state

        match state.mode:
            case Mode.BROWSE:
                state.root_dir = os.path.dirname(state.root_dir)
                state.files = self.get_list(state.root_dir)
                state.reset_pos()
                self.ui.draw()
            case m if m in [Mode.RANDOM, Mode.YOUTUBEPLAY]:
                self.player.skip()
            case Mode.PLAYING:
                self.player.kill_player()
                state.files = sorted(state.files, key=lambda f: f.name)
                state.mode = Mode.BROWSE
                self.ui.draw()
            case Mode.HISTORY:
                state.reset_pos()
                state.mode = Mode.TOPMENU
                self.ui.draw()
            case Mode.YOUTUBE:
                state.reset_pos()
                state.mode = Mode.TOPMENU
                self.ui.draw()

    def middle_click(self):
        self.player.kill_player()
        self.app_state.reset_pos()
        self.app_state.mode = Mode.TOPMENU
        self.ui.draw()

    # HELPERS

    def update_lib(self, path, ext):
        return [f for f in pathlib.Path(path).rglob("*") if f.suffix.lower() in ext]

    def get_ext(self, path):
        _, ext = os.path.splitext(path)
        return ext.lower()

    def get_list(self, path):
        return [entry for entry in os.scandir(path)]

    def navigate_up(self):
        state = self.app_state
        list_length = len(state.files)

        state.current_pos = (state.current_pos - 1) % list_length

        if state.current_pos == list_length - 1: # wrap
            state.start_pos = max(0, (list_length - self.ui.max_items))
        else:
            state.start_pos = max(0, min(state.start_pos, (state.current_pos - self.ui.scroll_padding)))

    def navigate_down(self):
        state = self.app_state
        list_length = len(state.files)

        state.current_pos = (state.current_pos + 1) % list_length

        if state.current_pos == 0:
            state.start_pos = 0
        else:
            if state.current_pos - self.ui.max_items + self.ui.scroll_padding >= state.start_pos and state.start_pos + self.ui.max_items < list_length:
                state.start_pos += 1
