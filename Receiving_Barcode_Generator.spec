# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['GUI.py'],
    pathex=[],
    binaries=[],
    datas=[('./resources', 'resources'), ('./documents/product_code_case.csv', './'), ('./logs', 'logs'), ('./.env', '.'), ('./.venv/Lib/site-packages/customtkinter', 'customtkinter'), ('./.venv/Lib/site-packages', 'site-packages'), ('./.venv/Lib/site-packages/PyMuPDF', 'PyMuPDF/'), ('./.venv/Lib/site-packages/barcode', 'barcode/')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Receiving_Barcode_Generator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['resources\\icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Receiving_Barcode_Generator',
)
