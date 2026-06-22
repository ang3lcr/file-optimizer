# FileOptimizer Pro — Build Spec para PyInstaller
# Uso: pyinstaller build.spec
# Genera el ejecutable en: dist/FileOptimizerPro/

from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from PyInstaller.building.datastruct import Tree
import sys
import os

block_cipher = None

# Datos adicionales a incluir
added_files = [
    ("assets", "assets"),
    ("logs", "logs"),
]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        # CustomTkinter
        "customtkinter",
        "customtkinter.windows",
        "customtkinter.windows.widgets",
        "customtkinter.windows.widgets.theme",
        # tkinterdnd2
        "tkinterdnd2",
        # pikepdf
        "pikepdf",
        "pikepdf._core",
        # PyMuPDF
        "fitz",
        # Pillow
        "PIL",
        "PIL._imaging",
        "PIL.Image",
        "PIL.JpegImagePlugin",
        "PIL.PngImagePlugin",
        "PIL.WebPImagePlugin",
        # Office
        "docx",
        "openpyxl",
        "pptx",
        # Reportlab
        "reportlab",
        "reportlab.graphics",
        "reportlab.platypus",
        "reportlab.lib",
        # Estándar
        "sqlite3",
        "json",
        "zipfile",
        "xml.etree.ElementTree",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "test",
        "unittest",
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
    name="FileOptimizerPro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,              # Sin consola (app de escritorio)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/logo.ico",     # Ícono (crear en assets/)
    version_file=None,
    uac_admin=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="FileOptimizerPro",
)
