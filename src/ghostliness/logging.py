from __future__ import annotations

import logging
import sys
from pathlib import Path

from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


def configure_logging(level: str = "INFO", log_dir: Path | str = "logs") -> Path:
    log_path = Path(log_dir) / "ghostliness.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stderr,
        level=level.upper(),
        colorize=True,
        format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}",
    )
    logger.add(
        log_path,
        level="TRACE",
        rotation="10 MB",
        retention=5,
        backtrace=True,
        diagnose=True,
        enqueue=True,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{name}:{function}:{line} | {message}"
        ),
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    return log_path
