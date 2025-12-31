"""Processeur d'encodage vidéo FFmpeg.

Ce module gère:
- L'encodage en arrière-plan via QThread
- Le parsing de la progression FFmpeg
- Les signaux pour l'UI (progression, logs, fin)
- L'annulation de l'encodage
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QThread, Signal

from utils.ffmpeg_wrapper import (
    build_multi_segment_command,
    build_multi_segment_with_separators_command,
    build_video_only_multi_segment_command,
    calculate_total_duration_with_separators,
    get_encoder_name,
    parse_progress_line,
    parse_time_to_ms,
)
from utils.logging_config import create_encoding_session_logger, get_app_logger

if TYPE_CHECKING:
    from core.video_info import VideoMetadata


class EncodingWorker(QThread):
    """Thread de travail pour l'encodage FFmpeg."""

    # Signaux
    progress = Signal(int)
    """Progression 0-100."""

    log_message = Signal(str, str)
    """Message de log (message, level)."""

    finished_encoding = Signal(bool, str)
    """Fin d'encodage (success, message)."""

    def __init__(
        self,
        command: list[str],
        total_duration_ms: int,
        session_logger: logging.Logger,
        parent: QObject | None = None
    ) -> None:
        """Initialise le worker d'encodage.

        Args:
            command: Commande FFmpeg à exécuter
            total_duration_ms: Durée totale attendue en sortie (ms)
            session_logger: Logger pour cette session
            parent: Parent Qt
        """
        super().__init__(parent)
        self._command: list[str] = command
        self._total_duration_ms: int = total_duration_ms
        self._session_logger: logging.Logger = session_logger
        self._cancelled: bool = False
        self._process: subprocess.Popen[str] | None = None

    def run(self) -> None:
        """Exécute l'encodage FFmpeg."""
        self._session_logger.info(f"Commande: {' '.join(self._command)}")
        self.log_message.emit("Démarrage de l'encodage...", "INFO")

        try:
            # Lancer le processus FFmpeg
            self._process = subprocess.Popen(
                self._command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
                encoding="utf-8",
                errors="replace"
            )

            current_time_ms: int = 0
            progress_data: dict[str, str] = {}

            # Lire la sortie ligne par ligne
            if self._process.stdout:
                for line in self._process.stdout:
                    line = line.strip()

                    if self._cancelled:
                        self._terminate_process()
                        self._session_logger.warning("Encodage annulé par l'utilisateur")
                        self.finished_encoding.emit(False, "Encodage annulé")
                        return

                    # Parser les lignes de progression
                    parsed: dict[str, str] = parse_progress_line(line)
                    progress_data.update(parsed)

                    # Extraire le temps actuel
                    if "out_time_us" in parsed:
                        try:
                            time_us: int = int(parsed["out_time_us"])
                            current_time_ms = time_us // 1000
                        except ValueError:
                            pass
                    elif "out_time" in parsed:
                        current_time_ms = parse_time_to_ms(parsed["out_time"])

                    # Calculer et émettre la progression
                    if self._total_duration_ms > 0 and current_time_ms > 0:
                        progress_pct: int = min(
                            100,
                            int((current_time_ms / self._total_duration_ms) * 100)
                        )
                        self.progress.emit(progress_pct)

                    # Logger et afficher les lignes non-progression (logs FFmpeg)
                    if line and "=" not in line:
                        self._session_logger.debug(line)
                        self.log_message.emit(line, "DEBUG")

                    # Détecter la fin d'un bloc progress
                    if "progress=" in line:
                        progress_data.clear()

            # Attendre la fin du processus
            self._process.wait()

            if self._cancelled:
                self.finished_encoding.emit(False, "Encodage annulé")
                return

            # Vérifier le code de retour
            if self._process.returncode == 0:
                self._session_logger.info("Encodage terminé avec succès")
                self.log_message.emit("Encodage terminé avec succès!", "INFO")
                self.progress.emit(100)
                self.finished_encoding.emit(True, "Encodage terminé avec succès")
            else:
                error_msg: str = f"FFmpeg a échoué (code {self._process.returncode})"
                self._session_logger.error(error_msg)
                self.log_message.emit(error_msg, "ERROR")
                self.finished_encoding.emit(False, error_msg)

        except FileNotFoundError as e:
            error_msg = f"FFmpeg non trouvé: {e}"
            self._session_logger.error(error_msg)
            self.log_message.emit(error_msg, "ERROR")
            self.finished_encoding.emit(False, error_msg)

        except Exception as e:
            error_msg = f"Erreur inattendue: {e}"
            self._session_logger.exception(error_msg)
            self.log_message.emit(error_msg, "ERROR")
            self.finished_encoding.emit(False, error_msg)

    def cancel(self) -> None:
        """Demande l'annulation de l'encodage."""
        self._cancelled = True
        self._terminate_process()

    def _terminate_process(self) -> None:
        """Termine le processus FFmpeg."""
        if self._process is not None:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            except Exception:
                pass


