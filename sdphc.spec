# -*- mode: python ; coding: utf-8 -*-
#run pyinstaller --workpath C:\sdphc_output\build --distpath C:\sdphc_output\dist --clean sdphc.spec
a = Analysis(
    ['./app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
    ('./app/assets','assets'),
    ('./settings.txt','settings.txt')
    ],
    hiddenimports=[
        'fiona',
        'shapely',
        'rtree',
        'geopandas',
        'pyproj',
        'pandas',
        'numpy',],
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
    name='sdphc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon='./app/assets/icons/windows.ico',  
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='sdphc',
)
