"""Wrapper pour les commandes FFmpeg.

Ce module construit les commandes FFmpeg pour:
- L'encodage H264 + AAC (avec support encodeurs matériels)
- La découpe multi-segments
- Le tracking de progression
"""

from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Final

from utils.paths import get_ffmpeg_path, get_ffprobe_path


# Paramètres d'encodage H264
H264_CRF: Final[str] = "18"

# Paramètres audio AAC
AAC_BITRATE: Final[str] = "192k"


@lru_cache(maxsize=1)
def detect_available_encoder() -> tuple[str, str]:
    """Détecte le meilleur encodeur H264 disponible.

    Teste les encodeurs matériels dans l'ordre de préférence:
    NVENC (NVIDIA) > Quick Sync (Intel) > AMF (AMD) > libx264 (CPU)

    Returns:
        Tuple (encoder_name, preset) pour FFmpeg
    """
    ffmpeg = get_ffmpeg_path()

    # Liste des encodeurs matériels avec leur preset qualité max
    encoders = [
        ("h264_nvenc", "p7"),      # NVIDIA - p7 = slowest/best quality
        ("h264_qsv", "veryslow"),  # Intel Quick Sync
        ("h264_amf", "quality"),   # AMD AMF
    ]

    for encoder, preset in encoders:
        try:
            # Vérifier si l'encodeur est listé
            result = subprocess.run(
                [str(ffmpeg), "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if encoder not in result.stdout:
                continue

            # Vérifier si l'encodeur fonctionne vraiment (test d'encodage)
            test = subprocess.run(
                [
                    str(ffmpeg), "-hide_banner",
                    "-f", "lavfi", "-i", "nullsrc=s=256x256:d=0.1",
                    "-c:v", encoder, "-f", "null", "-"
                ],
                capture_output=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if test.returncode == 0:
                return (encoder, preset)

        except (subprocess.TimeoutExpired, Exception):
            continue

    # Fallback: encodage logiciel avec preset medium
    return ("libx264", "medium")


def get_video_codec_args() -> list[str]:
    """Retourne les arguments de codec vidéo pour FFmpeg.

    Utilise l'encodeur matériel si disponible, sinon libx264.

    Returns:
        Liste d'arguments FFmpeg pour le codec vidéo
    """
    encoder, preset = detect_available_encoder()

    if encoder == "libx264":
        return ["-c:v", "libx264", "-preset", preset, "-crf", H264_CRF]
    elif encoder == "h264_nvenc":
        # NVENC: utiliser CQ (Constant Quality) au lieu de CRF
        return ["-c:v", "h264_nvenc", "-preset", preset, "-cq", H264_CRF, "-rc", "vbr"]
    elif encoder == "h264_qsv":
        return ["-c:v", "h264_qsv", "-preset", preset, "-global_quality", H264_CRF]
    elif encoder == "h264_amf":
        return ["-c:v", "h264_amf", "-quality", preset, "-rc", "cqp", "-qp_i", H264_CRF, "-qp_p", H264_CRF]

    # Fallback par défaut
    return ["-c:v", "libx264", "-preset", "medium", "-crf", H264_CRF]


def get_encoder_name() -> str:
    """Retourne le nom de l'encodeur actuellement utilisé.

    Returns:
        Nom de l'encodeur (ex: "h264_nvenc", "libx264")
    """
    encoder, _ = detect_available_encoder()
    return encoder


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
        *get_video_codec_args(),
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
        *get_video_codec_args(),
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
            *get_video_codec_args(),
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
        *get_video_codec_args(),
        "-an",
        "-progress", "pipe:1",
        "-nostats",
        str(output_path)
    ]


def build_multi_segment_with_separators_command(
    input_path: str | Path,
    output_path: str | Path,
    segments: list[tuple[float, float]],
    separator_duration: float = 2.0,
    separator_color: str = "black",
    has_audio: bool = True,
    video_width: int = 1920,
    video_height: int = 1080
) -> list[str]:
    """Construit une commande FFmpeg avec écrans de séparation entre segments.

    Args:
        input_path: Chemin du fichier source
        output_path: Chemin du fichier de sortie
        segments: Liste de tuples (start_seconds, end_seconds)
        separator_duration: Durée des séparateurs en secondes
        separator_color: Couleur des séparateurs ("black" ou "white")
        has_audio: True si la vidéo a de l'audio
        video_width: Largeur de la vidéo source
        video_height: Hauteur de la vidéo source

    Returns:
        Liste des arguments de commande
    """
    if not segments:
        raise ValueError("La liste de segments ne peut pas être vide")

    # Pour un seul segment, pas de séparateur nécessaire
    if len(segments) == 1:
        start, end = segments[0]
        if has_audio:
            return build_single_segment_command(input_path, output_path, start, end)
        else:
            return build_video_only_multi_segment_command(input_path, output_path, segments)

    ffmpeg: Path = get_ffmpeg_path()

    # Construire le filter_complex avec séparateurs
    filter_parts: list[str] = []
    concat_inputs: list[str] = []

    for i, (start, end) in enumerate(segments):
        # Trim vidéo du segment
        filter_parts.append(
            f"[0:v]trim={start}:{end},setpts=PTS-STARTPTS[v{i}]"
        )

        if has_audio:
            # Trim audio du segment
            filter_parts.append(
                f"[0:a]atrim={start}:{end},asetpts=PTS-STARTPTS[a{i}]"
            )
            concat_inputs.append(f"[v{i}][a{i}]")
        else:
            concat_inputs.append(f"[v{i}]")

        # Ajouter séparateur après chaque segment sauf le dernier
        if i < len(segments) - 1:
            sep_idx = f"sep{i}"

            # Générer un écran de couleur unie
            filter_parts.append(
                f"color=c={separator_color}:s={video_width}x{video_height}:"
                f"d={separator_duration},format=yuv420p[{sep_idx}v]"
            )

            if has_audio:
                # Générer du silence pour le séparateur
                filter_parts.append(
                    f"aevalsrc=0:d={separator_duration}:s=48000[{sep_idx}a]"
                )
                concat_inputs.append(f"[{sep_idx}v][{sep_idx}a]")
            else:
                concat_inputs.append(f"[{sep_idx}v]")

    # Nombre total d'éléments: segments + séparateurs
    n_elements = len(segments) + (len(segments) - 1)

    # Concat tous les éléments
    concat_inputs_str = "".join(concat_inputs)

    if has_audio:
        filter_parts.append(
            f"{concat_inputs_str}concat=n={n_elements}:v=1:a=1[outv][outa]"
        )
    else:
        filter_parts.append(
            f"{concat_inputs_str}concat=n={n_elements}:v=1:a=0[outv]"
        )

    filter_complex = ";".join(filter_parts)

    cmd = [
        str(ffmpeg),
        "-y",
        "-i", str(input_path),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
    ]

    if has_audio:
        cmd.extend(["-map", "[outa]"])

    cmd.extend(get_video_codec_args())

    if has_audio:
        cmd.extend(["-c:a", "aac", "-b:a", AAC_BITRATE])
    else:
        cmd.append("-an")

    cmd.extend([
        "-progress", "pipe:1",
        "-nostats",
        str(output_path)
    ])

    return cmd


def calculate_total_duration_with_separators(
    segments: list[tuple[float, float]],
    separator_duration: float
) -> float:
    """Calcule la durée totale incluant les séparateurs.

    Args:
        segments: Liste de tuples (start_seconds, end_seconds)
        separator_duration: Durée de chaque séparateur en secondes

    Returns:
        Durée totale en secondes
    """
    if not segments:
        return 0.0

    segment_duration = sum(end - start for start, end in segments)
    separator_count = max(0, len(segments) - 1)
    return segment_duration + (separator_count * separator_duration)


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
