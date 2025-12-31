"""Dialogue d'édition d'une région de découpe.

Ce module fournit un dialogue pour modifier les bornes
(début et fin) d'une région de découpe existante.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from core.cut_manager import CutRegion


class RegionEditDialog(QDialog):
    """Dialogue pour modifier les bornes d'une région."""

    def __init__(
        self,
        region: CutRegion,
        video_duration_ms: int,
        parent: QWidget | None = None
    ) -> None:
        """Initialise le dialogue.

        Args:
            region: Région à modifier
            video_duration_ms: Durée totale de la vidéo en ms
            parent: Widget parent
        """
        super().__init__(parent)

        self._region = region
        self._video_duration_ms = video_duration_ms

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configure l'interface du dialogue."""
        self.setWindowTitle("Modifier la région")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Informations
        info_label = QLabel(
            "Modifiez les temps de début et de fin de la région."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Formulaire
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Spinboxes pour les temps (en secondes pour plus de précision)
        self._spin_start = QSpinBox()
        self._spin_start.setRange(0, self._video_duration_ms // 1000)
        self._spin_start.setValue(self._region.start_ms // 1000)
        self._spin_start.setSuffix(" sec")
        self._spin_start.valueChanged.connect(self._on_start_changed)

        self._spin_end = QSpinBox()
        self._spin_end.setRange(0, self._video_duration_ms // 1000)
        self._spin_end.setValue(self._region.end_ms // 1000)
        self._spin_end.setSuffix(" sec")
        self._spin_end.valueChanged.connect(self._on_end_changed)

        # Labels pour affichage formaté
        self._lbl_start_formatted = QLabel(self._format_time(self._region.start_ms))
        self._lbl_end_formatted = QLabel(self._format_time(self._region.end_ms))

        form_layout.addRow("Début:", self._spin_start)
        form_layout.addRow("", self._lbl_start_formatted)
        form_layout.addRow("Fin:", self._spin_end)
        form_layout.addRow("", self._lbl_end_formatted)

        # Durée de la région
        self._lbl_duration = QLabel()
        self._update_duration_label()
        form_layout.addRow("Durée:", self._lbl_duration)

        layout.addLayout(form_layout)

        # Boutons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_start_changed(self, value: int) -> None:
        """Gère le changement du temps de début."""
        self._lbl_start_formatted.setText(self._format_time(value * 1000))
        self._update_duration_label()

    def _on_end_changed(self, value: int) -> None:
        """Gère le changement du temps de fin."""
        self._lbl_end_formatted.setText(self._format_time(value * 1000))
        self._update_duration_label()

    def _update_duration_label(self) -> None:
        """Met à jour le label de durée."""
        start_ms = self._spin_start.value() * 1000
        end_ms = self._spin_end.value() * 1000
        duration_ms = max(0, end_ms - start_ms)
        self._lbl_duration.setText(self._format_time(duration_ms))

    @staticmethod
    def _format_time(ms: int) -> str:
        """Formate des millisecondes en HH:MM:SS."""
        total_seconds = ms // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_new_bounds(self) -> tuple[int, int]:
        """Retourne les nouvelles bornes en millisecondes.

        Returns:
            Tuple (start_ms, end_ms)
        """
        start_ms = self._spin_start.value() * 1000
        end_ms = self._spin_end.value() * 1000
        return (start_ms, end_ms)
