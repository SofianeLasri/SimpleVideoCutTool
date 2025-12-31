"""Définitions des thèmes et palettes de couleurs.

Ce module contient les palettes de couleurs pour les thèmes
sombre et clair, inspirées du Fluent Design de Windows 11.
"""

from __future__ import annotations

from typing import Final


# Palette thème sombre (défaut)
DARK_PALETTE: Final[dict[str, str]] = {
    # Arrière-plans
    "background": "#1e1e1e",
    "background_secondary": "#252526",
    "surface": "#2d2d2d",
    "surface_hover": "#3a3a3a",
    "surface_pressed": "#404040",

    # Couleur d'accent (bleu Windows)
    "accent": "#0078d4",
    "accent_hover": "#1a86d9",
    "accent_pressed": "#006cbd",
    "accent_light": "#60cdff",

    # Texte
    "text_primary": "#ffffff",
    "text_secondary": "#b3b3b3",
    "text_disabled": "#6d6d6d",
    "text_on_accent": "#ffffff",

    # Bordures
    "border": "#3c3c3c",
    "border_strong": "#555555",
    "border_subtle": "#2d2d2d",

    # États sémantiques
    "success": "#4CAF50",
    "success_hover": "#45a049",
    "warning": "#FF9800",
    "warning_hover": "#f57c00",
    "error": "#f44336",
    "error_hover": "#d32f2f",
    "info": "#2196F3",

    # Éléments spécifiques
    "track": "#3c3c3c",
    "playhead": "#ffffff",
    "marker_a": "#2196F3",
    "region_default": "#4CAF50",
    "scrollbar": "#4a4a4a",
    "scrollbar_hover": "#5a5a5a",
}

# Palette thème clair
LIGHT_PALETTE: Final[dict[str, str]] = {
    # Arrière-plans
    "background": "#f3f3f3",
    "background_secondary": "#e8e8e8",
    "surface": "#ffffff",
    "surface_hover": "#f5f5f5",
    "surface_pressed": "#e8e8e8",

    # Couleur d'accent (bleu Windows)
    "accent": "#0078d4",
    "accent_hover": "#106ebe",
    "accent_pressed": "#005a9e",
    "accent_light": "#cce4f7",

    # Texte
    "text_primary": "#1a1a1a",
    "text_secondary": "#616161",
    "text_disabled": "#a0a0a0",
    "text_on_accent": "#ffffff",

    # Bordures
    "border": "#d1d1d1",
    "border_strong": "#a0a0a0",
    "border_subtle": "#e0e0e0",

    # États sémantiques
    "success": "#388e3c",
    "success_hover": "#2e7d32",
    "warning": "#f57c00",
    "warning_hover": "#ef6c00",
    "error": "#d32f2f",
    "error_hover": "#c62828",
    "info": "#1976d2",

    # Éléments spécifiques
    "track": "#e0e0e0",
    "playhead": "#1a1a1a",
    "marker_a": "#1976d2",
    "region_default": "#388e3c",
    "scrollbar": "#c0c0c0",
    "scrollbar_hover": "#a0a0a0",
}

# Couleurs des régions de coupe (partagées entre thèmes)
REGION_COLORS: Final[list[str]] = [
    "#4CAF50",  # Vert
    "#2196F3",  # Bleu
    "#FF9800",  # Orange
    "#9C27B0",  # Violet
    "#00BCD4",  # Cyan
    "#E91E63",  # Rose
]

# Paramètres de style Fluent
FLUENT_RADIUS_SMALL: Final[int] = 4
FLUENT_RADIUS_MEDIUM: Final[int] = 6
FLUENT_RADIUS_LARGE: Final[int] = 8

FLUENT_SPACING_SMALL: Final[int] = 4
FLUENT_SPACING_MEDIUM: Final[int] = 8
FLUENT_SPACING_LARGE: Final[int] = 16

# Police par défaut
FONT_FAMILY: Final[str] = "Segoe UI, sans-serif"
FONT_FAMILY_MONO: Final[str] = "Consolas, 'Courier New', monospace"
FONT_SIZE_SMALL: Final[int] = 11
FONT_SIZE_NORMAL: Final[int] = 13
FONT_SIZE_LARGE: Final[int] = 15
