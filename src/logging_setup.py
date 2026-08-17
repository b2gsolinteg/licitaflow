import logging
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


class _SafeFormatter(logging.Formatter):
    _patterns = (
        (re.compile(r"(?i)(authorization:\s*bearer\s+)[^\s]+"), r"\1[REDACTED]"),
        (re.compile(r"(?i)(password|secret|access[_-]?token)=([^\s,&]+)"), r"\1=[REDACTED]"),
    )

    def format(self, record):
        text = super().format(record)
        for pattern, replacement in self._patterns:
            text = pattern.sub(replacement, text)
        return text


def configure_logging(project_root: Path, environment: str = "production"):
    logger = logging.getLogger("licitanexo")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG if environment == "development" else logging.INFO)
    formatter = _SafeFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        "%Y-%m-%dT%H:%M:%S%z",
    )

    stream = logging.StreamHandler(sys.stdout)
    stream.setLevel(logger.level)
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    try:
        log_dir = project_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / "licitanexo.log",
            maxBytes=2_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logger.level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        # Ambientes serverless/read-only continuam operando com stdout.
        logger.warning("Diretório de logs local indisponível; usando stdout.")

    logger.propagate = False
    return logger
