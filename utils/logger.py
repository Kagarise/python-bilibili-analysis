import sys

from loguru import logger as _logger

logger = _logger

default_format = (
    "<g>{time:MM-DD HH:mm:ss}</g> "
    "[<lvl>{level}</lvl>] "
    "<c><u>{name}</u></c> | "
    # "<c>{function}:{line}</c>| "
    "{message}")

logger.remove()
logger.add(sys.stdout, format=default_format, level='DEBUG')
