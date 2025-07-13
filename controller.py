from state import AppState
from ui import UI
from mode import Mode
import pathlib
import os
from logger import logger

class Controller:
    def __init__(self, app_state, player):
        self.app_state = app_state
        self.ui = UI(app_state, self)
        self.player = player
        self.play_modes = [Mode.VIDEO, Mode.VIDEOSHUFFLE, Mode.MUSIC, Mode.MUSICSHUFFLE]

        self.all_tv = [f for f in pathlib.Path("/nfs/_TV480p").rglob("*") if f.suffix.lower() in [".mp4", ".avi", ".mkv"]]
        self.all_songs = [f for f in pathlib.Path("/nfs/_Opus").rglob("*") if f.suffix.lower() in [".opus"]]
        self.all_movies = [f for f in pathlib.Path("/nfs/_Movies").rglob("*") if f.suffix.lower() in [".mp4", ".avi", ".mkv"]]

        self.tv_lib = "/nfs/_TV480p"
        self.movie_lib = "/nfs/_Movies"
        self.music_lib = "/nfs/_Opus"

    # MENU FUNCTIONS

    def cable_tv(self):
        self.ui.show_loading()
        self.app_state.mode = Mode.VIDEOSHUFFLE
        self.app_state.files = self.all_tv
        self.player.play(shuffle=True)

    def guide(self):
        self.app_state.mode = Mode.BROWSE
        self.app_state.reset_pos()
        self.app_state.files = self.get_list(self.tv_lib)
        self.app_state.root_dir = self.tv_lib
        self.ui.draw()

    def jukebox(self):
        self.app_state.mode = Mode.BROWSE
        self.app_state.reset_pos()
        self.app_state.files = self.get_list(self.music_lib)
        self.app_state.root_dir = self.music_lib
        self.ui.draw()

    def dvds(self):
        self.app_state.mode = Mode.BROWSE
        self.app_state.reset_pos()
        self.app_state.files = self.get_list(self.movie_lib)
        self.app_state.root_dir = self.movie_lib
        self.ui.draw()

    def radio(self):
        self.ui.show_loading()
        self.app_state.mode = Mode.MUSICSHUFFLE
        self.app_state.files = self.all_songs
        self.player.play(shuffle=True)

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

            case m if m in self.play_modes:
                self.player.seek_forward()

    def scroll_down(self):
        mode = self.app_state.mode

        match mode:
            case Mode.TOPMENU:
                self.app_state.current_pos = (self.app_state.current_pos + 1) % len(self.ui.menu)
                self.ui.draw()

            case Mode.BROWSE:
                self.navigate_down()
                self.ui.draw()

            case m if m in self.play_modes:
                self.player.seek_backward()

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
                    self.ui.draw()

                elif selection.is_file():
                    state.files = state.files[state.current_pos:] + state.files[:state.current_pos]
                    self.player.play()
                    ext = self.get_ext(selection)
                    if ext == ".opus":
                        self.ui.show_loading()
                        state.mode = Mode.MUSIC
                    elif ext in [".mkv", ".mp4", ".avi"]:
                        self.ui.show_loading()
                        state.mode = Mode.VIDEO

            case m if m in self.play_modes:
                self.player.toggle_pause()

            case Mode.HISTORY:
                state.mode = Mode.TOPMENU
                self.ui.draw()

    def right_click(self):
        state = self.app_state

        match state.mode:
            case Mode.BROWSE:
                state.root_dir = os.path.dirname(state.root_dir)
                state.files = self.get_list(state.root_dir)
                state.reset_pos()
                self.ui.draw()
            case m if m in [Mode.VIDEOSHUFFLE, Mode.MUSICSHUFFLE]:
                self.player.skip()
            case m if m in [Mode.VIDEO, Mode.MUSIC]:
                self.player.kill_player()
                state.files = sorted(state.files, key=lambda f: f.name)
                state.mode = Mode.BROWSE
                self.ui.draw()
            case Mode.HISTORY:
                state.reset_pos()
                state.mode = Mode.TOPMENU
                self.ui.draw()

    def middle_click(self):
        self.player.kill_player()
        self.app_state.reset_pos()
        self.app_state.mode = Mode.TOPMENU
        self.ui.draw()

    # HELPERS

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
