"""Widget timeline personnalisé avec marqueurs A-B.

Ce module fournit une timeline interactive pour:
- Visualiser la durée de la vidéo
- Afficher et gérer les régions de découpe
- Naviguer dans la vidéo par clic
- Afficher la position de lecture
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QRect, Signal, QPoint, Slot
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPen, QBrush, QFont, QContextMenuEvent
from PySide6.QtWidgets import QWidget, QSizePolicy, QMenu

from ui.theme import ThemeManager

if TYPE_CHECKING:
    from core.cut_manager import CutRegion


class TimelineWidget(QWidget):
    """Widget timeline avec visualisation des régions A-B."""

    # Signaux
    seek_requested = Signal(int)
    """Émis quand l'utilisateur clique pour naviguer (position_ms)."""

    region_clicked = Signal(int)
    """Émis quand une région est cliquée (index)."""

    region_edit_requested = Signal(int)
    """Émis quand l'utilisateur demande à éditer une région (index)."""

    region_delete_requested = Signal(int)
    """Émis quand l'utilisateur demande à supprimer une région (index)."""

    # Dimensions
    TRACK_HEIGHT: int = 40
    MARKER_WIDTH: int = 2
    PLAYHEAD_WIDTH: int = 2
    TIME_MARKER_HEIGHT: int = 20
    PADDING: int = 10

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise la timeline.

        Args:
            parent: Widget parent
        """
        super().__init__(parent)

        self._duration_ms: int = 0
        self._position_ms: int = 0
        self._regions: list[CutRegion] = []
        self._pending_marker_a: int | None = None
        self._hovered_region: int | None = None
        self._theme = ThemeManager.instance()

        self._setup_ui()
        self._theme.theme_changed.connect(self._on_theme_changed)

    @Slot(str)
    def _on_theme_changed(self, _theme: str) -> None:
        """Redessine lors du changement de thème."""
        self.update()

    @property
    def _color_background(self) -> QColor:
        return self._theme.get_qcolor("background")

    @property
    def _color_track(self) -> QColor:
        return self._theme.get_qcolor("track")

    @property
    def _color_track_border(self) -> QColor:
        return self._theme.get_qcolor("border_strong")

    @property
    def _color_playhead(self) -> QColor:
        return self._theme.get_qcolor("playhead")

    @property
    def _color_marker_a(self) -> QColor:
        return self._theme.get_qcolor("marker_a")

    @property
    def _color_time_text(self) -> QColor:
        return self._theme.get_qcolor("text_secondary")

    def _setup_ui(self) -> None:
        """Configure l'interface du widget."""
        self.setMinimumHeight(80)
        self.setMaximumHeight(100)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @property
    def duration_ms(self) -> int:
        """Durée totale en millisecondes."""
        return self._duration_ms

    def set_duration(self, duration_ms: int) -> None:
        """Définit la durée totale de la vidéo.

        Args:
            duration_ms: Durée en millisecondes
        """
        self._duration_ms = max(0, duration_ms)
        self.update()

    def set_position(self, position_ms: int) -> None:
        """Met à jour la position de lecture.

        Args:
            position_ms: Position en millisecondes
        """
        self._position_ms = max(0, min(position_ms, self._duration_ms))
        self.update()

    def set_regions(self, regions: list[CutRegion]) -> None:
        """Met à jour les régions affichées.

        Args:
            regions: Liste des régions de découpe
        """
        self._regions = regions
        self.update()

    def set_pending_marker_a(self, position_ms: int | None) -> None:
        """Affiche ou masque le marqueur A en attente.

        Args:
            position_ms: Position du marqueur ou None
        """
        self._pending_marker_a = position_ms
        self.update()

    def clear(self) -> None:
        """Efface la timeline."""
        self._duration_ms = 0
        self._position_ms = 0
        self._regions = []
        self._pending_marker_a = None
        self.update()

    # Méthodes de dessin
    def paintEvent(self, event: QPaintEvent) -> None:
        """Dessine la timeline."""
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fond
        painter.fillRect(self.rect(), self._color_background)

        if self._duration_ms <= 0:
            self._draw_empty_state(painter)
            return

        # Zone de la piste
        track_rect: QRect = self._get_track_rect()

        # Dessiner dans l'ordre
        self._draw_track(painter, track_rect)
        self._draw_time_markers(painter, track_rect)
        self._draw_regions(painter, track_rect)
        self._draw_pending_marker(painter, track_rect)
        self._draw_playhead(painter, track_rect)

        painter.end()

    def _get_track_rect(self) -> QRect:
        """Retourne le rectangle de la piste."""
        return QRect(
            self.PADDING,
            self.TIME_MARKER_HEIGHT,
            self.width() - 2 * self.PADDING,
            self.TRACK_HEIGHT
        )

    def _draw_empty_state(self, painter: QPainter) -> None:
        """Dessine l'état vide (pas de vidéo)."""
        painter.setPen(self._color_time_text)
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "Ouvrez une vidéo pour commencer"
        )

    def _draw_track(self, painter: QPainter, track_rect: QRect) -> None:
        """Dessine la piste principale."""
        # Fond de la piste
        painter.fillRect(track_rect, self._color_track)

        # Bordure
        painter.setPen(QPen(self._color_track_border, 1))
        painter.drawRect(track_rect)

    def _draw_time_markers(self, painter: QPainter, track_rect: QRect) -> None:
        """Dessine les marqueurs de temps."""
        if self._duration_ms <= 0:
            return

        painter.setPen(self._color_time_text)
        font: QFont = painter.font()
        font.setPointSize(8)
        painter.setFont(font)

        # Calculer l'intervalle approprié
        duration_sec: float = self._duration_ms / 1000.0
        interval_sec: float = self._calculate_time_interval(duration_sec)

        current_sec: float = 0.0
        while current_sec <= duration_sec:
            x: int = self._ms_to_x(int(current_sec * 1000), track_rect)

            # Trait
            painter.drawLine(x, track_rect.top() - 5, x, track_rect.top())

            # Texte
            time_str: str = self._format_time_short(int(current_sec))
            painter.drawText(
                x - 20, 0, 40, self.TIME_MARKER_HEIGHT - 5,
                Qt.AlignmentFlag.AlignCenter,
                time_str
            )

            current_sec += interval_sec

    def _calculate_time_interval(self, duration_sec: float) -> float:
        """Calcule l'intervalle de temps approprié pour les marqueurs."""
        if duration_sec <= 60:
            return 10.0
        elif duration_sec <= 300:
            return 30.0
        elif duration_sec <= 600:
            return 60.0
        elif duration_sec <= 1800:
            return 300.0
        else:
            return 600.0

    def _format_time_short(self, seconds: int) -> str:
        """Formate le temps en MM:SS ou H:MM:SS."""
        hours: int = seconds // 3600
        minutes: int = (seconds % 3600) // 60
        secs: int = seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def _draw_regions(self, painter: QPainter, track_rect: QRect) -> None:
        """Dessine les régions de découpe."""
        for i, region in enumerate(self._regions):
            x_start: int = self._ms_to_x(region.start_ms, track_rect)
            x_end: int = self._ms_to_x(region.end_ms, track_rect)

            # Couleur avec transparence
            color: QColor = QColor(region.color)
            color.setAlpha(150 if i != self._hovered_region else 200)

            region_rect: QRect = QRect(
                x_start,
                track_rect.top() + 2,
                x_end - x_start,
                track_rect.height() - 4
            )

            painter.fillRect(region_rect, color)

            # Bordure
            border_color: QColor = QColor(region.color)
            border_color.setAlpha(255)
            painter.setPen(QPen(border_color, 2))
            painter.drawRect(region_rect)

    def _draw_pending_marker(self, painter: QPainter, track_rect: QRect) -> None:
        """Dessine le marqueur A en attente."""
        if self._pending_marker_a is None:
            return

        x: int = self._ms_to_x(self._pending_marker_a, track_rect)

        # Ligne verticale
        pen: QPen = QPen(self._color_marker_a, self.MARKER_WIDTH)
        painter.setPen(pen)
        painter.drawLine(x, track_rect.top(), x, track_rect.bottom())

        # Triangle indicateur
        painter.setBrush(QBrush(self._color_marker_a))
        painter.drawPolygon([
            QPoint(x - 6, track_rect.top()),
            QPoint(x + 6, track_rect.top()),
            QPoint(x, track_rect.top() + 8),
        ])

    def _draw_playhead(self, painter: QPainter, track_rect: QRect) -> None:
        """Dessine la tête de lecture."""
        x: int = self._ms_to_x(self._position_ms, track_rect)

        # Ligne verticale
        pen: QPen = QPen(self._color_playhead, self.PLAYHEAD_WIDTH)
        painter.setPen(pen)
        painter.drawLine(x, track_rect.top() - 5, x, track_rect.bottom() + 5)

        # Triangle en haut
        painter.setBrush(QBrush(self._color_playhead))
        painter.drawPolygon([
            QPoint(x - 5, track_rect.top() - 5),
            QPoint(x + 5, track_rect.top() - 5),
            QPoint(x, track_rect.top() + 3),
        ])

    # Conversion coordonnées
    def _ms_to_x(self, ms: int, track_rect: QRect) -> int:
        """Convertit des millisecondes en position X."""
        if self._duration_ms <= 0:
            return track_rect.left()
        ratio: float = ms / self._duration_ms
        return track_rect.left() + int(ratio * track_rect.width())

    def _x_to_ms(self, x: int, track_rect: QRect) -> int:
        """Convertit une position X en millisecondes."""
        if track_rect.width() <= 0:
            return 0
        x = max(track_rect.left(), min(x, track_rect.right()))
        ratio: float = (x - track_rect.left()) / track_rect.width()
        return int(ratio * self._duration_ms)

    # Événements souris
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Gère le clic souris."""
        if event.button() != Qt.MouseButton.LeftButton:
            return

        if self._duration_ms <= 0:
            return

        track_rect: QRect = self._get_track_rect()
        pos_ms: int = self._x_to_ms(event.position().x(), track_rect)  # type: ignore[arg-type]

        # Vérifier si on clique sur une région
        for i, region in enumerate(self._regions):
            if region.start_ms <= pos_ms <= region.end_ms:
                self.region_clicked.emit(i)
                return

        # Sinon, seek à cette position
        self.seek_requested.emit(pos_ms)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Gère le mouvement souris."""
        if self._duration_ms <= 0:
            return

        track_rect: QRect = self._get_track_rect()
        pos_ms: int = self._x_to_ms(event.position().x(), track_rect)  # type: ignore[arg-type]

        # Détecter le survol d'une région
        new_hovered: int | None = None
        for i, region in enumerate(self._regions):
            if region.start_ms <= pos_ms <= region.end_ms:
                new_hovered = i
                break

        if new_hovered != self._hovered_region:
            self._hovered_region = new_hovered
            self.update()

    def leaveEvent(self, event: object) -> None:
        """Gère la sortie de la souris."""
        if self._hovered_region is not None:
            self._hovered_region = None
            self.update()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Affiche le menu contextuel pour les régions."""
        if self._duration_ms <= 0 or not self._regions:
            return

        track_rect: QRect = self._get_track_rect()
        pos_ms: int = self._x_to_ms(event.pos().x(), track_rect)

        # Trouver la région sous le curseur
        region_index: int | None = None
        for i, region in enumerate(self._regions):
            if region.start_ms <= pos_ms <= region.end_ms:
                region_index = i
                break

        if region_index is None:
            return

        # Créer le menu contextuel
        menu = QMenu(self)

        edit_action = menu.addAction("Modifier...")
        edit_action.triggered.connect(
            lambda: self.region_edit_requested.emit(region_index)
        )

        delete_action = menu.addAction("Supprimer")
        delete_action.triggered.connect(
            lambda: self.region_delete_requested.emit(region_index)
        )

        menu.exec(event.globalPos())
