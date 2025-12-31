"""Package de gestion des thèmes.

Ce package fournit le système de thèmes Fluent Design
avec support pour les modes sombre et clair.
"""

from __future__ import annotations

from .theme_manager import ThemeManager
from .theme_definitions import (
    DARK_PALETTE,
    LIGHT_PALETTE,
    REGION_COLORS,
    FLUENT_RADIUS_SMALL,
    FLUENT_RADIUS_MEDIUM,
    FLUENT_RADIUS_LARGE,
)
from .icons import (
    IconProvider,
    get_icon,
    get_icon_provider,
    set_icon_provider,
    ICON_MAP,
)

__all__ = [
    "ThemeManager",
    "DARK_PALETTE",
    "LIGHT_PALETTE",
    "REGION_COLORS",
    "FLUENT_RADIUS_SMALL",
    "FLUENT_RADIUS_MEDIUM",
    "FLUENT_RADIUS_LARGE",
    "IconProvider",
    "get_icon",
    "get_icon_provider",
    "set_icon_provider",
    "ICON_MAP",
]
