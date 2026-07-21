# build.spec
# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all necessary data files
datas = []

# Add Tesseract data files if available
tesseract_paths = [
    r'C:\Program Files\Tesseract-OCR',
    r'C:\Program Files (x86)\Tesseract-OCR',
    r'C:\Users\hp\AppData\Local\Programs\Tesseract-OCR',
]

for path in tesseract_paths:
    if os.path.exists(path):
        # Include tessdata
        tessdata_path = os.path.join(path, 'tessdata')
        if os.path.exists(tessdata_path):
            datas.append((tessdata_path, 'tessdata'))

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL._tkinter_finder',
        'cv2',
        'pytesseract',
        'mss',
        'numpy',
        'sqlite3',
        'json',
        'logging',
        'threading',
        'queue',
        'time',
        'random',
        'datetime',
        're',
        'pathlib',
        'tkinter',
        'src',
        'src.models',
        'src.views',
        'src.controllers',
        'src.ocr',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='RiskManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False for --windowed, True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path if you have one
)