"""Gestionnaire d'icônes Font Awesome via qtawesome.

Ce module fournit des icônes adaptées au thème courant.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import qtawesome as qta
from PySide6.QtGui import QIcon

if TYPE_CHECKING:
    from ui.theme.theme_manager import ThemeManager


# Mapping des noms d'icônes vers les identifiants Font Awesome
ICON_MAP: Final[dict[str, str]] = {
    # Lecture
    "play": "fa5s.play",
    "pause": "fa5s.pause",
    "stop": "fa5s.stop",
    "step_backward": "fa5s.step-backward",
    "step_forward": "fa5s.step-forward",
    "backward": "fa5s.backward",
    "forward": "fa5s.forward",
    "go_start": "fa5s.fast-backward",
    "go_end": "fa5s.fast-forward",

    # Marqueurs
    "marker_a": "fa5s.map-marker-alt",
    "marker_b": "fa5s.flag-checkered",
    "clear": "fa5s.trash-alt",

    # Édition
    "undo": "fa5s.undo",
    "redo": "fa5s.redo",
    "edit": "fa5s.edit",
    "delete": "fa5s.trash",

    # Fichiers
    "open": "fa5s.folder-open",
    "save": "fa5s.save",
    "export": "fa5s.file-export",

    # Thème
    "sun": "fa5s.sun",
    "moon": "fa5s.moon",

    # Divers
    "volume": "fa5s.volume-up",
    "volume_mute": "fa5s.volume-mute",
    "cut": "fa5s.cut",
    "check": "fa5s.check",
    "times": "fa5s.times",
    "cog": "fa5s.cog",
    "info": "fa5s.info-circle",
    "warning": "fa5s.exclamation-triangle",
    "error": "fa5s.times-circle",
}


class IconProvider:
    """Fournisseur d'icônes avec support du thème."""

    def __init__(self, theme_manager: ThemeManager) -> None:
        """Initialise le fournisseur d'icônes.

        Args:
            theme_manager: Gestionnaire de thème pour les couleurs
        """
        self._theme = theme_manager
        self._cache: dict[str, QIcon] = {}

        # Invalider le cache au changement de thème
        self._theme.theme_changed.connect(self._clear_cache)

    def _clear_cache(self) -> None:
        """Vide le cache d'icônes."""
        self._cache.clear()

    def get_icon(
        self,
        name: str,
        color: str | None = None,
        size: int | None = None
    ) -> QIcon:
        """Retourne une icône par son nom.

        Args:
            name: Nom de l'icône (clé dans ICON_MAP)
            color: Couleur override (sinon utilise text_primary du thème)
            size: Taille de l'icône en pixels

        Returns:
            QIcon configurée
        """
        # Utiliser la couleur du thème si non spécifiée
        if color is None:
            color = self._theme.get_color("text_primary")

        # Clé de cache
        cache_key = f"{name}_{color}_{size}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Récupérer l'identifiant FA
        fa_name = ICON_MAP.get(name, name)

        # Créer l'icône
        options: dict = {"color": color}
        if size:
            options["scale_factor"] = size / 16.0

        try:
            icon = qta.icon(fa_name, **options)
        except Exception:
            # Fallback sur une icône vide
            icon = QIcon()

        self._cache[cache_key] = icon
        return icon

    def get_themed_icon(self, name: str) -> QIcon:
        """Retourne une icône avec la couleur du thème actuel.

        Args:
            name: Nom de l'icône

        Returns:
            QIcon avec couleur text_primary
        """
        return self.get_icon(name)

    def get_accent_icon(self, name: str) -> QIcon:
        """Retourne une icône avec la couleur d'accent.

        Args:
            name: Nom de l'icône

        Returns:
            QIcon avec couleur accent
        """
        return self.get_icon(name, color=self._theme.get_color("accent"))

    def get_success_icon(self, name: str) -> QIcon:
        """Retourne une icône verte (succès).

        Args:
            name: Nom de l'icône

        Returns:
            QIcon verte
        """
        return self.get_icon(name, color="#4CAF50")

    def get_warning_icon(self, name: str) -> QIcon:
        """Retourne une icône orange (avertissement).

        Args:
            name: Nom de l'icône

        Returns:
            QIcon orange
        """
        return self.get_icon(name, color="#FF9800")

    def get_error_icon(self, name: str) -> QIcon:
        """Retourne une icône rouge (erreur).

        Args:
            name: Nom de l'icône

        Returns:
            QIcon rouge
        """
        return self.get_icon(name, color="#F44336")


# Instance globale (initialisée par ThemeManager)
_icon_provider: IconProvider | None = None


def get_icon_provider() -> IconProvider | None:
    """Retourne le fournisseur d'icônes global."""
    return _icon_provider


def set_icon_provider(provider: IconProvider) -> None:
    """Définit le fournisseur d'icônes global."""
    global _icon_provider
    _icon_provider = provider


def get_icon(name: str, color: str | None = None) -> QIcon:
    """Raccourci pour obtenir une icône.

    Args:
        name: Nom de l'icône
        color: Couleur optionnelle

    Returns:
        QIcon ou icône vide si provider non initialisé
    """
    if _icon_provider is None:
        return QIcon()
    return _icon_provider.get_icon(name, color)
