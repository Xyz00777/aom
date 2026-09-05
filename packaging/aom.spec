from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

root = Path(SPEC).resolve().parents[1]
package = root / "src" / "ansible_aom"

datas = [
    (str(package / "ansible" / "callback" / "aom_jsonl.py"), "ansible_aom/ansible/callback"),
    (str(package / "callbacks" / "aom_connection.py"), "ansible_aom/callbacks"),
    (str(package / "core" / "default_config.yaml"), "ansible_aom/core"),
]
datas.extend(copy_metadata("ansible-aom"))

a = Analysis(
    [str(package / "__main__.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="aom",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="aom",
)
