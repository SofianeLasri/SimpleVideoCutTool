"""Widget de lecture vidéo avec QMediaPlayer.

Ce module fournit un lecteur vidéo intégré avec:
- Prévisualisation en temps réel
- Contrôles play/pause/seek
- Synchronisation avec la timeline
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QUrl, Signal, Slot
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

if TYPE_CHECKING:
    pass


class VideoPlayerWidget(QWidget):
    """Widget de prévisualisation vidéo.

    Encapsule QMediaPlayer et QVideoWidget pour la lecture vidéo.
    """

    # Signaux
    position_changed = Signal(int)
    """Émis quand la position change (millisecondes)."""

    duration_changed = Signal(int)
    """Émis quand la durée est connue (millisecondes)."""

    playback_state_changed = Signal(QMediaPlayer.PlaybackState)
    """Émis quand l'état de lecture change."""

    media_loaded = Signal(bool)
    """Émis quand un média est chargé (success)."""

    error_occurred = Signal(str)
    """Émis en cas d'erreur (message)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise le lecteur vidéo.

        Args:
            parent: Widget parent
        """
        super().__init__(parent)

        self._setup_ui()
        self._setup_media_player()
        self._current_file: str | None = None
        self._show_first_frame: bool = False

    def _setup_ui(self) -> None:
        """Configure l'interface du widget."""
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Widget vidéo
        self._video_widget: QVideoWidget = QVideoWidget()
        self._video_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self._video_widget.setMinimumSize(320, 180)

        layout.addWidget(self._video_widget)

    def _setup_media_player(self) -> None:
        """Configure le lecteur multimédia."""
        # Sortie audio
        self._audio_output: QAudioOutput = QAudioOutput()
        self._audio_output.setVolume(0.7)

        # Lecteur
        self._player: QMediaPlayer = QMediaPlayer()
        self._player.setAudioOutput(self._audio_output)
        self._player.setVideoOutput(self._video_widget)

        # Connexions signaux
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)
        self._player.errorOccurred.connect(self._on_error)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)

    @property
    def duration(self) -> int:
        """Durée totale en millisecondes."""
        return self._player.duration()

    @property
    def position(self) -> int:
        """Position actuelle en millisecondes."""
        return self._player.position()

    @property
    def is_playing(self) -> bool:
        """True si la vidéo est en lecture."""
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    @property
    def is_paused(self) -> bool:
        """True si la vidéo est en pause."""
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PausedState

    @property
    def volume(self) -> float:
        """Volume actuel (0.0 à 1.0)."""
        return self._audio_output.volume()

    @property
    def current_file(self) -> str | None:
        """Chemin du fichier actuellement chargé."""
        return self._current_file

    def load_video(self, file_path: str | Path) -> bool:
        """Charge un fichier vidéo.

        Args:
            file_path: Chemin vers le fichier vidéo

        Returns:
            True si le chargement a démarré
        """
        path: Path = Path(file_path)

        if not path.exists():
            self.error_occurred.emit(f"Fichier non trouvé: {path}")
            return False

        self._current_file = str(path)
        self._show_first_frame = True  # Afficher la première frame au chargement
        url: QUrl = QUrl.fromLocalFile(str(path))
        self._player.setSource(url)

        return True

    def unload(self) -> None:
        """Décharge la vidéo actuelle."""
        self._player.stop()
        self._player.setSource(QUrl())
        self._current_file = None

    @Slot()
    def play(self) -> None:
        """Démarre la lecture."""
        if self._player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            self._player.play()

    @Slot()
    def pause(self) -> None:
        """Met en pause la lecture."""
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()

    @Slot()
    def toggle_playback(self) -> None:
        """Bascule entre lecture et pause."""
        if self.is_playing:
            self.pause()
        else:
            self.play()

    @Slot()
    def stop(self) -> None:
        """Arrête la lecture et revient au début."""
        self._player.stop()

    def seek(self, position_ms: int) -> None:
        """Déplace la position de lecture.

        Args:
            position_ms: Position en millisecondes
        """
        position_ms = max(0, min(position_ms, self._player.duration()))
        self._player.setPosition(position_ms)

    def seek_relative(self, delta_ms: int) -> None:
        """Déplace la position relativement.

        Args:
            delta_ms: Déplacement en millisecondes (positif ou négatif)
        """
        new_pos: int = self._player.position() + delta_ms
        self.seek(new_pos)

    def step_forward(self, ms: int = 100) -> None:
        """Avance d'un pas.

        Args:
            ms: Nombre de millisecondes
        """
        self.seek_relative(ms)

    def step_backward(self, ms: int = 100) -> None:
        """Recule d'un pas.

        Args:
            ms: Nombre de millisecondes
        """
        self.seek_relative(-ms)

    def set_volume(self, volume: float) -> None:
        """Définit le volume.

        Args:
            volume: Volume entre 0.0 et 1.0
        """
        self._audio_output.setVolume(max(0.0, min(1.0, volume)))

    def set_muted(self, muted: bool) -> None:
        """Active/désactive le son.

        Args:
            muted: True pour couper le son
        """
        self._audio_output.setMuted(muted)

    def go_to_start(self) -> None:
        """Va au début de la vidéo."""
        self.seek(0)

    def go_to_end(self) -> None:
        """Va à la fin de la vidéo."""
        self.seek(self._player.duration())

    # Slots privés
    @Slot(int)
    def _on_position_changed(self, position: int) -> None:
        """Gère le changement de position."""
        self.position_changed.emit(position)

    @Slot(int)
    def _on_duration_changed(self, duration: int) -> None:
        """Gère le changement de durée."""
        self.duration_changed.emit(duration)

    @Slot(QMediaPlayer.PlaybackState)
    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        """Gère le changement d'état de lecture."""
        self.playback_state_changed.emit(state)

    @Slot(QMediaPlayer.Error, str)
    def _on_error(self, error: QMediaPlayer.Error, message: str) -> None:
        """Gère les erreurs du lecteur."""
        if error != QMediaPlayer.Error.NoError:
            self.error_occurred.emit(f"Erreur lecteur: {message}")
            self.media_loaded.emit(False)

    @Slot(QMediaPlayer.MediaStatus)
    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        """Gère le changement de statut média."""
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            # Afficher la première frame uniquement au premier chargement
            if self._show_first_frame:
                self._show_first_frame = False
                self._player.setPosition(0)
                self._player.pause()
            self.media_loaded.emit(True)
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self.error_occurred.emit("Format vidéo non supporté")
            self.media_loaded.emit(False)
