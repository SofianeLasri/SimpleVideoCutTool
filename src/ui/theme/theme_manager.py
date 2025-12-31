"""Gestionnaire de thèmes singleton.

Ce module fournit un gestionnaire centralisé pour les thèmes
de l'application, permettant de basculer entre mode sombre et clair.
"""

from __future__ import annotations

from typing import ClassVar

from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from .theme_definitions import DARK_PALETTE, LIGHT_PALETTE, REGION_COLORS
from .fluent_styles import generate_stylesheet, generate_log_viewer_colors


class ThemeManager(QObject):
    """Gestionnaire singleton pour les thèmes de l'application.

    Signals:
        theme_changed: Émis quand le thème change (nom du thème)
    """

    theme_changed = Signal(str)
    """Signal émis lors du changement de thème."""

    _instance: ClassVar[ThemeManager | None] = None

    def __new__(cls) -> ThemeManager:
        """Implémente le pattern singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialise le gestionnaire de thèmes."""
        # Éviter la réinitialisation du singleton
        if hasattr(self, "_initialized") and self._initialized:
            return

        super().__init__()
        self._initialized = True
        self._current_theme: str = "dark"
        self._settings = QSettings("SimpleVideoCut", "Preferences")

    @classmethod
    def instance(cls) -> ThemeManager:
        """Retourne l'instance singleton du gestionnaire.

        Returns:
            Instance unique de ThemeManager
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def current_theme(self) -> str:
        """Retourne le nom du thème actuel.

        Returns:
            "dark" ou "light"
        """
        return self._current_theme

    @property
    def is_dark(self) -> bool:
        """Vérifie si le thème actuel est sombre.

        Returns:
            True si thème sombre
        """
        return self._current_theme == "dark"

    @property
    def palette(self) -> dict[str, str]:
        """Retourne la palette de couleurs actuelle.

        Returns:
            Dictionnaire des couleurs
        """
        return DARK_PALETTE if self.is_dark else LIGHT_PALETTE

    def get_color(self, name: str) -> str:
        """Retourne une couleur de la palette actuelle.

        Args:
            name: Nom de la couleur (ex: "background", "accent")

        Returns:
            Code couleur hexadécimal
        """
        return self.palette.get(name, "#ff00ff")  # Magenta si non trouvé

    def get_qcolor(self, name: str) -> QColor:
        """Retourne une QColor de la palette actuelle.

        Args:
            name: Nom de la couleur

        Returns:
            QColor correspondante
        """
        return QColor(self.get_color(name))

    def get_region_color(self, index: int) -> QColor:
        """Retourne la couleur pour une région de coupe.

        Args:
            index: Index de la région

        Returns:
            QColor pour la région
        """
        color_hex = REGION_COLORS[index % len(REGION_COLORS)]
        return QColor(color_hex)

    def get_stylesheet(self) -> str:
        """Génère la feuille de style complète.

        Returns:
            QSS pour le thème actuel
        """
        return generate_stylesheet(self.palette)

    def get_log_colors(self) -> dict[str, str]:
        """Retourne les couleurs pour le log viewer.

        Returns:
            Dictionnaire niveau -> couleur
        """
        return generate_log_viewer_colors(self.palette)

    def load_saved_theme(self) -> None:
        """Charge le thème sauvegardé depuis les préférences."""
        saved_theme = self._settings.value("theme/mode", "dark")
        if saved_theme in ("dark", "light"):
            self._current_theme = saved_theme

    def save_theme(self) -> None:
        """Sauvegarde le thème actuel dans les préférences."""
        self._settings.setValue("theme/mode", self._current_theme)

    def set_theme(self, theme: str) -> None:
        """Change le thème de l'application.

        Args:
            theme: "dark" ou "light"
        """
        if theme not in ("dark", "light"):
            return

        if theme == self._current_theme:
            return

        self._current_theme = theme
        self.save_theme()
        self._apply_theme()
        self.theme_changed.emit(theme)

    def toggle_theme(self) -> None:
        """Bascule entre thème sombre et clair."""
        new_theme = "light" if self.is_dark else "dark"
        self.set_theme(new_theme)

    def _apply_theme(self) -> None:
        """Applique le thème à l'application."""
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self.get_stylesheet())

    def apply_initial_theme(self) -> None:
        """Applique le thème initial au démarrage.

        Doit être appelé après la création de QApplication.
        """
        self.load_saved_theme()
        self._apply_theme()
