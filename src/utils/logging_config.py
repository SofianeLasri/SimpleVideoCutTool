"""Configuration du système de logging.

Stratégie de logging:
- Logger application: logs/app.log avec rotation quotidienne (7 jours)
- Logger par encodage: logs/encoding_YYYY-MM-DD_HHMMSS.log
"""

from __future__ import annotations

import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING

from utils.paths import get_logs_dir

if TYPE_CHECKING:
    pass


# Nom du logger principal
APP_LOGGER_NAME: str = "SimpleVideoCut"


def setup_app_logging(debug: bool = False) -> logging.Logger:
    """Configure le logger principal de l'application.

    Args:
        debug: Si True, active le niveau DEBUG pour la console

    Returns:
        Logger configuré pour l'application
    """
    logs_dir: Path = get_logs_dir()

    logger: logging.Logger = logging.getLogger(APP_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)

    # Éviter les doublons si déjà configuré
    if logger.handlers:
        return logger

    # Format des messages
    file_formatter: logging.Formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_formatter: logging.Formatter = logging.Formatter(
        "%(levelname)s - %(message)s"
    )

    # Handler console
    console_handler: logging.StreamHandler = logging.StreamHandler()  # type: ignore[type-arg]
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Handler fichier avec rotation quotidienne
    log_file: Path = logs_dir / "app.log"
    file_handler: TimedRotatingFileHandler = TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.info("Logging initialisé")
    return logger


def create_encoding_session_logger(video_name: str = "") -> tuple[logging.Logger, Path]:
    """Crée un logger dédié pour une session d'encodage.

    Args:
        video_name: Nom de la vidéo (optionnel, pour le nom du fichier)

    Returns:
        Tuple (logger, chemin du fichier log)
    """
    logs_dir: Path = get_logs_dir()
    timestamp: str = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    # Nettoyer le nom de vidéo pour le fichier
    safe_name: str = ""
    if video_name:
        safe_name = "".join(c for c in video_name if c.isalnum() or c in "._- ")[:30]
        safe_name = f"_{safe_name}"

    log_filename: str = f"encoding_{timestamp}{safe_name}.log"
    log_file: Path = logs_dir / log_filename

    # Créer un logger unique pour cette session
    logger_name: str = f"encoding_{timestamp}"
    logger: logging.Logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Éviter les doublons
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    # Handler fichier
    formatter: logging.Formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler: logging.FileHandler = logging.FileHandler(
        filename=str(log_file),
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info(f"=== Session d'encodage démarrée ===")
    logger.info(f"Fichier log: {log_file}")

    return logger, log_file


def get_app_logger() -> logging.Logger:
    """Retourne le logger principal de l'application.

    Returns:
        Logger de l'application (crée si nécessaire)
    """
    logger: logging.Logger = logging.getLogger(APP_LOGGER_NAME)
    if not logger.handlers:
        return setup_app_logging()
    return logger
