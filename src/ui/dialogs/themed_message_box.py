"""Boîtes de dialogue stylisées selon le thème.

Ce module fournit des alternatives à QMessageBox qui respectent
le thème clair/sombre de l'application.
"""

from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget

from ui.theme import ThemeManager


class ThemedMessageBox:
    """Utilitaire pour afficher des boîtes de dialogue thématisées."""

    @staticmethod
    def _apply_theme(msg_box: QMessageBox) -> None:
        """Applique le style du thème actuel à une QMessageBox.

        Args:
            msg_box: La boîte de dialogue à styliser
        """
        theme = ThemeManager.instance()
        palette = theme.palette

        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {palette['surface']};
            }}
            QMessageBox QLabel {{
                color: {palette['text_primary']};
                background-color: transparent;
            }}
            QPushButton {{
                background-color: {palette['surface']};
                color: {palette['text_primary']};
                border: 1px solid {palette['border']};
                border-radius: 4px;
                padding: 6px 16px;
                min-width: 80px;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {palette['surface_hover']};
                border-color: {palette['border_strong']};
            }}
            QPushButton:pressed {{
                background-color: {palette['surface_pressed']};
            }}
        """)

    @staticmethod
    def information(
        parent: QWidget | None,
        title: str,
        text: str
    ) -> None:
        """Affiche une boîte de dialogue d'information.

        Args:
            parent: Widget parent
            title: Titre de la boîte de dialogue
            text: Message à afficher
        """
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        ThemedMessageBox._apply_theme(msg_box)
        msg_box.exec()

    @staticmethod
    def warning(
        parent: QWidget | None,
        title: str,
        text: str
    ) -> None:
        """Affiche une boîte de dialogue d'avertissement.

        Args:
            parent: Widget parent
            title: Titre de la boîte de dialogue
            text: Message à afficher
        """
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        ThemedMessageBox._apply_theme(msg_box)
        msg_box.exec()

    @staticmethod
    def critical(
        parent: QWidget | None,
        title: str,
        text: str
    ) -> None:
        """Affiche une boîte de dialogue d'erreur critique.

        Args:
            parent: Widget parent
            title: Titre de la boîte de dialogue
            text: Message à afficher
        """
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        ThemedMessageBox._apply_theme(msg_box)
        msg_box.exec()

    @staticmethod
    def question(
        parent: QWidget | None,
        title: str,
        text: str
    ) -> bool:
        """Affiche une boîte de dialogue de question Oui/Non.

        Args:
            parent: Widget parent
            title: Titre de la boîte de dialogue
            text: Question à poser

        Returns:
            True si l'utilisateur a cliqué Oui, False sinon
        """
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        ThemedMessageBox._apply_theme(msg_box)
        result = msg_box.exec()
        return result == QMessageBox.StandardButton.Yes
