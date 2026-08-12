import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(project_root: Path, environment: str = "production"):
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("licitanexo")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG if environment == "development" else logging.INFO)
    handler = RotatingFileHandler(
        log_dir / "licitanexo.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s", "%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(handler)
    logger.propagate = False
    return logger
