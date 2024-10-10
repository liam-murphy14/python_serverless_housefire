import logging
import logging.handlers
import sys
import os.path

_base_housefire_logger = logging.getLogger("housefire")
_base_housefire_format = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)

if not os.path.exists("/tmp/housefire_logs") or not os.path.isdir(
    "/tmp/housefire_logs"
):
    os.mkdir("/tmp/housefire_logs")

_base_housefire_handler = logging.handlers.RotatingFileHandler(
    os.path.join("/tmp/housefire_logs", "housefire.log"),
    backupCount=5,
    maxBytes=5000000,
)

_base_housefire_handler.setFormatter(_base_housefire_format)
_base_housefire_logger.addHandler(_base_housefire_handler)
_base_housefire_logger.setLevel(logging.DEBUG)


# catch all uncaught exceptions for logging
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    _base_housefire_logger.critical(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


sys.excepthook = handle_exception


def get_logger(name: str) -> logging.Logger:
    return _base_housefire_logger.getChild(name)
