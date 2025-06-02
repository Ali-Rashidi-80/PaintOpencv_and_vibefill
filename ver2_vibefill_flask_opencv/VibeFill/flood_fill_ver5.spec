# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['flood_fill_ver5.py'],
    pathex=[],
    binaries=[],
    datas=[('BNazanin.ttf', '.'), ('c:/Program Files/Python312/Lib/site-packages/mediapipe/modules', 'mediapipe/modules')],
    hiddenimports=['mediapipe', 'persiantools', 'arabic_reshaper', 'bidi.algorithm'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PySide6', 'kivy', 'kivymd', 'pygame', 'tensorflow', 'torch', 'pandas', 'sklearn', 'nltk', 'spacy', 'librosa', 'googleapiclient', 'scipy', 'sympy', 'lxml', 'numba', 'win32com', 'openpyxl', 'sqlalchemy', 'imageio', 'torchvision', 'onnxruntime', 'transformers', 'pydantic', 'anyio', 'orjson', 'timm', 'av', 'h5py', 'regex', 'soundfile', 'httplib2', 'Crypto', 'grpc', 'jupyterlab', 'gevent', 'zope.interface', 'babel', 'tinycss2', 'mistune'],
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
    name='flood_fill_ver5',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.jpg'],
)
