# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\clark\\Desktop\\LOC_COMPILE\\LOC_COMPILE\\main.py'],
    pathex=[],
    binaries=[('C:\\Users\\clark\\anaconda3\\envs\\AUTO_RT\\DLLs\\_tkinter.pyd', '.'), ('C:\\Users\\clark\\anaconda3\\envs\\AUTO_RT\\Library\\bin\\tcl86t.dll', '.'), ('C:\\Users\\clark\\anaconda3\\envs\\AUTO_RT\\Library\\bin\\tk86t.dll', '.')],
    datas=[],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.scrolledtext', '_tkinter'],
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
    a.binaries,
    a.datas,
    [],
    name='LOC_COMPILE_tkfix_20250530_141546',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
