"""Architecture layering enforcement (ARCHITECTURE.md §7.8).

These tests parse every module under ``src/ansible_aom/`` for ``import``
statements (top-level *and* within function bodies, so lazy imports are
caught too) and assert the dependency rules described in
``ARCHITECTURE.md §1–2``:

* ``core/`` is the pure domain — it must not import any infrastructure
  package.
* ``drivers/`` is the EventSource port side; it may depend on ansible/,
  session/, core/, renderer/ — but not on a concrete renderer
  (``compact``, ``tui``, ``formats``).
* ``renderer/protocol.py`` is the Renderer port; it must not import a
  concrete renderer. The factory may.
* ``compact``, ``tui``, ``formats`` are sibling concrete renderers and
  must not import each other.

Some modules listed below have not been relocated yet (see
``ARCHITECTURE.md §7.2``).  Where the *current* file path differs from
the *target* one, the test imports the module under both names so the
expectations can be updated atomically with each move.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "ansible_aom"
PACKAGE_PREFIX = "ansible_aom."


def _module_name_for(path: Path) -> str:
    rel = path.relative_to(SRC_ROOT).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(["ansible_aom", *parts])


def _imports_in(path: Path) -> set[str]:
    """Return every ansible_aom.* module name imported by ``path``.

    Walks the AST so lazy imports inside function bodies are captured —
    those are exactly the ones that hide layering bugs.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(PACKAGE_PREFIX) or alias.name == "ansible_aom":
                    found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue  # we don't use relative imports in this tree
            module = node.module or ""
            if module.startswith(PACKAGE_PREFIX) or module == "ansible_aom":
                found.add(module)
    return found


def _iter_modules(subpkg: str) -> list[Path]:
    base = SRC_ROOT / subpkg
    return [p for p in base.rglob("*.py") if p.name != "__init__.py" or p.parent != base]


def _violations(subpkg: str, forbidden_prefixes: tuple[str, ...]) -> list[tuple[str, str]]:
    bad: list[tuple[str, str]] = []
    base = SRC_ROOT / subpkg
    files = list(base.rglob("*.py"))
    for file in files:
        owner = _module_name_for(file)
        for imp in _imports_in(file):
            for prefix in forbidden_prefixes:
                if imp == prefix.rstrip(".") or imp.startswith(prefix):
                    bad.append((owner, imp))
                    break
    return bad


# ---------------------------------------------------------------------------
# core/ — pure domain
# ---------------------------------------------------------------------------


def test_core_does_not_depend_on_infrastructure() -> None:
    """``core/`` must not import any infrastructure package.

    This is the load-bearing invariant of the layer map. It is true on
    the current tree by inspection — this test exists to catch the
    first regression.
    """
    forbidden = (
        "ansible_aom.compact.",
        "ansible_aom.tui.",
        "ansible_aom.renderer.",
        "ansible_aom.ansible.",
        "ansible_aom.session.",
        "ansible_aom.drivers.",
        "ansible_aom.inspect.",
        "ansible_aom.rerun.",
        "ansible_aom.formats.",
        # Top-level infra modules still living at package root pre-§7.2.
        # Removed as each module relocates into its target subpackage.
        "ansible_aom.runner",
        "ansible_aom.replay",
        "ansible_aom.cli",
    )
    violations = _violations("core", forbidden)
    assert violations == [], (
        "core/ imported infrastructure: "
        + ", ".join(f"{src}→{dst}" for src, dst in violations)
    )


# ---------------------------------------------------------------------------
# renderer/ — port + factory
# ---------------------------------------------------------------------------


def test_renderer_protocol_does_not_import_concrete_renderers() -> None:
    """``renderer/protocol.py`` is the port; it must stay abstract."""
    forbidden = (
        "ansible_aom.compact.",
        "ansible_aom.tui.",
        "ansible_aom.formats.",
    )
    imports = _imports_in(SRC_ROOT / "renderer" / "protocol.py")
    bad = sorted({imp for imp in imports for p in forbidden if imp == p.rstrip(".") or imp.startswith(p)})
    assert bad == [], f"renderer/protocol.py must not depend on a concrete renderer; got {bad}"


# ---------------------------------------------------------------------------
# Concrete renderers must not import each other
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "subpkg, forbidden_siblings",
    [
        ("compact", ("ansible_aom.tui.", "ansible_aom.formats.")),
        ("tui", ("ansible_aom.compact.", "ansible_aom.formats.")),
    ],
)
def test_concrete_renderers_do_not_cross_import(
    subpkg: str, forbidden_siblings: tuple[str, ...]
) -> None:
    violations = _violations(subpkg, forbidden_siblings)
    assert violations == [], (
        f"{subpkg}/ imported a sibling renderer: "
        + ", ".join(f"{src}→{dst}" for src, dst in violations)
    )


# ---------------------------------------------------------------------------
# drivers/ — event-source port; not present yet pre-§7.1
# ---------------------------------------------------------------------------


def test_drivers_do_not_depend_on_concrete_renderers() -> None:
    """``drivers/`` couples to the Renderer Protocol, not to a concrete impl.

    The package may not exist yet on this branch — that's expected
    until §7.1 lands.  The test then trivially passes.
    """
    drivers_root = SRC_ROOT / "drivers"
    if not drivers_root.exists():
        pytest.skip("drivers/ package does not exist yet (§7.1 not landed)")
    forbidden = (
        "ansible_aom.compact.",
        "ansible_aom.tui.",
        "ansible_aom.formats.",
    )
    violations = _violations("drivers", forbidden)
    assert violations == [], (
        "drivers/ imported a concrete renderer: "
        + ", ".join(f"{src}→{dst}" for src, dst in violations)
    )
