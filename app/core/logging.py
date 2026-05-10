import logging
import sys
from pythonjsonlogger import jsonlogger
from app.core.config import settings


def setup_logging():
    logger = logging.getLogger()
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger