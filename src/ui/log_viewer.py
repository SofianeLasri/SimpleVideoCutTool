"""Widget de visualisation des logs.

Ce module fournit un panneau rétractable pour:
- Afficher les logs d'encodage en temps réel
- Colorer les messages par niveau (info, warning, error)
- Copier les logs dans le presse-papiers
- Effacer les logs affichés
"""

from __future__ import annotations

from PySide6.QtCore import Slot
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QApplication,
)

from ui.theme import ThemeManager


class LogViewerWidget(QWidget):
    """Widget de visualisation des logs avec couleurs."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialise le panneau de logs.

        Args:
            parent: Widget parent
        """
        super().__init__(parent)
        self._is_expanded: bool = False  # Fermé par défaut
        self._theme = ThemeManager.instance()
        self._setup_ui()

    @property
    def _log_colors(self) -> dict[str, str]:
        """Retourne les couleurs de log adaptées au thème."""
        return self._theme.get_log_colors()

    def _setup_ui(self) -> None:
        """Configure l'interface du widget."""
        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        # Barre de titre
        header_layout: QHBoxLayout = QHBoxLayout()
        header_layout.setContentsMargins(5, 2, 5, 2)

        self._btn_toggle: QPushButton = QPushButton("> Logs d'encodage")  # Fermé par défaut
        self._btn_toggle.setFlat(True)
        self._btn_toggle.clicked.connect(self._toggle_expanded)

        self._btn_copy: QPushButton = QPushButton("Copier")
        self._btn_copy.setFixedWidth(72)
        self._btn_copy.setToolTip("Copier les logs dans le presse-papiers")
        self._btn_copy.clicked.connect(self._copy_to_clipboard)

        self._btn_clear: QPushButton = QPushButton("Effacer")
        self._btn_clear.setFixedWidth(72)
        self._btn_clear.setToolTip("Effacer les logs affichés")
        self._btn_clear.clicked.connect(self.clear)

        header_layout.addWidget(self._btn_toggle)
        header_layout.addStretch()
        header_layout.addWidget(self._btn_copy)
        header_layout.addWidget(self._btn_clear)

        main_layout.addLayout(header_layout)

        # Zone de texte
        self._text_edit: QTextEdit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setMinimumHeight(80)
        self._text_edit.setMaximumHeight(150)
        self._text_edit.setVisible(False)  # Fermé par défaut

        main_layout.addWidget(self._text_edit)

    @Slot()
    def _toggle_expanded(self) -> None:
        """Bascule l'état replié/déplié."""
        self._is_expanded = not self._is_expanded
        self._text_edit.setVisible(self._is_expanded)

        if self._is_expanded:
            self._btn_toggle.setText("v Logs d'encodage")
        else:
            self._btn_toggle.setText("> Logs d'encodage")

    @Slot()
    def _copy_to_clipboard(self) -> None:
        """Copie les logs dans le presse-papiers."""
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self._text_edit.toPlainText())

    @Slot()
    def clear(self) -> None:
        """Efface les logs affichés."""
        self._text_edit.clear()

    def append_log(self, message: str, level: str = "INFO") -> None:
        """Ajoute un message de log.

        Args:
            message: Message à afficher
            level: Niveau (INFO, WARNING, ERROR, DEBUG)
        """
        # Déplacer le curseur à la fin
        cursor: QTextCursor = self._text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._text_edit.setTextCursor(cursor)

        # Formater le message avec couleur
        format_obj: QTextCharFormat = QTextCharFormat()
        colors = self._log_colors
        color: str = colors.get(level.upper(), colors["INFO"])
        format_obj.setForeground(QColor(color))

        # Ajouter le préfixe de niveau
        level_prefix: str = f"[{level.upper()}] "

        cursor.insertText(level_prefix, format_obj)

        # Message en couleur texte principale
        format_obj.setForeground(self._theme.get_qcolor("text_primary"))
        cursor.insertText(f"{message}\n", format_obj)

        # Défiler vers le bas
        scrollbar = self._text_edit.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def set_expanded(self, expanded: bool) -> None:
        """Définit l'état replié/déplié.

        Args:
            expanded: True pour déplier
        """
        if expanded != self._is_expanded:
            self._toggle_expanded()

    @property
    def is_expanded(self) -> bool:
        """Retourne True si le panneau est déplié."""
        return self._is_expanded

    def get_log_text(self) -> str:
        """Retourne le texte complet des logs."""
        return self._text_edit.toPlainText()
