import logging

LOGGER_NAME = "vela47"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not any(current.get_name() == LOGGER_NAME for current in logger.handlers):
        handler = logging.StreamHandler()
        handler.set_name(LOGGER_NAME)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
