"""Gestionnaire des régions de découpe A-B.

Ce module gère:
- Le placement des marqueurs A et B
- Les régions de découpe (plusieurs possibles)
- Le calcul des segments finaux à garder/supprimer
- L'historique undo/redo
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor

if TYPE_CHECKING:
    pass


@dataclass
class CutRegion:
    """Représente une région de découpe A-B."""

    start_ms: int
    """Position du marqueur A en millisecondes."""

    end_ms: int
    """Position du marqueur B en millisecondes."""

    color: QColor = field(default_factory=lambda: QColor("#4CAF50"))
    """Couleur de la région pour l'affichage."""

    @property
    def duration_ms(self) -> int:
        """Durée de la région en millisecondes."""
        return self.end_ms - self.start_ms

    @property
    def start_seconds(self) -> float:
        """Position de début en secondes."""
        return self.start_ms / 1000.0

    @property
    def end_seconds(self) -> float:
        """Position de fin en secondes."""
        return self.end_ms / 1000.0

    def contains(self, position_ms: int) -> bool:
        """Vérifie si une position est dans cette région.

        Args:
            position_ms: Position en millisecondes

        Returns:
            True si la position est dans la région
        """
        return self.start_ms <= position_ms <= self.end_ms

    def overlaps(self, other: CutRegion) -> bool:
        """Vérifie si cette région chevauche une autre.

        Args:
            other: Autre région à vérifier

        Returns:
            True si les régions se chevauchent
        """
        return not (self.end_ms <= other.start_ms or self.start_ms >= other.end_ms)

    def as_tuple(self) -> tuple[float, float]:
        """Retourne la région comme tuple (start_seconds, end_seconds)."""
        return (self.start_seconds, self.end_seconds)


