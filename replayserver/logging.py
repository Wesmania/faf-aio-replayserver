import logging

logger = logging.getLogger("replayserver")
stderr_handler = logging.StreamHandler()
stderr_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)-8s %(message)s'))
logger.addHandler(stderr_handler)
