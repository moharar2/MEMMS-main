import os
from PyInstaller.utils.hooks import collect_all

project_root = os.path.abspath(SPECPATH)
datas = [(os.path.join(project_root, 'src'), 'src')]
binaries = []
hiddenimports = ['src.models', 'src.models.user', 'src.models.role', 'src.models.equipment', 'src.models.work_order', 'src.models.preventive', 'src.models.inventory', 'src.models.contract', 'src.models.technician', 'src.models.hospital', 'src.models.audit', 'src.core.arabic_translations', 'sqlalchemy.dialects.sqlite']
tmp_ret = collect_all('qtawesome')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('sqlalchemy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='MEMMS',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MEMMS',
)
