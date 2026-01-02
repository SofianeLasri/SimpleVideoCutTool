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
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ui.theme import ThemeManager

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

    step_backward_5_clicked = Signal()
    """Émis pour reculer de 5 secondes."""

    step_forward_5_clicked = Signal()
    """Émis pour avancer de 5 secondes."""

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

    # Signaux - Séparateurs
    separator_settings_changed = Signal(bool, float, str)
    """Émis quand les paramètres de séparateur changent (enabled, duration, color)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise le panneau de contrôles.

        Args:
            parent: Widget parent
        """
        super().__init__(parent)
        self._is_playing: bool = False
        self._theme = ThemeManager.instance()
        self._setup_ui()
        self._update_icons()

        # Mettre à jour les icônes au changement de thème
        self._theme.theme_changed.connect(self._update_icons)

    def _setup_ui(self) -> None:
        """Configure l'interface du panneau."""
        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(8)

        # Ligne 1: Contrôles de lecture + temps + volume
        playback_layout: QHBoxLayout = QHBoxLayout()
        playback_layout.setSpacing(5)

        # Boutons de navigation
        self._btn_step_back_5: QPushButton = QPushButton()
        self._btn_step_back_5.setFixedSize(36, 36)
        self._btn_step_back_5.setToolTip("Reculer de 5 secondes")
        self._btn_step_back_5.clicked.connect(self.step_backward_5_clicked)

        self._btn_step_back: QPushButton = QPushButton()
        self._btn_step_back.setFixedSize(36, 36)
        self._btn_step_back.setToolTip("Reculer de 1 seconde")
        self._btn_step_back.clicked.connect(self.step_backward_clicked)

        # Bouton Play/Pause
        self._btn_play_pause: QPushButton = QPushButton()
        self._btn_play_pause.setFixedSize(48, 36)
        self._btn_play_pause.setToolTip("Lecture / Pause")
        self._btn_play_pause.clicked.connect(self._on_play_pause_clicked)

        self._btn_step_forward: QPushButton = QPushButton()
        self._btn_step_forward.setFixedSize(36, 36)
        self._btn_step_forward.setToolTip("Avancer de 1 seconde")
        self._btn_step_forward.clicked.connect(self.step_forward_clicked)

        self._btn_step_forward_5: QPushButton = QPushButton()
        self._btn_step_forward_5.setFixedSize(36, 36)
        self._btn_step_forward_5.setToolTip("Avancer de 5 secondes")
        self._btn_step_forward_5.clicked.connect(self.step_forward_5_clicked)

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

        playback_layout.addWidget(self._btn_step_back_5)
        playback_layout.addWidget(self._btn_step_back)
        playback_layout.addWidget(self._btn_play_pause)
        playback_layout.addWidget(self._btn_step_forward)
        playback_layout.addWidget(self._btn_step_forward_5)
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
        self._btn_marker_a: QPushButton = QPushButton(" A")
        self._btn_marker_a.setToolTip("Placer le marqueur de début (A)")
        self._btn_marker_a.clicked.connect(self.set_marker_a_clicked)

        self._btn_marker_b: QPushButton = QPushButton(" B")
        self._btn_marker_b.setToolTip("Placer le marqueur de fin (B)")
        self._btn_marker_b.setEnabled(False)
        self._btn_marker_b.clicked.connect(self.set_marker_b_clicked)

        self._btn_clear: QPushButton = QPushButton()
        self._btn_clear.setFixedSize(36, 36)
        self._btn_clear.setToolTip("Effacer tous les marqueurs")
        self._btn_clear.clicked.connect(self.clear_markers_clicked)

        # Undo/Redo
        self._btn_undo: QPushButton = QPushButton()
        self._btn_undo.setFixedSize(36, 36)
        self._btn_undo.setToolTip("Annuler la dernière action (Ctrl+Z)")
        self._btn_undo.setEnabled(False)
        self._btn_undo.clicked.connect(self.undo_clicked)

        self._btn_redo: QPushButton = QPushButton()
        self._btn_redo.setFixedSize(36, 36)
        self._btn_redo.setToolTip("Refaire l'action annulée (Ctrl+Y)")
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

        # Ligne 3: Paramètres de séparateur
        separator_layout: QHBoxLayout = QHBoxLayout()
        separator_layout.setSpacing(10)

        separator_label: QLabel = QLabel("Séparateurs entre segments:")
        self._chk_separator: QCheckBox = QCheckBox("Activer")
        self._chk_separator.setToolTip(
            "Ajouter un écran de séparation entre les segments coupés"
        )
        self._chk_separator.stateChanged.connect(self._on_separator_settings_changed)

        duration_label: QLabel = QLabel("Durée:")
        self._spin_separator_duration: QDoubleSpinBox = QDoubleSpinBox()
        self._spin_separator_duration.setRange(0.5, 10.0)
        self._spin_separator_duration.setValue(2.0)
        self._spin_separator_duration.setSingleStep(0.5)
        self._spin_separator_duration.setSuffix(" s")
        self._spin_separator_duration.setToolTip("Durée du séparateur en secondes")
        self._spin_separator_duration.setEnabled(False)
        self._spin_separator_duration.valueChanged.connect(
            self._on_separator_settings_changed
        )

        color_label: QLabel = QLabel("Couleur:")
        self._combo_separator_color: QComboBox = QComboBox()
        self._combo_separator_color.addItems(["Noir", "Blanc"])
        self._combo_separator_color.setToolTip("Couleur de l'écran de séparation")
        self._combo_separator_color.setEnabled(False)
        self._combo_separator_color.setFixedWidth(80)
        self._combo_separator_color.currentIndexChanged.connect(
            self._on_separator_settings_changed
        )

        separator_layout.addWidget(separator_label)
        separator_layout.addWidget(self._chk_separator)
        separator_layout.addSpacing(20)
        separator_layout.addWidget(duration_label)
        separator_layout.addWidget(self._spin_separator_duration)
        separator_layout.addSpacing(10)
        separator_layout.addWidget(color_label)
        separator_layout.addWidget(self._combo_separator_color)
        separator_layout.addStretch()

        main_layout.addLayout(separator_layout)

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
            self._btn_play_pause.setIcon(self._theme.get_icon("pause"))
        else:
            self._is_playing = False
            self._btn_play_pause.setIcon(self._theme.get_icon("play"))

    def set_marker_a_pending(self, pending: bool) -> None:
        """Met à jour l'état du marqueur A.

        Args:
            pending: True si en attente du marqueur B
        """
        self._btn_marker_b.setEnabled(pending)
        if pending:
            self._btn_marker_a.setText(" A OK")
            self._btn_marker_a.setProperty("success", True)
            # Icône verte pour indiquer le succès
            self._btn_marker_a.setIcon(
                self._theme._icon_provider.get_success_icon("check")
            )
        else:
            self._btn_marker_a.setText(" A")
            self._btn_marker_a.setProperty("success", False)
            self._btn_marker_a.setIcon(self._theme.get_icon("marker_a"))
        # Forcer le rafraîchissement du style
        self._btn_marker_a.style().unpolish(self._btn_marker_a)
        self._btn_marker_a.style().polish(self._btn_marker_a)

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
        self._btn_step_back_5.setEnabled(enabled)
        self._btn_step_back.setEnabled(enabled)
        self._btn_play_pause.setEnabled(enabled)
        self._btn_step_forward.setEnabled(enabled)
        self._btn_step_forward_5.setEnabled(enabled)
        self._btn_marker_a.setEnabled(enabled)
        self._btn_clear.setEnabled(enabled)
        self._radio_keep.setEnabled(enabled)
        self._radio_cut.setEnabled(enabled)

    def is_keep_mode(self) -> bool:
        """Retourne True si le mode "garder" est sélectionné."""
        return self._radio_keep.isChecked()

    @Slot()
    def _on_separator_settings_changed(self) -> None:
        """Gère le changement des paramètres de séparateur."""
        enabled: bool = self._chk_separator.isChecked()
        self._spin_separator_duration.setEnabled(enabled)
        self._combo_separator_color.setEnabled(enabled)

        duration: float = self._spin_separator_duration.value()
        color: str = "black" if self._combo_separator_color.currentIndex() == 0 else "white"

        self.separator_settings_changed.emit(enabled, duration, color)

    def get_separator_settings(self) -> tuple[bool, float, str]:
        """Retourne les paramètres de séparateur.

        Returns:
            Tuple (enabled, duration_seconds, color)
            color est "black" ou "white"
        """
        enabled: bool = self._chk_separator.isChecked()
        duration: float = self._spin_separator_duration.value()
        color: str = "black" if self._combo_separator_color.currentIndex() == 0 else "white"
        return (enabled, duration, color)

    @Slot()
    def _update_icons(self) -> None:
        """Met à jour les icônes selon le thème actuel."""
        # Boutons de lecture
        self._btn_step_back_5.setIcon(self._theme.get_icon("backward"))
        self._btn_step_back.setIcon(self._theme.get_icon("step_backward"))
        self._btn_step_forward.setIcon(self._theme.get_icon("step_forward"))
        self._btn_step_forward_5.setIcon(self._theme.get_icon("forward"))

        # Play/Pause selon état
        if self._is_playing:
            self._btn_play_pause.setIcon(self._theme.get_icon("pause"))
        else:
            self._btn_play_pause.setIcon(self._theme.get_icon("play"))

        # Marqueurs
        self._btn_marker_a.setIcon(self._theme.get_icon("marker_a"))
        self._btn_marker_b.setIcon(self._theme.get_icon("marker_b"))
        self._btn_clear.setIcon(self._theme.get_icon("clear"))

        # Undo/Redo
        self._btn_undo.setIcon(self._theme.get_icon("undo"))
        self._btn_redo.setIcon(self._theme.get_icon("redo"))
