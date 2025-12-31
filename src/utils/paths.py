"""Gestion des chemins pour les ressources et binaires FFmpeg.

Ce module gère la résolution des chemins de manière compatible avec:
- L'exécution en développement (depuis les sources)
- L'exécution en tant qu'exécutable PyInstaller
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Final


def _get_base_path() -> Path:
    """Retourne le chemin de base de l'application.

    En mode développement, c'est le dossier racine du projet.
    En mode PyInstaller, c'est le dossier temporaire _MEIPASS.
    """
    if getattr(sys, "frozen", False):
        # Exécution en tant qu'exécutable PyInstaller
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        # Exécution en développement
        return Path(__file__).parent.parent.parent


# Chemin de base mis en cache
_BASE_PATH: Final[Path] = _get_base_path()


def get_ffmpeg_path() -> Path:
    """Retourne le chemin vers l'exécutable ffmpeg.

    Returns:
        Path vers ffmpeg.exe

    Raises:
        FileNotFoundError: Si ffmpeg.exe n'est pas trouvé
    """
    ffmpeg_path: Path = _BASE_PATH / "ffmpeg" / "ffmpeg.exe"
    if not ffmpeg_path.exists():
        raise FileNotFoundError(f"FFmpeg non trouvé: {ffmpeg_path}")
    return ffmpeg_path


def get_ffprobe_path() -> Path:
    """Retourne le chemin vers l'exécutable ffprobe.

    Returns:
        Path vers ffprobe.exe

    Raises:
        FileNotFoundError: Si ffprobe.exe n'est pas trouvé
    """
    ffprobe_path: Path = _BASE_PATH / "ffmpeg" / "ffprobe.exe"
    if not ffprobe_path.exists():
        raise FileNotFoundError(f"FFprobe non trouvé: {ffprobe_path}")
    return ffprobe_path


def get_resource_path(relative_path: str) -> Path:
    """Retourne le chemin absolu vers une ressource.

    Args:
        relative_path: Chemin relatif depuis la racine du projet

    Returns:
        Path absolu vers la ressource
    """
    return _BASE_PATH / relative_path


def get_logs_dir() -> Path:
    """Retourne le chemin vers le dossier des logs.

    Le dossier est créé s'il n'existe pas.

    Returns:
        Path vers le dossier logs
    """
    if getattr(sys, "frozen", False):
        # En mode exe, utiliser le dossier à côté de l'exécutable
        logs_dir: Path = Path(sys.executable).parent / "logs"
    else:
        # En mode développement
        logs_dir = _BASE_PATH / "logs"

    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def get_project_root() -> Path:
    """Retourne le chemin racine du projet.

    Returns:
        Path vers la racine du projet
    """
    return _BASE_PATH
