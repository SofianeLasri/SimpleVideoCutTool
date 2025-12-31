"""Point d'entrée de Simple Video Cut Tool.

Ce module initialise l'application Qt et lance la fenêtre principale.
"""

from __future__ import annotations

import sys
from typing import NoReturn

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from .utils.logging_config import setup_app_logging
from .ui.main_window import MainWindow


def main() -> NoReturn:
    """Point d'entrée principal de l'application."""
    # Configurer le logging
    logger = setup_app_logging(debug="--debug" in sys.argv)
    logger.info("=== Démarrage de Simple Video Cut Tool ===")

    # Créer l'application Qt
    app: QApplication = QApplication(sys.argv)
    app.setApplicationName("Simple Video Cut Tool")
    app.setOrganizationName("SimpleVideoCut")
    app.setApplicationVersion("1.0.0")

    # Activer le support des hauts DPI
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

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
