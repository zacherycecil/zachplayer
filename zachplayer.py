import traceback
from state import AppState
from event_handler import EventHandler
from controller import Controller
from mode import Mode
import sys
from player import Player
from logger import logger, log_uncaught_exceptions

state = AppState()
player = Player(state)
controller = Controller(state, player)
event_handler = EventHandler(state, controller)

sys.excepthook = lambda exctype, value, tb: log_uncaught_exceptions(exctype, value, tb, state)

controller.ui.draw()

while True:
    event_handler.handle_events()
