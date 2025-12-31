#!/usr/bin/env python3
"""Script de lancement pour le développement.

Utilisation:
    python run.py
    python run.py --debug
"""

import sys
from pathlib import Path

# Ajouter le dossier src au path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from main import main

if __name__ == "__main__":
    main()
