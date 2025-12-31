# -*- mode: python ; coding: utf-8 -*-
"""Configuration PyInstaller pour Simple Video Cut Tool.

Pour construire l'exécutable:
    pyinstaller simple_video_cut.spec

Pour un build one-file:
    pyinstaller --onefile simple_video_cut.spec
"""

import sys
from pathlib import Path

# Chemin du projet
PROJECT_ROOT = Path(SPECPATH)

block_cipher = None

a = Analysis(
    [str(PROJECT_ROOT / 'src' / 'main.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        # FFmpeg binaires
        (str(PROJECT_ROOT / 'ffmpeg' / 'ffmpeg.exe'), 'ffmpeg'),
        (str(PROJECT_ROOT / 'ffmpeg' / 'ffprobe.exe'), 'ffmpeg'),
    ],
    hiddenimports=[
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SimpleVideoCut',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Pas de console Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon=str(PROJECT_ROOT / 'resources' / 'icons' / 'app_icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SimpleVideoCut',
)
