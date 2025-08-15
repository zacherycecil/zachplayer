import logging
import os

MAX_LOG_LINES = 1000
LOG_FILE = "log.txt"

class TrimmingFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        try:
            self.trim_log()
        except Exception as e:
            print(f"Warning: Failed to trim log: {e}")

    def trim_log(self):
        if not os.path.exists(self.baseFilename):
            return

        with open(self.baseFilename, "r") as f:
            lines = f.readlines()

        if len(lines) > MAX_LOG_LINES:
            with open(self.baseFilename, "w") as f:
                f.writelines(lines[-MAX_LOG_LINES:])

logger = logging.getLogger("zachplayer")
logger.setLevel(logging.DEBUG)

file_handler = TrimmingFileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

def log_uncaught_exceptions(exctype, value, tb, state=None):
    logger.error("Uncaught exception", exc_info=(exctype, value, tb))
    if state:
        try:
            logger.debug(f"state.root_dir = {state.root_dir}")
            logger.debug(f"state.current_pos = {state.current_pos}")
            logger.debug(f"state.start_pos = {state.start_pos}")
            logger.debug(f"len(state.files) = {len(state.files)}")
            logger.debug(f"state.mode = {state.mode}")
        except Exception as e:
            logger.warning(f"Could not log full state: {e}")
