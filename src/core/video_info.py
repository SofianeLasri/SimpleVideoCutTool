"""Extraction des métadonnées vidéo via ffprobe.

Ce module permet d'extraire les informations essentielles d'un fichier vidéo:
- Durée
- Résolution
- FPS
- Codecs audio/vidéo
- Présence de piste audio
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..utils.ffmpeg_wrapper import build_probe_command
from ..utils.logging_config import get_app_logger


@dataclass(frozen=True)
class VideoMetadata:
    """Métadonnées d'un fichier vidéo."""

    duration_ms: int
    """Durée totale en millisecondes."""

    width: int
    """Largeur en pixels."""

    height: int
    """Hauteur en pixels."""

    fps: float
    """Images par seconde."""

    video_codec: str
    """Codec vidéo (ex: h264, hevc)."""

    audio_codec: str | None
    """Codec audio ou None si pas d'audio."""

    has_audio: bool
    """True si le fichier contient une piste audio."""

    file_size_bytes: int
    """Taille du fichier en octets."""

    @property
    def duration_seconds(self) -> float:
        """Durée en secondes."""
        return self.duration_ms / 1000.0

    @property
    def resolution(self) -> str:
        """Résolution formatée (ex: 1920x1080)."""
        return f"{self.width}x{self.height}"

    @property
    def duration_formatted(self) -> str:
        """Durée formatée (HH:MM:SS)."""
        total_seconds: int = self.duration_ms // 1000
        hours: int = total_seconds // 3600
        minutes: int = (total_seconds % 3600) // 60
        seconds: int = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class VideoInfo:
    """Classe pour extraire les informations d'un fichier vidéo."""

    # Extensions vidéo supportées
    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv",
        ".webm", ".m4v", ".mpeg", ".mpg", ".3gp", ".ts"
    })

    @classmethod
    def probe(cls, file_path: str | Path) -> VideoMetadata:
        """Extrait les métadonnées d'un fichier vidéo.

        Args:
            file_path: Chemin vers le fichier vidéo

        Returns:
            VideoMetadata avec toutes les informations

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            ValueError: Si le fichier n'est pas une vidéo valide
            RuntimeError: Si ffprobe échoue
        """
        logger = get_app_logger()
        path: Path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {path}")

        logger.debug(f"Analyse de: {path}")

        # Exécuter ffprobe
        command: list[str] = build_probe_command(path)

        try:
            result: subprocess.CompletedProcess[str] = subprocess.run(
                command,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
            )
        except Exception as e:
            logger.error(f"Erreur ffprobe: {e}")
            raise RuntimeError(f"Impossible d'analyser le fichier: {e}")

        if result.returncode != 0:
            logger.error(f"ffprobe erreur: {result.stderr}")
            raise RuntimeError(f"ffprobe a échoué: {result.stderr}")

        # Parser le JSON
        try:
            data: dict[str, Any] = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON: {e}")
            raise ValueError(f"Format de sortie ffprobe invalide: {e}")

        return cls._parse_probe_data(data, path)

    @classmethod
    def _parse_probe_data(cls, data: dict[str, Any], file_path: Path) -> VideoMetadata:
        """Parse les données JSON de ffprobe.

        Args:
            data: Données JSON de ffprobe
            file_path: Chemin du fichier pour la taille

        Returns:
            VideoMetadata extraites

        Raises:
            ValueError: Si les données sont incomplètes
        """
        streams: list[dict[str, Any]] = data.get("streams", [])
        format_info: dict[str, Any] = data.get("format", {})

        # Chercher les streams vidéo et audio
        video_stream: dict[str, Any] | None = None
        audio_stream: dict[str, Any] | None = None

        for stream in streams:
            codec_type: str = stream.get("codec_type", "")
            if codec_type == "video" and video_stream is None:
                video_stream = stream
            elif codec_type == "audio" and audio_stream is None:
                audio_stream = stream

        if video_stream is None:
            raise ValueError("Aucun flux vidéo trouvé dans le fichier")

        # Extraire les informations vidéo
        width: int = int(video_stream.get("width", 0))
        height: int = int(video_stream.get("height", 0))
        video_codec: str = video_stream.get("codec_name", "unknown")

        # FPS (peut être sous différents formats)
        fps: float = cls._parse_fps(video_stream)

        # Durée (en secondes dans format)
        duration_str: str = format_info.get("duration", "0")
        try:
            duration_seconds: float = float(duration_str)
        except ValueError:
            duration_seconds = 0.0
        duration_ms: int = int(duration_seconds * 1000)

        # Informations audio
        has_audio: bool = audio_stream is not None
        audio_codec: str | None = None
        if audio_stream:
            audio_codec = audio_stream.get("codec_name")

        # Taille du fichier
        file_size: int = file_path.stat().st_size if file_path.exists() else 0

        return VideoMetadata(
            duration_ms=duration_ms,
            width=width,
            height=height,
            fps=fps,
            video_codec=video_codec,
            audio_codec=audio_codec,
            has_audio=has_audio,
            file_size_bytes=file_size
        )

    @classmethod
    def _parse_fps(cls, video_stream: dict[str, Any]) -> float:
        """Parse le FPS depuis un stream vidéo.

        Le FPS peut être dans r_frame_rate ou avg_frame_rate
        au format "num/den" ou directement un nombre.

        Args:
            video_stream: Données du stream vidéo

        Returns:
            FPS en float
        """
        fps_str: str = video_stream.get("r_frame_rate", "")

        if not fps_str:
            fps_str = video_stream.get("avg_frame_rate", "0/1")

        try:
            if "/" in fps_str:
                num_str, den_str = fps_str.split("/")
                num: int = int(num_str)
                den: int = int(den_str)
                if den > 0:
                    return round(num / den, 3)
            else:
                return float(fps_str)
        except (ValueError, ZeroDivisionError):
            pass

        return 0.0

    @classmethod
    def is_supported_format(cls, file_path: str | Path) -> bool:
        """Vérifie si l'extension du fichier est supportée.

        Args:
            file_path: Chemin vers le fichier

        Returns:
            True si l'extension est supportée
        """
        path: Path = Path(file_path)
        return path.suffix.lower() in cls.SUPPORTED_EXTENSIONS

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """Retourne la liste des extensions supportées.

        Returns:
            Liste des extensions (avec le point)
        """
        return sorted(cls.SUPPORTED_EXTENSIONS)