class CutManager(QObject):
    """Gestionnaire des régions de découpe.

    Gère le workflow de placement des marqueurs A-B
    et le calcul des segments finaux.
    """

    # Signaux
    regions_changed = Signal()
    """Émis quand les régions changent."""

    marker_a_set = Signal(int)
    """Émis quand le marqueur A est placé (position_ms)."""

    marker_a_cleared = Signal()
    """Émis quand le marqueur A est effacé."""

    # Couleurs pour les régions (cycle)
    REGION_COLORS: list[str] = [
        "#4CAF50",  # Vert
        "#2196F3",  # Bleu
        "#FF9800",  # Orange
        "#9C27B0",  # Violet
        "#00BCD4",  # Cyan
        "#E91E63",  # Rose
    ]

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialise le gestionnaire de découpe.

        Args:
            parent: Widget parent Qt
        """
        super().__init__(parent)

        self._regions: list[CutRegion] = []
        self._pending_marker_a: int | None = None
        self._video_duration_ms: int = 0
        self._color_index: int = 0

        # Historique pour undo/redo
        self._history: list[list[CutRegion]] = []
        self._history_index: int = -1
        self._max_history: int = 50

    @property
    def regions(self) -> list[CutRegion]:
        """Retourne une copie de la liste des régions."""
        return list(self._regions)

    @property
    def pending_marker_a(self) -> int | None:
        """Position du marqueur A en attente, ou None."""
        return self._pending_marker_a

    @property
    def has_pending_marker(self) -> bool:
        """True si un marqueur A est en attente d'un B."""
        return self._pending_marker_a is not None

    @property
    def region_count(self) -> int:
        """Nombre de régions définies."""
        return len(self._regions)

    @property
    def video_duration_ms(self) -> int:
        """Durée de la vidéo en millisecondes."""
        return self._video_duration_ms

    def get_region(self, index: int) -> CutRegion | None:
        """Retourne une région par son index.

        Args:
            index: Index de la région

        Returns:
            CutRegion ou None si index invalide
        """
        if 0 <= index < len(self._regions):
            return self._regions[index]
        return None

    def set_video_duration(self, duration_ms: int) -> None:
        """Définit la durée totale de la vidéo.

        Args:
            duration_ms: Durée en millisecondes
        """
        self._video_duration_ms = duration_ms
        self.clear_all()

    def set_marker_a(self, position_ms: int) -> bool:
        """Place le marqueur A.

        Args:
            position_ms: Position en millisecondes

        Returns:
            True si le marqueur a été placé
        """
        if position_ms < 0 or position_ms > self._video_duration_ms:
            return False

        self._pending_marker_a = position_ms
        self.marker_a_set.emit(position_ms)
        return True

    def set_marker_b(self, position_ms: int) -> bool:
        """Place le marqueur B et crée une région.

        Le marqueur A doit être défini au préalable.
        Si B est avant A, les positions sont inversées.

        Args:
            position_ms: Position en millisecondes

        Returns:
            True si la région a été créée
        """
        if self._pending_marker_a is None:
            return False

        if position_ms < 0 or position_ms > self._video_duration_ms:
            return False

        # Ordonner les positions
        start: int = min(self._pending_marker_a, position_ms)
        end: int = max(self._pending_marker_a, position_ms)

        # Vérifier que la région a une durée minimale (100ms)
        if end - start < 100:
            return False

        # Créer la région
        color: QColor = QColor(self.REGION_COLORS[self._color_index % len(self.REGION_COLORS)])
        self._color_index += 1

        region: CutRegion = CutRegion(start_ms=start, end_ms=end, color=color)

        # Sauvegarder l'état pour undo
        self._save_history()

        self._regions.append(region)
        self._pending_marker_a = None

        # Trier par position de début
        self._regions.sort(key=lambda r: r.start_ms)

        self.marker_a_cleared.emit()
        self.regions_changed.emit()
        return True

    def cancel_marker_a(self) -> None:
        """Annule le marqueur A en attente."""
        if self._pending_marker_a is not None:
            self._pending_marker_a = None
            self.marker_a_cleared.emit()

    def remove_region(self, index: int) -> bool:
        """Supprime une région par son index.

        Args:
            index: Index de la région à supprimer

        Returns:
            True si la région a été supprimée
        """
        if 0 <= index < len(self._regions):
            self._save_history()
            del self._regions[index]
            self.regions_changed.emit()
            return True
        return False

    def edit_region(self, index: int, new_start_ms: int, new_end_ms: int) -> bool:
        """Modifie les bornes d'une région existante.

        Args:
            index: Index de la région à modifier
            new_start_ms: Nouveau temps de début en ms
            new_end_ms: Nouveau temps de fin en ms

        Returns:
            True si la région a été modifiée
        """
        if not (0 <= index < len(self._regions)):
            return False

        # Ordonner les positions
        start = min(new_start_ms, new_end_ms)
        end = max(new_start_ms, new_end_ms)

        # Vérifier les bornes
        if start < 0 or end > self._video_duration_ms:
            return False

        # Durée minimale
        if end - start < 100:
            return False

        self._save_history()

        # Conserver la couleur
        old_color = self._regions[index].color

        self._regions[index] = CutRegion(
            start_ms=start,
            end_ms=end,
            color=old_color
        )

        # Re-trier par position de début
        self._regions.sort(key=lambda r: r.start_ms)

        self.regions_changed.emit()
        return True

    def remove_region_at_position(self, position_ms: int) -> bool:
        """Supprime la région contenant une position.

        Args:
            position_ms: Position en millisecondes

        Returns:
            True si une région a été supprimée
        """
        for i, region in enumerate(self._regions):
            if region.contains(position_ms):
                return self.remove_region(i)
        return False

    def clear_all(self) -> None:
        """Efface toutes les régions et le marqueur A."""
        if self._regions or self._pending_marker_a is not None:
            self._save_history()

        self._regions.clear()
        self._pending_marker_a = None
        self._color_index = 0

        self.marker_a_cleared.emit()
        self.regions_changed.emit()

    def get_region_at_position(self, position_ms: int) -> CutRegion | None:
        """Retourne la région contenant une position.

        Args:
            position_ms: Position en millisecondes

        Returns:
            CutRegion ou None
        """
        for region in self._regions:
            if region.contains(position_ms):
                return region
        return None

    def get_final_segments(self, keep_mode: bool = True) -> list[tuple[float, float]]:
        """Calcule les segments finaux selon le mode.

        Args:
            keep_mode: True = garder les régions, False = les supprimer

        Returns:
            Liste de tuples (start_seconds, end_seconds)
        """
        if not self._regions:
            # Pas de régions: garder toute la vidéo
            if self._video_duration_ms > 0:
                return [(0.0, self._video_duration_ms / 1000.0)]
            return []

        if keep_mode:
            # Mode "garder": retourner les régions
            return [region.as_tuple() for region in self._regions]
        else:
            # Mode "couper": retourner les intervalles entre les régions
            return self._calculate_inverse_segments()

    def _calculate_inverse_segments(self) -> list[tuple[float, float]]:
        """Calcule les segments inversés (entre les régions).

        Returns:
            Liste des segments à garder quand on coupe les régions
        """
        if not self._regions:
            return [(0.0, self._video_duration_ms / 1000.0)]

        segments: list[tuple[float, float]] = []
        current_pos: float = 0.0

        for region in self._regions:
            start_sec: float = region.start_ms / 1000.0
            if current_pos < start_sec:
                segments.append((current_pos, start_sec))
            current_pos = region.end_ms / 1000.0

        # Segment après la dernière région
        end_sec: float = self._video_duration_ms / 1000.0
        if current_pos < end_sec:
            segments.append((current_pos, end_sec))

        return segments

    def get_total_selected_duration_ms(self) -> int:
        """Calcule la durée totale des régions sélectionnées.

        Returns:
            Durée en millisecondes
        """
        return sum(region.duration_ms for region in self._regions)

    def has_overlapping_regions(self) -> bool:
        """Vérifie s'il y a des régions qui se chevauchent.

        Returns:
            True si des régions se chevauchent
        """
        for i, region_a in enumerate(self._regions):
            for region_b in self._regions[i + 1:]:
                if region_a.overlaps(region_b):
                    return True
        return False

    def merge_overlapping_regions(self) -> None:
        """Fusionne les régions qui se chevauchent."""
        if len(self._regions) < 2:
            return

        self._save_history()

        # Trier par début
        self._regions.sort(key=lambda r: r.start_ms)

        merged: list[CutRegion] = []
        current: CutRegion = self._regions[0]

        for region in self._regions[1:]:
            if current.overlaps(region) or current.end_ms >= region.start_ms:
                # Fusionner
                current = CutRegion(
                    start_ms=current.start_ms,
                    end_ms=max(current.end_ms, region.end_ms),
                    color=current.color
                )
            else:
                merged.append(current)
                current = region

        merged.append(current)
        self._regions = merged
        self.regions_changed.emit()

    def _save_history(self) -> None:
        """Sauvegarde l'état actuel dans l'historique."""
        # Supprimer l'historique après l'index actuel
        if self._history_index < len(self._history) - 1:
            self._history = self._history[:self._history_index + 1]

        # Sauvegarder une copie des régions
        state: list[CutRegion] = [
            CutRegion(r.start_ms, r.end_ms, QColor(r.color))
            for r in self._regions
        ]
        self._history.append(state)
        self._history_index = len(self._history) - 1

        # Limiter la taille de l'historique
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
            self._history_index = len(self._history) - 1

    def can_undo(self) -> bool:
        """Vérifie si undo est possible."""
        return self._history_index > 0

    def can_redo(self) -> bool:
        """Vérifie si redo est possible."""
        return self._history_index < len(self._history) - 1

    def undo(self) -> bool:
        """Annule la dernière action.

        Returns:
            True si undo a été effectué
        """
        if not self.can_undo():
            return False

        self._history_index -= 1
        self._restore_from_history()
        return True

    def redo(self) -> bool:
        """Refait la dernière action annulée.

        Returns:
            True si redo a été effectué
        """
        if not self.can_redo():
            return False

        self._history_index += 1
        self._restore_from_history()
        return True

    def _restore_from_history(self) -> None:
        """Restaure l'état depuis l'historique."""
        if 0 <= self._history_index < len(self._history):
            state: list[CutRegion] = self._history[self._history_index]
            self._regions = [
                CutRegion(r.start_ms, r.end_ms, QColor(r.color))
                for r in state
            ]
            self._pending_marker_a = None
            self.marker_a_cleared.emit()
            self.regions_changed.emit()
