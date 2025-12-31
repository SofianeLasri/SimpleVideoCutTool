"""Panneau de contrôles de lecture et marqueurs.

Ce module fournit les contrôles pour:
- Lecture/Pause/Arrêt
- Navigation (début, fin, pas à pas)
- Placement des marqueurs A/B
- Sélection du mode (garder/couper)
- Contrôle du volume
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass


def _format_time(ms: int) -> str:
    """Formate des millisecondes en HH:MM:SS.

    Args:
        ms: Temps en millisecondes

    Returns:
        Chaîne formatée
    """
    if ms < 0:
        ms = 0
    total_seconds: int = ms // 1000
    hours: int = total_seconds // 3600
    minutes: int = (total_seconds % 3600) // 60
    seconds: int = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class ControlPanel(QWidget):
    """Panneau de contrôles de lecture et marqueurs."""

    # Signaux - Lecture
    play_clicked = Signal()
    """Émis quand le bouton lecture est cliqué."""

    pause_clicked = Signal()
    """Émis quand le bouton pause est cliqué."""

    stop_clicked = Signal()
    """Émis quand le bouton stop est cliqué."""

    go_to_start_clicked = Signal()
    """Émis pour aller au début."""

    go_to_end_clicked = Signal()
    """Émis pour aller à la fin."""

    step_forward_clicked = Signal()
    """Émis pour avancer d'un pas."""

    step_backward_clicked = Signal()
    """Émis pour reculer d'un pas."""

    # Signaux - Marqueurs
    set_marker_a_clicked = Signal()
    """Émis pour placer le marqueur A."""

    set_marker_b_clicked = Signal()
    """Émis pour placer le marqueur B."""

    clear_markers_clicked = Signal()
    """Émis pour effacer les marqueurs."""

    # Signaux - Mode
    mode_changed = Signal(bool)
    """Émis quand le mode change (True = garder)."""

    # Signaux - Volume
    volume_changed = Signal(float)
    """Émis quand le volume change (0.0 à 1.0)."""

    # Signaux - Undo/Redo
    undo_clicked = Signal()
    """Émis pour annuler."""

    redo_clicked = Signal()
    """Émis pour refaire."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise le panneau de contrôles.

        Args:
            parent: Widget parent
        """
        super().__init__(parent)
        self._is_playing: bool = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configure l'interface du panneau."""
        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(8)

        # Ligne 1: Contrôles de lecture + temps + volume
        playback_layout: QHBoxLayout = QHBoxLayout()
        playback_layout.setSpacing(5)

        # Boutons de navigation
        self._btn_go_start: QPushButton = QPushButton("|<")
        self._btn_go_start.setFixedWidth(35)
        self._btn_go_start.setToolTip("Aller au début")
        self._btn_go_start.clicked.connect(self.go_to_start_clicked)

        self._btn_step_back: QPushButton = QPushButton("<")
        self._btn_step_back.setFixedWidth(35)
        self._btn_step_back.setToolTip("Reculer de 1 seconde")
        self._btn_step_back.clicked.connect(self.step_backward_clicked)

        # Bouton Play/Pause
        self._btn_play_pause: QPushButton = QPushButton("Lecture")
        self._btn_play_pause.setFixedWidth(80)
        self._btn_play_pause.setToolTip("Lecture / Pause")
        self._btn_play_pause.clicked.connect(self._on_play_pause_clicked)

        self._btn_step_forward: QPushButton = QPushButton(">")
        self._btn_step_forward.setFixedWidth(35)
        self._btn_step_forward.setToolTip("Avancer de 1 seconde")
        self._btn_step_forward.clicked.connect(self.step_forward_clicked)

        self._btn_go_end: QPushButton = QPushButton(">|")
        self._btn_go_end.setFixedWidth(35)
        self._btn_go_end.setToolTip("Aller à la fin")
        self._btn_go_end.clicked.connect(self.go_to_end_clicked)

        # Label temps
        self._lbl_time: QLabel = QLabel("00:00:00 / 00:00:00")
        self._lbl_time.setMinimumWidth(140)
        self._lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Volume
        self._lbl_volume: QLabel = QLabel("Vol:")
        self._slider_volume: QSlider = QSlider(Qt.Orientation.Horizontal)
        self._slider_volume.setRange(0, 100)
        self._slider_volume.setValue(70)
        self._slider_volume.setFixedWidth(80)
        self._slider_volume.setToolTip("Volume")
        self._slider_volume.valueChanged.connect(self._on_volume_changed)

        playback_layout.addWidget(self._btn_go_start)
        playback_layout.addWidget(self._btn_step_back)
        playback_layout.addWidget(self._btn_play_pause)
        playback_layout.addWidget(self._btn_step_forward)
        playback_layout.addWidget(self._btn_go_end)
        playback_layout.addStretch()
        playback_layout.addWidget(self._lbl_time)
        playback_layout.addStretch()
        playback_layout.addWidget(self._lbl_volume)
        playback_layout.addWidget(self._slider_volume)

        main_layout.addLayout(playback_layout)

        # Ligne 2: Mode + Marqueurs + Undo/Redo
        markers_layout: QHBoxLayout = QHBoxLayout()
        markers_layout.setSpacing(10)

        # Mode de sélection
        mode_label: QLabel = QLabel("Mode:")
        self._radio_keep: QRadioButton = QRadioButton("Garder la sélection")
        self._radio_keep.setToolTip("Les régions marquées seront conservées")
        self._radio_keep.setChecked(True)

        self._radio_cut: QRadioButton = QRadioButton("Couper la sélection")
        self._radio_cut.setToolTip("Les régions marquées seront supprimées")

        self._mode_group: QButtonGroup = QButtonGroup(self)
        self._mode_group.addButton(self._radio_keep)
        self._mode_group.addButton(self._radio_cut)
        self._radio_keep.toggled.connect(self._on_mode_changed)

        # Boutons marqueurs
        self._btn_marker_a: QPushButton = QPushButton("Marquer A")
        self._btn_marker_a.setToolTip("Placer le marqueur de début (A)")
        self._btn_marker_a.clicked.connect(self.set_marker_a_clicked)

        self._btn_marker_b: QPushButton = QPushButton("Marquer B")
        self._btn_marker_b.setToolTip("Placer le marqueur de fin (B)")
        self._btn_marker_b.setEnabled(False)
        self._btn_marker_b.clicked.connect(self.set_marker_b_clicked)

        self._btn_clear: QPushButton = QPushButton("Effacer")
        self._btn_clear.setToolTip("Effacer tous les marqueurs")
        self._btn_clear.clicked.connect(self.clear_markers_clicked)

        # Undo/Redo
        self._btn_undo: QPushButton = QPushButton("Annuler")
        self._btn_undo.setToolTip("Annuler la dernière action")
        self._btn_undo.setEnabled(False)
        self._btn_undo.clicked.connect(self.undo_clicked)

        self._btn_redo: QPushButton = QPushButton("Refaire")
        self._btn_redo.setToolTip("Refaire l'action annulée")
        self._btn_redo.setEnabled(False)
        self._btn_redo.clicked.connect(self.redo_clicked)

        markers_layout.addWidget(mode_label)
        markers_layout.addWidget(self._radio_keep)
        markers_layout.addWidget(self._radio_cut)
        markers_layout.addStretch()
        markers_layout.addWidget(self._btn_marker_a)
        markers_layout.addWidget(self._btn_marker_b)
        markers_layout.addWidget(self._btn_clear)
        markers_layout.addStretch()
        markers_layout.addWidget(self._btn_undo)
        markers_layout.addWidget(self._btn_redo)

        main_layout.addLayout(markers_layout)

    @Slot()
    def _on_play_pause_clicked(self) -> None:
        """Gère le clic sur play/pause."""
        if self._is_playing:
            self.pause_clicked.emit()
        else:
            self.play_clicked.emit()

    @Slot(bool)
    def _on_mode_changed(self, checked: bool) -> None:
        """Gère le changement de mode."""
        if checked:  # radio_keep est coché
            self.mode_changed.emit(True)
        else:
            self.mode_changed.emit(False)

    @Slot(int)
    def _on_volume_changed(self, value: int) -> None:
        """Gère le changement de volume."""
        self.volume_changed.emit(value / 100.0)

    # Méthodes publiques pour mise à jour de l'UI
    def update_time_display(self, position_ms: int, duration_ms: int) -> None:
        """Met à jour l'affichage du temps.

        Args:
            position_ms: Position actuelle en ms
            duration_ms: Durée totale en ms
        """
        pos_str: str = _format_time(position_ms)
        dur_str: str = _format_time(duration_ms)
        self._lbl_time.setText(f"{pos_str} / {dur_str}")

    def update_playback_state(self, state: QMediaPlayer.PlaybackState) -> None:
        """Met à jour l'état du bouton play/pause.

        Args:
            state: État de lecture
        """
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._is_playing = True
            self._btn_play_pause.setText("Pause")
        else:
            self._is_playing = False
            self._btn_play_pause.setText("Lecture")

    def set_marker_a_pending(self, pending: bool) -> None:
        """Met à jour l'état du marqueur A.

        Args:
            pending: True si en attente du marqueur B
        """
        self._btn_marker_b.setEnabled(pending)
        if pending:
            self._btn_marker_a.setText("A placé")
            self._btn_marker_a.setStyleSheet("background-color: #4CAF50; color: white;")
        else:
            self._btn_marker_a.setText("Marquer A")
            self._btn_marker_a.setStyleSheet("")

    def set_undo_enabled(self, enabled: bool) -> None:
        """Active/désactive le bouton Annuler."""
        self._btn_undo.setEnabled(enabled)

    def set_redo_enabled(self, enabled: bool) -> None:
        """Active/désactive le bouton Refaire."""
        self._btn_redo.setEnabled(enabled)

    def set_controls_enabled(self, enabled: bool) -> None:
        """Active/désactive tous les contrôles.

        Args:
            enabled: True pour activer
        """
        self._btn_go_start.setEnabled(enabled)
        self._btn_step_back.setEnabled(enabled)
        self._btn_play_pause.setEnabled(enabled)
        self._btn_step_forward.setEnabled(enabled)
        self._btn_go_end.setEnabled(enabled)
        self._btn_marker_a.setEnabled(enabled)
        self._btn_clear.setEnabled(enabled)
        self._radio_keep.setEnabled(enabled)
        self._radio_cut.setEnabled(enabled)

    def is_keep_mode(self) -> bool:
        """Retourne True si le mode "garder" est sélectionné."""
        return self._radio_keep.isChecked()
