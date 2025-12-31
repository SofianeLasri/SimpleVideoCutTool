"""Générateur de styles QSS Fluent Design.

Ce module génère les feuilles de style Qt (QSS) pour reproduire
le style Fluent Design de Windows 11.
"""

from __future__ import annotations

from .theme_definitions import (
    FLUENT_RADIUS_SMALL,
    FLUENT_RADIUS_MEDIUM,
    FONT_FAMILY,
    FONT_FAMILY_MONO,
    FONT_SIZE_NORMAL,
    FONT_SIZE_SMALL,
)


def generate_stylesheet(palette: dict[str, str]) -> str:
    """Génère la feuille de style complète pour un thème.

    Args:
        palette: Dictionnaire des couleurs du thème

    Returns:
        Feuille de style QSS complète
    """
    return f"""
/* ========== BASE ========== */
QWidget {{
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_NORMAL}px;
    color: {palette['text_primary']};
    background-color: transparent;
}}

QMainWindow {{
    background-color: {palette['background']};
}}

/* ========== BOUTONS ========== */
QPushButton {{
    background-color: {palette['surface']};
    color: {palette['text_primary']};
    border: 1px solid {palette['border']};
    border-radius: {FLUENT_RADIUS_SMALL}px;
    padding: 6px 16px;
    min-height: 28px;
}}

QPushButton:hover {{
    background-color: {palette['surface_hover']};
    border-color: {palette['border_strong']};
}}

QPushButton:pressed {{
    background-color: {palette['surface_pressed']};
}}

QPushButton:disabled {{
    background-color: {palette['background_secondary']};
    color: {palette['text_disabled']};
    border-color: {palette['border_subtle']};
}}

/* Bouton accent (primary) */
QPushButton[accent="true"] {{
    background-color: {palette['accent']};
    color: {palette['text_on_accent']};
    border-color: {palette['accent']};
}}

QPushButton[accent="true"]:hover {{
    background-color: {palette['accent_hover']};
    border-color: {palette['accent_hover']};
}}

QPushButton[accent="true"]:pressed {{
    background-color: {palette['accent_pressed']};
    border-color: {palette['accent_pressed']};
}}

QPushButton[accent="true"]:disabled {{
    background-color: {palette['text_disabled']};
    border-color: {palette['text_disabled']};
}}

/* Bouton danger (destructif) */
QPushButton[danger="true"] {{
    background-color: {palette['error']};
    color: {palette['text_on_accent']};
    border-color: {palette['error']};
}}

QPushButton[danger="true"]:hover {{
    background-color: {palette['error_hover']};
    border-color: {palette['error_hover']};
}}

/* Bouton succès */
QPushButton[success="true"] {{
    background-color: {palette['success']};
    color: {palette['text_on_accent']};
    border-color: {palette['success']};
}}

QPushButton[success="true"]:hover {{
    background-color: {palette['success_hover']};
    border-color: {palette['success_hover']};
}}

/* ========== LABELS ========== */
QLabel {{
    background-color: transparent;
    color: {palette['text_primary']};
}}

QLabel[secondary="true"] {{
    color: {palette['text_secondary']};
}}

QLabel[success="true"] {{
    color: {palette['success']};
}}

/* ========== INPUTS ========== */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {palette['surface']};
    color: {palette['text_primary']};
    border: 1px solid {palette['border']};
    border-radius: {FLUENT_RADIUS_SMALL}px;
    padding: 6px 10px;
    min-height: 28px;
}}

QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {palette['border_strong']};
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {palette['accent']};
    border-width: 2px;
}}

QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
    background-color: {palette['background_secondary']};
    color: {palette['text_disabled']};
}}

/* ========== COMBOBOX ========== */
QComboBox {{
    background-color: {palette['surface']};
    color: {palette['text_primary']};
    border: 1px solid {palette['border']};
    border-radius: {FLUENT_RADIUS_SMALL}px;
    padding: 6px 10px;
    min-height: 28px;
}}

QComboBox:hover {{
    border-color: {palette['border_strong']};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {palette['text_secondary']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {palette['surface']};
    color: {palette['text_primary']};
    border: 1px solid {palette['border']};
    border-radius: {FLUENT_RADIUS_SMALL}px;
    selection-background-color: {palette['accent']};
    selection-color: {palette['text_on_accent']};
    outline: none;
}}

/* ========== CHECKBOX & RADIO ========== */
QCheckBox, QRadioButton {{
    background-color: transparent;
    color: {palette['text_primary']};
    spacing: 8px;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {palette['border_strong']};
    background-color: {palette['surface']};
}}

QCheckBox::indicator {{
    border-radius: {FLUENT_RADIUS_SMALL}px;
}}

QRadioButton::indicator {{
    border-radius: 9px;
}}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border-color: {palette['accent']};
}}

QCheckBox::indicator:checked {{
    background-color: {palette['accent']};
    border-color: {palette['accent']};
}}

QRadioButton::indicator:checked {{
    background-color: {palette['accent']};
    border-color: {palette['accent']};
}}

/* ========== SLIDER ========== */
QSlider::groove:horizontal {{
    background-color: {palette['track']};
    height: 4px;
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background-color: {palette['accent']};
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}

QSlider::handle:horizontal:hover {{
    background-color: {palette['accent_hover']};
}}

QSlider::sub-page:horizontal {{
    background-color: {palette['accent']};
    border-radius: 2px;
}}

/* ========== PROGRESS BAR ========== */
QProgressBar {{
    background-color: {palette['track']};
    border: none;
    border-radius: {FLUENT_RADIUS_SMALL}px;
    height: 6px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {palette['accent']};
    border-radius: {FLUENT_RADIUS_SMALL}px;
}}

/* ========== GROUPBOX ========== */
QGroupBox {{
    background-color: {palette['surface']};
    border: 1px solid {palette['border']};
    border-radius: {FLUENT_RADIUS_MEDIUM}px;
    margin-top: 12px;
    padding: 16px 12px 12px 12px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: {palette['surface']};
    color: {palette['text_primary']};
}}

/* ========== TEXTEDIT ========== */
QTextEdit, QPlainTextEdit {{
    background-color: {palette['surface']};
    color: {palette['text_primary']};
    border: 1px solid {palette['border']};
    border-radius: {FLUENT_RADIUS_SMALL}px;
    padding: 8px;
    font-family: {FONT_FAMILY_MONO};
    font-size: {FONT_SIZE_SMALL}px;
}}

QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {palette['accent']};
}}

/* ========== SCROLLBAR ========== */
QScrollBar:vertical {{
    background-color: transparent;
    width: 12px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {palette['scrollbar']};
    border-radius: 4px;
    min-height: 30px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {palette['scrollbar_hover']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background-color: transparent;
}}

QScrollBar:horizontal {{
    background-color: transparent;
    height: 12px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {palette['scrollbar']};
    border-radius: 4px;
    min-width: 30px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {palette['scrollbar_hover']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ========== MENU ========== */
QMenu {{
    background-color: {palette['surface']};
    color: {palette['text_primary']};
    border: 1px solid {palette['border']};
    border-radius: {FLUENT_RADIUS_MEDIUM}px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: {FLUENT_RADIUS_SMALL}px;
}}

QMenu::item:selected {{
    background-color: {palette['surface_hover']};
}}

QMenu::separator {{
    height: 1px;
    background-color: {palette['border']};
    margin: 4px 8px;
}}

/* ========== TOOLTIP ========== */
QToolTip {{
    background-color: {palette['surface']};
    color: {palette['text_primary']};
    border: 1px solid {palette['border']};
    border-radius: {FLUENT_RADIUS_SMALL}px;
    padding: 6px 10px;
}}

/* ========== STATUS BAR ========== */
QStatusBar {{
    background-color: {palette['background_secondary']};
    color: {palette['text_secondary']};
    border-top: 1px solid {palette['border']};
}}

QStatusBar::item {{
    border: none;
}}

/* ========== VIDEO WIDGET ========== */
QVideoWidget {{
    background-color: #000000;
}}
"""


def generate_log_viewer_colors(palette: dict[str, str]) -> dict[str, str]:
    """Génère les couleurs pour le log viewer.

    Args:
        palette: Dictionnaire des couleurs du thème

    Returns:
        Dictionnaire des couleurs par niveau de log
    """
    return {
        "INFO": palette["success"],
        "WARNING": palette["warning"],
        "ERROR": palette["error"],
        "DEBUG": palette["text_secondary"],
    }
