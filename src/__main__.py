"""Permet l'exécution du package avec: python -m src"""

import sys
from pathlib import Path

# Configurer le path pour les imports absolus
_src_path: Path = Path(__file__).parent
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from main import main

if __name__ == "__main__":
    main()
