"""Dialogue À propos de l'application.

Ce module fournit un dialogue personnalisé pour afficher
les informations sur l'application, respectant le thème actuel.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ui.theme import ThemeManager


class AboutDialog(QDialog):
    """Dialogue À propos de l'application."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise le dialogue.

        Args:
            parent: Widget parent
        """
        super().__init__(parent)
        self._theme = ThemeManager.instance()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configure l'interface du dialogue."""
        self.setWindowTitle("À propos de Simple Video Cut Tool")
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)

        # Appliquer le style de fond du dialogue
        palette = self._theme.palette
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {palette['surface']};
            }}
        """)

        # Style pour les liens
        link_color = palette['accent_light'] if self._theme.is_dark else palette['accent']

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Titre
        title_label = QLabel("Simple Video Cut Tool")
        title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {palette['text_primary']};
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel("Outil de découpe vidéo utilisant FFmpeg.")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addSpacing(8)

        # Auteur
        author_label = QLabel(
            f'Développé par Sofiane Lasri<br>'
            f'<a href="https://sofianelasri.fr" style="color: {link_color};">'
            f'https://sofianelasri.fr</a>'
        )
        author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        author_label.setOpenExternalLinks(True)
        author_label.setWordWrap(True)
        layout.addWidget(author_label)

        # Code source
        source_label = QLabel(
            f'Code source :<br>'
            f'<a href="https://github.com/SofianeLasri/SimpleVideoCutTool" '
            f'style="color: {link_color};">'
            f'https://github.com/SofianeLasri/SimpleVideoCutTool</a>'
        )
        source_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        source_label.setOpenExternalLinks(True)
        source_label.setWordWrap(True)
        layout.addWidget(source_label)

        layout.addSpacing(8)

        # Version
        version_label = QLabel("Version 1.1")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        layout.addStretch()

        # Bouton OK
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
