import logging
from app.core.config import get_settings

LOG_LEVEL = get_settings().log_level.upper()

LOG_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

log_level = LOG_LEVELS.get(LOG_LEVEL, logging.DEBUG)


def setup_logger():
    logger = logging.getLogger("secure_ai_insights_assistant")

    logger.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)-12s - %(levelname)-8s - [%(filename)-25s:%(lineno)4d] - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()