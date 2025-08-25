import logging
import logging.handlers
import sys
import os.path


class HousefireLoggerFactory:
    def __init__(
        self, deploy_env: str, log_dir_path: str
    ):  # Add log_dir_path parameter
        base_housefire_logger = logging.getLogger("housefire")
        base_housefire_logger.setLevel(
            logging.DEBUG if deploy_env == "development" else logging.INFO
        )

        base_housefire_format = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )

        if not os.path.exists(log_dir_path) or not os.path.isdir(log_dir_path):
            os.mkdir(log_dir_path)
        base_housefire_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir_path, "housefire.log"),  # Use log_dir_path
            backupCount=5,
            maxBytes=5000000,
        )

        base_housefire_handler.setFormatter(base_housefire_format)
        base_housefire_logger.addHandler(base_housefire_handler)

        if deploy_env == "development":
            base_housefire_console_handler = logging.StreamHandler()
            base_housefire_console_handler.setFormatter(base_housefire_format)
            base_housefire_logger.addHandler(base_housefire_console_handler)

        # catch all uncaught exceptions for logging
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            base_housefire_logger.critical(
                "Uncaught exception",
                exc_info=(exc_type, exc_value, exc_traceback),
            )

        sys.excepthook = handle_exception

        self._base_housefire_logger = base_housefire_logger

    def get_logger(self, name: str) -> logging.Logger:
        return self._base_housefire_logger.getChild(name)
