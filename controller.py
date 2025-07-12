from state import AppState
from ui import UI
from mode import Mode
import pathlib

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
        self.app_state.mode = Mode.VIDEOSHUFFLE
        self.app_state.files = self.all_tv
        self.player.play(shuffle=True)

    def guide(self):
        self.app_state.mode = Mode.BROWSE
        self.app_state.files = get_list(self.tv_lib)
        self.ui.draw()

    def jukebox(self):
        self.app_state.mode = Mode.BROWSE
        self.app_state.files = get_list(self.music_lib)
        self.ui.draw()

    def dvds(self):
        self.app_state.mode = Mode.BROWSE
        self.app_state.files = get_list(self.movie_lib)
        self.ui.draw()

    def radio(self):
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
                self.navigate_up()
                self.ui.draw()

            case Mode.BROWSE:
                self.navigate_up()
                self.ui.draw()

            case m if m in play_modes:
                self.player.seek_forward()

    def scroll_down(self):
        mode = self.app_state.mode

        match mode:
            case Mode.TOPMENU:
                self.navigate_down()
                self.ui.draw()

            case Mode.BROWSE:
                self.navigate_down()
                self.ui.draw()

            case m if m in play_modes:
                self.player.seek_backward()

    def left_click(self):
        mode = self.app_state.mode
        state = self.app_state

        match mode:
            case Mode.TOPMENU:
                list(menu.values())[current_pos]()

            case Mode.BROWSE:
                selection = state.files[state.current_pos]
                if selection.is_dir():
                    state.reset_pos()
                    state.root_dir = selection
                    state.files = get_list(selection)
                    self.ui.draw()

                elif selection.is_file():
                    state.files = state.files[state.current_pos:] + state.files[:state.current_pos]
                    self.player.play()

            case m if m in self.play_modes:
                player.toggle_pause()

            case Mode.HISTORY:
                state.mode = Mode.TOPMENU
                self.ui.draw()

    def right_click(self):
        mode = self.app_state.mode
        state = self.app_state

        match mode:
            case Mode.BROWSE:
                state.root_dir = os.path.dirname(root_dir)
                state.files = get_list(state.root_dir)
                state.reset_pos()
                self.ui.draw()
            case m if m in [Mode.VIDEOSHUFFLE, Mode.MUSICSHUFFLE]:
                self.player.skip()
            case m if m in [Mode.VIDEO, Mode.MUSIC]:
                mode = Mode.BROWSE
                state.reset_pos()
                self.ui.draw()
            case Mode.HISTORY:
                state.reset_pos()
                mode = Mode.TOPMENU
                self.ui.draw()

    def middle_click(self):
        kill_player()
        self.app_state.reset_pos()
        self.app_state.mode = Mode.TOPMENU
        self.ui.draw()

    # HELPERS

    def get_ext(path):
        _, ext = os.path.splitext(path)
        return ext.lower()

    def get_list(path):
        return [entry for entry in os.scandir(path)]

    def navigate_up(self):
        state = self.app_state
        list_length = len(state.files)

        state.current_pos = (state.current_pos - 1) % list_length

        if state.current_pos == list_length - 1: # wrap
            state.start_pos = list_length - self.ui.max_items
        else:
            state.start_pos = max(0, (state.current_pos - self.ui.scroll_padding))

    def navigate_down(self):
        state = self.app_state
        list_length = len(state.files)

        state.current_pos = (state.current_pos + 1) % list_length

        if state.current_pos == 0:
            state.start_pos = 0
        else:
            max_start = max(0, (list_length - self.ui.max_items))
            state.start_pos = min(max_start, (state.current_pos - self.ui.scroll_padding))
