"""Point d'entrée de Simple Video Cut Tool.

Ce module initialise l'application Qt et lance la fenêtre principale.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import NoReturn

# Configurer le path pour PyInstaller et le mode développement
if getattr(sys, 'frozen', False):
    # Mode exe PyInstaller
    _BASE_PATH: Path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    # Mode développement
    _BASE_PATH = Path(__file__).parent

if str(_BASE_PATH) not in sys.path:
    sys.path.insert(0, str(_BASE_PATH))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from utils.logging_config import setup_app_logging
from ui.main_window import MainWindow
from ui.theme import ThemeManager


def main() -> NoReturn:
    """Point d'entrée principal de l'application."""
    # Configurer le logging
    logger = setup_app_logging(debug="--debug" in sys.argv)
    logger.info("=== Démarrage de Simple Video Cut Tool ===")

    # Créer l'application Qt
    app: QApplication = QApplication(sys.argv)
    app.setApplicationName("Simple Video Cut Tool")
    app.setOrganizationName("SimpleVideoCut")
    app.setApplicationVersion("1.1.0")

    # Activer le support des hauts DPI
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Initialiser et appliquer le thème
    theme_manager = ThemeManager.instance()
    theme_manager.apply_initial_theme()
    logger.info(f"Thème appliqué: {theme_manager.current_theme}")

    # Créer et afficher la fenêtre principale
    window: MainWindow = MainWindow()
    window.show()

    logger.info("Application prête")

    # Boucle principale
    exit_code: int = app.exec()

    logger.info(f"=== Fermeture de l'application (code: {exit_code}) ===")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
