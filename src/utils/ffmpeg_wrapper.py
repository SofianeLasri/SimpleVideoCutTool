"""Wrapper pour les commandes FFmpeg.

Ce module construit les commandes FFmpeg pour:
- L'encodage H264 + AAC
- La découpe multi-segments
- Le tracking de progression
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from .paths import get_ffmpeg_path, get_ffprobe_path


# Paramètres d'encodage H264
H264_PRESET: Final[str] = "medium"
H264_CRF: Final[str] = "18"

# Paramètres audio AAC
AAC_BITRATE: Final[str] = "192k"


def build_probe_command(input_path: str | Path) -> list[str]:
    """Construit la commande ffprobe pour extraire les métadonnées.

    Args:
        input_path: Chemin vers le fichier vidéo

    Returns:
        Liste des arguments de commande
    """
    ffprobe: Path = get_ffprobe_path()

    return [
        str(ffprobe),
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(input_path)
    ]


def build_single_segment_command(
    input_path: str | Path,
    output_path: str | Path,
    start_seconds: float,
    end_seconds: float
) -> list[str]:
    """Construit une commande FFmpeg pour un seul segment.

    Args:
        input_path: Chemin du fichier source
        output_path: Chemin du fichier de sortie
        start_seconds: Début du segment en secondes
        end_seconds: Fin du segment en secondes

    Returns:
        Liste des arguments de commande
    """
    ffmpeg: Path = get_ffmpeg_path()
    duration: float = end_seconds - start_seconds

    return [
        str(ffmpeg),
        "-y",  # Écraser sans demander
        "-i", str(input_path),
        "-ss", str(start_seconds),
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", H264_PRESET,
        "-crf", H264_CRF,
        "-c:a", "aac",
        "-b:a", AAC_BITRATE,
        "-progress", "pipe:1",
        "-nostats",
        str(output_path)
    ]


def build_multi_segment_command(
    input_path: str | Path,
    output_path: str | Path,
    segments: list[tuple[float, float]]
) -> list[str]:
    """Construit une commande FFmpeg pour plusieurs segments avec concat.

    Utilise filter_complex avec trim/concat pour assembler plusieurs
    portions de la vidéo source en une seule sortie.

    Args:
        input_path: Chemin du fichier source
        output_path: Chemin du fichier de sortie
        segments: Liste de tuples (start_seconds, end_seconds)

    Returns:
        Liste des arguments de commande

    Raises:
        ValueError: Si la liste de segments est vide
    """
    if not segments:
        raise ValueError("La liste de segments ne peut pas être vide")

    # Pour un seul segment, utiliser la commande simple
    if len(segments) == 1:
        start, end = segments[0]
        return build_single_segment_command(input_path, output_path, start, end)

    ffmpeg: Path = get_ffmpeg_path()

    # Construire le filter_complex
    filter_parts: list[str] = []
    concat_inputs: list[str] = []

    for i, (start, end) in enumerate(segments):
        # Trim vidéo
        filter_parts.append(
            f"[0:v]trim={start}:{end},setpts=PTS-STARTPTS[v{i}]"
        )
        # Trim audio
        filter_parts.append(
            f"[0:a]atrim={start}:{end},asetpts=PTS-STARTPTS[a{i}]"
        )
        concat_inputs.append(f"[v{i}][a{i}]")

    # Concat tous les segments
    n_segments: int = len(segments)
    concat_inputs_str: str = "".join(concat_inputs)
    filter_parts.append(
        f"{concat_inputs_str}concat=n={n_segments}:v=1:a=1[outv][outa]"
    )

    filter_complex: str = ";".join(filter_parts)

    return [
        str(ffmpeg),
        "-y",  # Écraser sans demander
        "-i", str(input_path),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-preset", H264_PRESET,
        "-crf", H264_CRF,
        "-c:a", "aac",
        "-b:a", AAC_BITRATE,
        "-progress", "pipe:1",
        "-nostats",
        str(output_path)
    ]


def build_video_only_multi_segment_command(
    input_path: str | Path,
    output_path: str | Path,
    segments: list[tuple[float, float]]
) -> list[str]:
    """Construit une commande FFmpeg pour vidéos sans audio.

    Args:
        input_path: Chemin du fichier source
        output_path: Chemin du fichier de sortie
        segments: Liste de tuples (start_seconds, end_seconds)

    Returns:
        Liste des arguments de commande
    """
    if not segments:
        raise ValueError("La liste de segments ne peut pas être vide")

    if len(segments) == 1:
        start, end = segments[0]
        ffmpeg: Path = get_ffmpeg_path()
        duration: float = end - start
        return [
            str(ffmpeg),
            "-y",
            "-i", str(input_path),
            "-ss", str(start),
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", H264_PRESET,
            "-crf", H264_CRF,
            "-an",  # Pas d'audio
            "-progress", "pipe:1",
            "-nostats",
            str(output_path)
        ]

    ffmpeg = get_ffmpeg_path()

    # Filter complex pour vidéo seulement
    filter_parts: list[str] = []
    concat_inputs: list[str] = []

    for i, (start, end) in enumerate(segments):
        filter_parts.append(
            f"[0:v]trim={start}:{end},setpts=PTS-STARTPTS[v{i}]"
        )
        concat_inputs.append(f"[v{i}]")

    n_segments: int = len(segments)
    concat_inputs_str: str = "".join(concat_inputs)
    filter_parts.append(
        f"{concat_inputs_str}concat=n={n_segments}:v=1:a=0[outv]"
    )

    filter_complex: str = ";".join(filter_parts)

    return [
        str(ffmpeg),
        "-y",
        "-i", str(input_path),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264",
        "-preset", H264_PRESET,
        "-crf", H264_CRF,
        "-an",
        "-progress", "pipe:1",
        "-nostats",
        str(output_path)
    ]


def parse_progress_line(line: str) -> dict[str, str]:
    """Parse une ligne de sortie -progress de FFmpeg.

    Args:
        line: Ligne de sortie FFmpeg

    Returns:
        Dictionnaire clé=valeur ou vide si non parsable
    """
    line = line.strip()
    if "=" in line:
        key, _, value = line.partition("=")
        return {key: value}
    return {}


def parse_time_to_ms(time_str: str) -> int:
    """Convertit un timestamp FFmpeg en millisecondes.

    Args:
        time_str: Format "HH:MM:SS.microseconds" ou microsecondes

    Returns:
        Temps en millisecondes
    """
    try:
        # Format out_time_us (microsecondes)
        if time_str.isdigit() or (time_str.startswith("-") and time_str[1:].isdigit()):
            return int(time_str) // 1000

        # Format HH:MM:SS.microseconds
        if ":" in time_str:
            parts: list[str] = time_str.split(":")
            hours: int = int(parts[0])
            minutes: int = int(parts[1])
            seconds_parts: list[str] = parts[2].split(".")
            seconds: int = int(seconds_parts[0])
            microseconds: int = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0

            total_ms: int = (
                hours * 3600000 +
                minutes * 60000 +
                seconds * 1000 +
                microseconds // 1000
            )
            return total_ms
    except (ValueError, IndexError):
        pass

    return 0
