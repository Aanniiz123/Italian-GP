import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# backend/config/logger.py -> backend/logs/
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"


def get_logger(name: str = __name__, log_file: Path = LOG_FILE, level: int = logging.INFO) -> logging.Logger:
    """
    Create (or retrieve) a logger that writes to both the console and a
    rotating log file.

    Parameters
    ----------
    name : str
        Logger name — pass __name__ from the calling module so log lines
        show which file they came from.
    log_file : Path
        Path to the log file. Defaults to backend/logs/pipeline.log.
    level : int
        Logging level (e.g. logging.INFO, logging.DEBUG).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid attaching duplicate handlers if get_logger is called more than once
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console output (what you currently see in the terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # File output — rotates at 5MB, keeps 3 backups so logs don't grow forever
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Stop double-logging if root logger also has handlers configured elsewhere
    logger.propagate = False

    return logger