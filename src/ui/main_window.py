"""Fenêtre principale de l'application.

Ce module orchestre tous les composants UI:
- Lecteur vidéo
- Timeline
- Contrôles
- Panneau de logs
- Dialogues fichiers
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Slot
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from core.cut_manager import CutManager
from core.video_info import VideoInfo, VideoMetadata
from core.video_processor import VideoProcessor
from utils.ffmpeg_wrapper import is_av1_hardware_decode_available
from utils.logging_config import get_app_logger
from ui.control_panel import ControlPanel
from ui.dialogs import RegionEditDialog
from ui.log_viewer import LogViewerWidget
from ui.timeline_widget import TimelineWidget
from ui.video_player import VideoPlayerWidget
from ui.theme import ThemeManager

if TYPE_CHECKING:
    pass


class MainWindow(QMainWindow):
    """Fenêtre principale de Simple Video Cut Tool."""

    def __init__(self) -> None:
        """Initialise la fenêtre principale."""
        super().__init__()

        self._logger = get_app_logger()
        self._current_video_path: str | None = None
        self._current_output_path: str | None = None
        self._video_metadata: VideoMetadata | None = None

        self._setup_core_components()
        self._setup_ui()
        self._connect_signals()
        self._update_ui_state()

    def _setup_core_components(self) -> None:
        """Initialise les composants métier."""
        self._cut_manager: CutManager = CutManager(self)
        self._video_processor: VideoProcessor = VideoProcessor(self)

    def _setup_ui(self) -> None:
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Simple Video Cut Tool")
        self.setMinimumSize(900, 700)

        # Widget central
        central_widget: QWidget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout: QVBoxLayout = QVBoxLayout(central_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Barre d'outils
        toolbar_layout: QHBoxLayout = self._create_toolbar()
        main_layout.addLayout(toolbar_layout)

        # Lecteur vidéo
        self._video_player: VideoPlayerWidget = VideoPlayerWidget()
        main_layout.addWidget(self._video_player, stretch=1)

        # Timeline
        self._timeline: TimelineWidget = TimelineWidget()
        main_layout.addWidget(self._timeline)

        # Panneau de contrôles
        self._control_panel: ControlPanel = ControlPanel()
        main_layout.addWidget(self._control_panel)

        # Barre de progression
        self._progress_bar: QProgressBar = QProgressBar()
        self._progress_bar.setVisible(False)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("Encodage: %p%")
        main_layout.addWidget(self._progress_bar)

        # Panneau de logs
        self._log_viewer: LogViewerWidget = LogViewerWidget()
        main_layout.addWidget(self._log_viewer)

        # Barre de statut
        self._setup_status_bar()

    def _create_toolbar(self) -> QHBoxLayout:
        """Crée la barre d'outils."""
        layout: QHBoxLayout = QHBoxLayout()
        layout.setSpacing(10)

        # Bouton Ouvrir
        self._btn_open: QPushButton = QPushButton(" Ouvrir")
        self._btn_open.setMinimumWidth(100)
        self._btn_open.setToolTip("Ouvrir un fichier vidéo à éditer")
        self._btn_open.clicked.connect(self._open_video)

        # Bouton Destination
        self._btn_destination: QPushButton = QPushButton(" Destination")
        self._btn_destination.setMinimumWidth(110)
        self._btn_destination.setToolTip("Choisir le fichier de sortie")
        self._btn_destination.clicked.connect(self._set_output_destination)

        # Label destination
        self._lbl_destination: QLabel = QLabel("Aucune destination")
        self._lbl_destination.setProperty("secondary", True)

        # Bouton Exporter
        self._btn_export: QPushButton = QPushButton(" EXPORTER")
        self._btn_export.setMinimumWidth(120)
        self._btn_export.setProperty("accent", True)
        self._btn_export.setToolTip("Exporter la vidéo découpée")
        self._btn_export.clicked.connect(self._start_export)

        # Bouton Annuler encodage
        self._btn_cancel: QPushButton = QPushButton(" Annuler")
        self._btn_cancel.setVisible(False)
        self._btn_cancel.setProperty("danger", True)
        self._btn_cancel.clicked.connect(self._cancel_export)

        # Bouton toggle thème
        self._theme_manager = ThemeManager.instance()
        self._btn_theme: QPushButton = QPushButton()
        self._btn_theme.setFixedSize(40, 36)
        self._btn_theme.setToolTip("Basculer thème clair/sombre")
        self._btn_theme.clicked.connect(self._toggle_theme)
        self._update_theme_button()

        # Appliquer les icônes
        self._update_toolbar_icons()

        layout.addWidget(self._btn_open)
        layout.addWidget(self._btn_destination)
        layout.addWidget(self._lbl_destination, stretch=1)
        layout.addWidget(self._btn_export)
        layout.addWidget(self._btn_cancel)
        layout.addWidget(self._btn_theme)

        return layout

    def _update_theme_button(self) -> None:
        """Met à jour l'icône du bouton thème."""
        if self._theme_manager.is_dark:
            self._btn_theme.setIcon(self._theme_manager.get_icon("sun"))
        else:
            self._btn_theme.setIcon(self._theme_manager.get_icon("moon"))

    def _update_toolbar_icons(self) -> None:
        """Met à jour les icônes de la barre d'outils."""
        self._btn_open.setIcon(self._theme_manager.get_icon("open"))
        self._btn_destination.setIcon(self._theme_manager.get_icon("save"))
        self._btn_export.setIcon(self._theme_manager.get_icon("export"))
        self._btn_cancel.setIcon(self._theme_manager.get_icon("times"))
        self._update_theme_button()

    @Slot()
    def _toggle_theme(self) -> None:
        """Bascule entre thème clair et sombre."""
        self._theme_manager.toggle_theme()
        self._update_toolbar_icons()

    def _setup_status_bar(self) -> None:
        """Configure la barre de statut."""
        status_bar: QStatusBar = QStatusBar()
        self.setStatusBar(status_bar)

        self._status_label: QLabel = QLabel("Prêt")
        status_bar.addWidget(self._status_label, stretch=1)

        self._status_video_info: QLabel = QLabel("")
        status_bar.addPermanentWidget(self._status_video_info)

    def _connect_signals(self) -> None:
        """Connecte les signaux aux slots."""
        # Lecteur vidéo
        self._video_player.position_changed.connect(self._on_position_changed)
        self._video_player.duration_changed.connect(self._on_duration_changed)
        self._video_player.playback_state_changed.connect(self._on_playback_state_changed)
        self._video_player.media_loaded.connect(self._on_media_loaded)
        self._video_player.error_occurred.connect(self._on_player_error)

        # Contrôles de lecture
        self._control_panel.play_clicked.connect(self._video_player.play)
        self._control_panel.pause_clicked.connect(self._video_player.pause)
        self._control_panel.go_to_start_clicked.connect(self._video_player.go_to_start)
        self._control_panel.go_to_end_clicked.connect(self._video_player.go_to_end)
        self._control_panel.step_forward_clicked.connect(
            lambda: self._video_player.step_forward(1000)
        )
        self._control_panel.step_backward_clicked.connect(
            lambda: self._video_player.step_backward(1000)
        )
        self._control_panel.volume_changed.connect(self._video_player.set_volume)

        # Marqueurs
        self._control_panel.set_marker_a_clicked.connect(self._set_marker_a)
        self._control_panel.set_marker_b_clicked.connect(self._set_marker_b)
        self._control_panel.clear_markers_clicked.connect(self._clear_markers)
        self._control_panel.undo_clicked.connect(self._undo)
        self._control_panel.redo_clicked.connect(self._redo)

        # Cut manager
        self._cut_manager.regions_changed.connect(self._on_regions_changed)
        self._cut_manager.marker_a_set.connect(self._on_marker_a_set)
        self._cut_manager.marker_a_cleared.connect(self._on_marker_a_cleared)

        # Timeline
        self._timeline.seek_requested.connect(self._video_player.seek)
        self._timeline.region_edit_requested.connect(self._on_edit_region)
        self._timeline.region_delete_requested.connect(self._on_delete_region)

        # Processeur vidéo
        self._video_processor.encoding_started.connect(self._on_encoding_started)
        self._video_processor.encoding_finished.connect(self._on_encoding_finished)
        self._video_processor.progress_updated.connect(self._on_progress_updated)
        self._video_processor.log_message.connect(self._on_log_message)

    def _update_ui_state(self) -> None:
        """Met à jour l'état de l'interface."""
        has_video: bool = self._current_video_path is not None
        has_output: bool = self._current_output_path is not None
        has_regions: bool = self._cut_manager.region_count > 0
        is_encoding: bool = self._video_processor.is_encoding

        # Activer/désactiver les contrôles
        self._control_panel.set_controls_enabled(has_video and not is_encoding)
        self._btn_destination.setEnabled(has_video and not is_encoding)
        self._btn_open.setEnabled(not is_encoding)

        # Bouton export
        can_export: bool = has_video and has_output and has_regions and not is_encoding
        self._btn_export.setEnabled(can_export)

        # Undo/Redo
        self._control_panel.set_undo_enabled(self._cut_manager.can_undo())
        self._control_panel.set_redo_enabled(self._cut_manager.can_redo())

    # Slots - Fichiers
    @Slot()
    def _open_video(self) -> None:
        """Ouvre un fichier vidéo."""
        extensions: str = " ".join(f"*{ext}" for ext in VideoInfo.get_supported_extensions())
        file_filter: str = f"Vidéos ({extensions});;Tous les fichiers (*.*)"

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Ouvrir une vidéo",
            "",
            file_filter
        )

        if not file_path:
            return

        self._load_video(file_path)

    def _load_video(self, file_path: str) -> None:
        """Charge un fichier vidéo."""
        self._logger.info(f"Chargement: {file_path}")
        self._status_label.setText("Chargement de la vidéo...")

        try:
            # Extraire les métadonnées
            self._video_metadata = VideoInfo.probe(file_path)

            # Charger dans le lecteur
            if not self._video_player.load_video(file_path):
                raise RuntimeError("Échec du chargement dans le lecteur")

            self._current_video_path = file_path

            # Configurer le cut manager
            self._cut_manager.set_video_duration(self._video_metadata.duration_ms)

            # Proposer un fichier de sortie par défaut
            self._suggest_output_path(file_path)

            # Mettre à jour l'affichage
            self._status_video_info.setText(
                f"{self._video_metadata.resolution} | "
                f"{self._video_metadata.fps:.1f} fps | "
                f"{self._video_metadata.duration_formatted}"
            )
            self._status_label.setText("Vidéo chargée")
            self._logger.info(f"Vidéo chargée: {self._video_metadata}")

            # Avertissement pour AV1 si pas de décodage matériel
            if (self._video_metadata.video_codec.lower() == "av1"
                    and not is_av1_hardware_decode_available()):
                QMessageBox.warning(
                    self,
                    "Codec AV1 non supporté",
                    "Ce fichier utilise le codec AV1, mais votre matériel "
                    "ne supporte pas son décodage.\n\n"
                    "La prévisualisation risque de ne pas fonctionner.\n\n"
                    "L'export fonctionnera normalement (FFmpeg)."
                )

        except Exception as e:
            self._logger.error(f"Erreur chargement: {e}")
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible de charger la vidéo:\n{e}"
            )
            self._status_label.setText("Erreur de chargement")

        self._update_ui_state()

    def _suggest_output_path(self, input_path: str) -> None:
        """Suggère un chemin de sortie basé sur l'entrée."""
        path: Path = Path(input_path)
        output_name: str = f"{path.stem}_cut.mp4"
        output_path: Path = path.parent / output_name

        self._current_output_path = str(output_path)
        self._lbl_destination.setText(str(output_path))
        self._lbl_destination.setProperty("secondary", False)
        self._lbl_destination.setProperty("success", True)
        self._lbl_destination.style().unpolish(self._lbl_destination)
        self._lbl_destination.style().polish(self._lbl_destination)

    @Slot()
    def _set_output_destination(self) -> None:
        """Définit le fichier de sortie."""
        default_path: str = self._current_output_path or ""

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer sous",
            default_path,
            "Vidéo MP4 (*.mp4)"
        )

        if not file_path:
            return

        # Assurer l'extension .mp4
        if not file_path.lower().endswith(".mp4"):
            file_path += ".mp4"

        self._current_output_path = file_path
        self._lbl_destination.setText(file_path)
        self._lbl_destination.setProperty("secondary", False)
        self._lbl_destination.setProperty("success", True)
        self._lbl_destination.style().unpolish(self._lbl_destination)
        self._lbl_destination.style().polish(self._lbl_destination)
        self._update_ui_state()

    # Slots - Marqueurs
    @Slot()
    def _set_marker_a(self) -> None:
        """Place le marqueur A à la position actuelle."""
        position: int = self._video_player.position
        self._cut_manager.set_marker_a(position)

    @Slot()
    def _set_marker_b(self) -> None:
        """Place le marqueur B à la position actuelle."""
        position: int = self._video_player.position
        if self._cut_manager.set_marker_b(position):
            self._log_viewer.append_log(
                f"Région ajoutée: {self._format_time(self._cut_manager.regions[-1].start_ms)} - "
                f"{self._format_time(self._cut_manager.regions[-1].end_ms)}",
                "INFO"
            )

    @Slot()
    def _clear_markers(self) -> None:
        """Efface tous les marqueurs."""
        self._cut_manager.clear_all()

    @Slot()
    def _undo(self) -> None:
        """Annule la dernière action."""
        self._cut_manager.undo()

    @Slot()
    def _redo(self) -> None:
        """Refait l'action annulée."""
        self._cut_manager.redo()

    # Slots - Cut manager
    @Slot()
    def _on_regions_changed(self) -> None:
        """Gère le changement des régions."""
        self._timeline.set_regions(self._cut_manager.regions)
        self._update_ui_state()

    @Slot(int)
    def _on_marker_a_set(self, position_ms: int) -> None:
        """Gère le placement du marqueur A."""
        self._timeline.set_pending_marker_a(position_ms)
        self._control_panel.set_marker_a_pending(True)

    @Slot()
    def _on_marker_a_cleared(self) -> None:
        """Gère l'effacement du marqueur A."""
        self._timeline.set_pending_marker_a(None)
        self._control_panel.set_marker_a_pending(False)

    @Slot(int)
    def _on_edit_region(self, index: int) -> None:
        """Ouvre le dialogue d'édition pour une région."""
        region = self._cut_manager.get_region(index)
        if region is None:
            return

        dialog = RegionEditDialog(
            region,
            self._cut_manager.video_duration_ms,
            self
        )

        if dialog.exec():
            new_start, new_end = dialog.get_new_bounds()
            if self._cut_manager.edit_region(index, new_start, new_end):
                self._log_viewer.append_log(
                    f"Région modifiée: {self._format_time(new_start)} - {self._format_time(new_end)}",
                    "INFO"
                )

    @Slot(int)
    def _on_delete_region(self, index: int) -> None:
        """Supprime une région après confirmation."""
        region = self._cut_manager.get_region(index)
        if region is None:
            return

        reply = QMessageBox.question(
            self,
            "Supprimer la région",
            f"Voulez-vous supprimer cette région ?\n"
            f"{self._format_time(region.start_ms)} - {self._format_time(region.end_ms)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._cut_manager.remove_region(index)
            self._log_viewer.append_log("Région supprimée", "INFO")

    # Slots - Lecteur
    @Slot(int)
    def _on_position_changed(self, position_ms: int) -> None:
        """Gère le changement de position."""
        self._timeline.set_position(position_ms)
        self._control_panel.update_time_display(position_ms, self._video_player.duration)

    @Slot(int)
    def _on_duration_changed(self, duration_ms: int) -> None:
        """Gère le changement de durée."""
        self._timeline.set_duration(duration_ms)
        self._control_panel.update_time_display(0, duration_ms)

    @Slot(QMediaPlayer.PlaybackState)
    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        """Gère le changement d'état de lecture."""
        self._control_panel.update_playback_state(state)

    @Slot(bool)
    def _on_media_loaded(self, success: bool) -> None:
        """Gère la fin du chargement média."""
        if success:
            self._logger.debug("Média chargé avec succès")
        else:
            self._logger.error("Échec du chargement média")
            self._show_playback_error_warning()

    @Slot(str)
    def _on_player_error(self, message: str) -> None:
        """Gère les erreurs du lecteur."""
        self._logger.error(f"Erreur lecteur: {message}")
        self._log_viewer.append_log(message, "ERROR")

    def _show_playback_error_warning(self) -> None:
        """Affiche un avertissement si la lecture échoue."""
        codec = self._video_metadata.video_codec if self._video_metadata else None

        if codec and codec.lower() == "av1":
            QMessageBox.warning(
                self,
                "Codec AV1 non supporté",
                "La prévisualisation des vidéos AV1 n'est pas disponible "
                "sur ce système (décodage matériel requis).\n\n"
                "L'export fonctionnera normalement car il utilise FFmpeg.\n\n"
                "Pour prévisualiser, convertissez la vidéo en H.264."
            )
        else:
            QMessageBox.warning(
                self,
                "Erreur de lecture",
                "Impossible de lire cette vidéo pour la prévisualisation.\n\n"
                "L'export pourrait quand même fonctionner."
            )

    # Slots - Export
    @Slot()
    def _start_export(self) -> None:
        """Démarre l'exportation."""
        if not self._current_video_path or not self._current_output_path:
            return

        # Vérifier si le fichier existe
        if Path(self._current_output_path).exists():
            reply: QMessageBox.StandardButton = QMessageBox.question(
                self,
                "Fichier existant",
                f"Le fichier existe déjà:\n{self._current_output_path}\n\nVoulez-vous le remplacer?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Obtenir les segments
        keep_mode: bool = self._control_panel.is_keep_mode()
        segments: list[tuple[float, float]] = self._cut_manager.get_final_segments(keep_mode)

        if not segments:
            QMessageBox.warning(
                self,
                "Attention",
                "Aucun segment à exporter. Placez des marqueurs A-B d'abord."
            )
            return

        # Lancer l'encodage
        has_audio: bool = self._video_metadata.has_audio if self._video_metadata else True
        video_width: int = self._video_metadata.width if self._video_metadata else 1920
        video_height: int = self._video_metadata.height if self._video_metadata else 1080

        # Paramètres de séparateur
        sep_enabled, sep_duration, sep_color = self._control_panel.get_separator_settings()

        self._logger.info(f"Démarrage export: {len(segments)} segment(s)")
        if sep_enabled and len(segments) > 1:
            self._logger.info(f"Séparateurs: {sep_duration}s, {sep_color}")
        self._log_viewer.clear()
        self._log_viewer.set_expanded(True)

        self._video_processor.encode(
            self._current_video_path,
            self._current_output_path,
            segments,
            has_audio,
            separator_enabled=sep_enabled,
            separator_duration=sep_duration,
            separator_color=sep_color,
            video_width=video_width,
            video_height=video_height
        )

    @Slot()
    def _cancel_export(self) -> None:
        """Annule l'exportation en cours."""
        self._video_processor.cancel()

    @Slot()
    def _on_encoding_started(self) -> None:
        """Gère le démarrage de l'encodage."""
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self._btn_cancel.setVisible(True)
        self._btn_export.setVisible(False)
        self._status_label.setText("Encodage en cours...")
        self._update_ui_state()

    @Slot(bool, str)
    def _on_encoding_finished(self, success: bool, message: str) -> None:
        """Gère la fin de l'encodage."""
        self._progress_bar.setVisible(False)
        self._btn_cancel.setVisible(False)
        self._btn_export.setVisible(True)
        self._update_ui_state()

        if success:
            self._status_label.setText("Exportation terminée!")
            self._log_viewer.append_log(message, "INFO")

            # Afficher le chemin du log
            log_path = self._video_processor.log_file_path
            if log_path:
                self._log_viewer.append_log(f"Log sauvegardé: {log_path}", "INFO")

            QMessageBox.information(
                self,
                "Succès",
                f"Vidéo exportée avec succès!\n\n{self._current_output_path}"
            )
        else:
            self._status_label.setText("Échec de l'exportation")
            self._log_viewer.append_log(message, "ERROR")
            QMessageBox.warning(
                self,
                "Erreur",
                f"L'exportation a échoué:\n{message}"
            )

    @Slot(int)
    def _on_progress_updated(self, value: int) -> None:
        """Met à jour la progression."""
        self._progress_bar.setValue(value)

    @Slot(str, str)
    def _on_log_message(self, message: str, level: str) -> None:
        """Ajoute un message au panneau de logs."""
        self._log_viewer.append_log(message, level)

    # Utilitaires
    @staticmethod
    def _format_time(ms: int) -> str:
        """Formate des millisecondes en HH:MM:SS."""
        total_seconds: int = ms // 1000
        hours: int = total_seconds // 3600
        minutes: int = (total_seconds % 3600) // 60
        seconds: int = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def closeEvent(self, event: object) -> None:
        """Gère la fermeture de la fenêtre."""
        if self._video_processor.is_encoding:
            reply: QMessageBox.StandardButton = QMessageBox.question(
                self,
                "Encodage en cours",
                "Un encodage est en cours. Voulez-vous vraiment quitter?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()  # type: ignore[union-attr]
                return

            self._video_processor.cancel()

        self._video_player.unload()
        event.accept()  # type: ignore[union-attr]
