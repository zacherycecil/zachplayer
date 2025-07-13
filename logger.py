import logging

logger = logging.getLogger("zachplayer")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("log.txt")
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
        except Exception as e:
            logger.warning(f"Could not log full state: {e}")