class VideoProcessor(QObject):
    """Gestionnaire principal d'encodage vidéo.

    Coordonne l'encodage FFmpeg avec l'interface utilisateur.
    """

    # Signaux
    progress_updated = Signal(int)
    """Progression 0-100."""

    encoding_started = Signal()
    """Émis au démarrage de l'encodage."""

    encoding_finished = Signal(bool, str)
    """Émis à la fin (success, message)."""

    log_message = Signal(str, str)
    """Message de log pour l'UI (message, level)."""

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialise le processeur vidéo.

        Args:
            parent: Parent Qt
        """
        super().__init__(parent)
        self._worker: EncodingWorker | None = None
        self._session_logger: logging.Logger | None = None
        self._log_file_path: Path | None = None
        self._is_encoding: bool = False

    @property
    def is_encoding(self) -> bool:
        """True si un encodage est en cours."""
        return self._is_encoding

    @property
    def log_file_path(self) -> Path | None:
        """Chemin du fichier log de la session courante."""
        return self._log_file_path

    def encode(
        self,
        input_path: str | Path,
        output_path: str | Path,
        segments: list[tuple[float, float]],
        has_audio: bool = True,
        separator_enabled: bool = False,
        separator_duration: float = 2.0,
        separator_color: str = "black",
        video_width: int = 1920,
        video_height: int = 1080
    ) -> bool:
        """Lance l'encodage d'une vidéo.

        Args:
            input_path: Chemin du fichier source
            output_path: Chemin du fichier de sortie
            segments: Liste de tuples (start_sec, end_sec) à garder
            has_audio: True si la vidéo a une piste audio
            separator_enabled: True pour ajouter des écrans de séparation
            separator_duration: Durée des séparateurs en secondes
            separator_color: Couleur des séparateurs ("black" ou "white")
            video_width: Largeur de la vidéo source
            video_height: Hauteur de la vidéo source

        Returns:
            True si l'encodage a démarré
        """
        if self._is_encoding:
            get_app_logger().warning("Encodage déjà en cours")
            return False

        if not segments:
            self.log_message.emit("Aucun segment à encoder", "ERROR")
            return False

        # Créer le logger de session
        video_name: str = Path(input_path).stem
        self._session_logger, self._log_file_path = create_encoding_session_logger(video_name)

        # Afficher l'encodeur utilisé
        encoder_name = get_encoder_name()
        encoder_display = {
            "h264_nvenc": "NVIDIA NVENC (GPU)",
            "h264_qsv": "Intel Quick Sync (GPU)",
            "h264_amf": "AMD AMF (GPU)",
            "libx264": "libx264 (CPU)"
        }.get(encoder_name, encoder_name)
        self.log_message.emit(f"Encodeur: {encoder_display}", "INFO")
        self._session_logger.info(f"Encodeur: {encoder_display}")

        self._session_logger.info(f"Source: {input_path}")
        self._session_logger.info(f"Destination: {output_path}")
        self._session_logger.info(f"Segments: {segments}")
        self._session_logger.info(f"Audio: {'Oui' if has_audio else 'Non'}")
        if separator_enabled:
            self._session_logger.info(
                f"Séparateurs: {separator_duration}s, couleur={separator_color}"
            )

        # Construire la commande FFmpeg
        try:
            # Utiliser séparateurs seulement si activés ET plusieurs segments
            use_separators: bool = separator_enabled and len(segments) > 1

            if use_separators:
                command: list[str] = build_multi_segment_with_separators_command(
                    input_path=input_path,
                    output_path=output_path,
                    segments=segments,
                    separator_duration=separator_duration,
                    separator_color=separator_color,
                    has_audio=has_audio,
                    video_width=video_width,
                    video_height=video_height
                )
            elif has_audio:
                command = build_multi_segment_command(
                    input_path, output_path, segments
                )
            else:
                command = build_video_only_multi_segment_command(
                    input_path, output_path, segments
                )
        except Exception as e:
            error_msg: str = f"Erreur construction commande: {e}"
            self._session_logger.error(error_msg)
            self.log_message.emit(error_msg, "ERROR")
            return False

        # Calculer la durée totale de sortie
        if use_separators:
            total_duration_ms = int(
                calculate_total_duration_with_separators(segments, separator_duration) * 1000
            )
        else:
            total_duration_ms = int(
                sum((end - start) * 1000 for start, end in segments)
            )

        # Créer et démarrer le worker
        self._worker = EncodingWorker(
            command=command,
            total_duration_ms=total_duration_ms,
            session_logger=self._session_logger,
            parent=self
        )

        # Connecter les signaux
        self._worker.progress.connect(self._on_progress)
        self._worker.log_message.connect(self._on_log_message)
        self._worker.finished_encoding.connect(self._on_finished)
        self._worker.finished.connect(self._on_thread_finished)

        self._is_encoding = True
        self.encoding_started.emit()
        self._worker.start()

        return True

    def cancel(self) -> None:
        """Annule l'encodage en cours."""
        if self._worker is not None and self._is_encoding:
            self.log_message.emit("Annulation en cours...", "WARNING")
            self._worker.cancel()

    def _on_progress(self, value: int) -> None:
        """Gère les mises à jour de progression.

        Args:
            value: Progression 0-100
        """
        self.progress_updated.emit(value)

    def _on_log_message(self, message: str, level: str) -> None:
        """Gère les messages de log.

        Args:
            message: Message à logger
            level: Niveau (INFO, WARNING, ERROR)
        """
        self.log_message.emit(message, level)

    def _on_finished(self, success: bool, message: str) -> None:
        """Gère la fin de l'encodage.

        Args:
            success: True si succès
            message: Message de fin
        """
        if self._session_logger:
            self._session_logger.info(f"=== Fin de session: {message} ===")

        # Libérer le flag AVANT d'émettre le signal pour que l'UI se mette à jour correctement
        self._is_encoding = False
        self.encoding_finished.emit(success, message)

    def _on_thread_finished(self) -> None:
        """Gère la fin du thread."""
        self._worker = None  # Nettoyer la référence au worker
