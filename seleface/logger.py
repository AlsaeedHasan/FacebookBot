import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from colorlog import ColoredFormatter


class Logger:
    """Enhanced logging system for the seleface package."""

    LOG_DIR = "logs"
    _instance = None
    _loggers = {}

    @classmethod
    def setup(
        cls,
        level: int = logging.INFO,
        log_to_file: bool = False,
        log_dir: str = LOG_DIR,
        max_file_size: int = 5 * 1024 * 1024,
        backup_count: int = 3,
    ) -> None:
        cls._instance = cls(level, log_to_file, log_dir, max_file_size, backup_count)

    def __init__(
        self,
        level: int = logging.INFO,
        log_to_file: bool = False,
        log_dir: str = LOG_DIR,
        max_file_size: int = 5 * 1024 * 1024,
        backup_count: int = 3,
    ):
        self.level = level
        self.log_to_file = log_to_file
        self.log_dir = log_dir
        self.max_file_size = max_file_size
        self.backup_count = backup_count

        if self.log_to_file and not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        self._configure_root_logger()

    def _configure_root_logger(self):
        root_logger = logging.getLogger()
        root_logger.setLevel(self.level)

        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Console handler with colorlog
        console_handler = logging.StreamHandler()
        color_formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
        console_handler.setFormatter(color_formatter)
        root_logger.addHandler(console_handler)

        # File handler (no color)
        if self.log_to_file:
            file_handler = RotatingFileHandler(
                os.path.join(self.log_dir, "seleface.log"),
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
            )
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        if cls._instance is None:
            cls.setup()

        logger_name = name if name else "seleface"
        if logger_name in cls._loggers:
            return cls._loggers[logger_name]

        logger = logging.getLogger(logger_name)
        cls._loggers[logger_name] = logger
        return logger


# Initialize default logger
Logger.setup()

# For backward compatibility
default_logger = Logger.get_logger()
