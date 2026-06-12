"""The bundled aom.interactive collection is laid out where ansible expects."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1].parent / "src" / "ansible_aom" / "ansible" / "collections"


def test_collection_files_present():
    base = _ROOT / "ansible_collections" / "aom" / "interactive"
    assert (base / "galaxy.yml").is_file()
    assert (base / "plugins" / "action" / "confirm.py").is_file()
    assert (base / "plugins" / "modules" / "confirm.py").is_file()


def test_action_plugin_is_stdlib_only():
    src = (
        _ROOT / "ansible_collections" / "aom" / "interactive" / "plugins" / "action" / "confirm.py"
    ).read_text()
    # Must not import the aom package (runs inside ansible's interpreter).
    assert "import ansible_aom" not in src
    assert "from ansible_aom" not in src
