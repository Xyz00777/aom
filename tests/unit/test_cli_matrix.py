"""Batch E item #9 — CLI matrix smoke.

Every subcommand's ``--help`` exits 0, and every documented mutual-exclusion
combo is rejected with a non-zero exit code and a stable error fragment.

These tests use ``subprocess`` to drive ``python -m ansible_aom`` so the
real argparse wiring is exercised end-to-end (no mocks, no internal API).

The subcommand and mutex lists below must be kept in sync with
``src/ansible_aom/cli.py`` and the ``inspect`` / ``replay`` / ``rerun``
sub-CLIs. If you add a new subcommand or mutex pair, add a row here.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

# Subcommand argv prefixes whose ``--help`` should exit 0.
# Empty list = top-level ``aom --help``.
_HELP_TARGETS: list[tuple[str, list[str]]] = [
    ("top-level", []),
    ("inspect", ["inspect"]),
    ("inspect-prune", ["inspect", "prune"]),
    ("replay", ["replay"]),
    ("rerun", ["rerun"]),
]


# Documented mutually-exclusive combos. Each row:
#   (label, argv-without-program, expected stderr fragment)
# Keep in sync with cli.py error messages and any argparse mutex groups.
_MUTEX_CASES: list[tuple[str, list[str], str]] = [
    (
        "tui+json",
        # --tui and --format must precede the playbook positional;
        # argparse REMAINDER consumes anything after the positional verbatim
        # and forwards it to ansible-playbook.
        ["--tui", "--format", "json", "site.yml"],
        "--tui and --format json are mutually exclusive",
    ),
    (
        "replay-compact+tui",
        ["replay", "abcd1234", "--compact", "--tui"],
        "not allowed with argument",
    ),
]


def _run_cli(argv: list[str]) -> subprocess.CompletedProcess[str]:
    """Spawn ``python -m ansible_aom <argv>`` and return the completed proc."""
    return subprocess.run(
        [sys.executable, "-m", "ansible_aom", *argv],
        capture_output=True,
        text=True,
        timeout=15,
    )


@pytest.mark.parametrize(("label", "argv"), _HELP_TARGETS, ids=[t[0] for t in _HELP_TARGETS])
def test_help_exits_zero(label: str, argv: list[str]) -> None:
    """Every documented subcommand's ``--help`` exits 0 with a usage banner."""
    result = _run_cli([*argv, "--help"])
    assert result.returncode == 0, (
        f"{label}: --help returned {result.returncode}, "
        f"stderr={result.stderr!r}, stdout={result.stdout[:200]!r}"
    )
    # argparse emits "usage:" on stdout for --help; case-insensitive match
    # because some custom usage strings start with "Usage:".
    assert "usage:" in result.stdout.lower(), (
        f"{label}: stdout missing 'usage:' banner, got {result.stdout[:200]!r}"
    )


@pytest.mark.parametrize(
    ("label", "argv", "fragment"), _MUTEX_CASES, ids=[c[0] for c in _MUTEX_CASES]
)
def test_mutex_rejected(label: str, argv: list[str], fragment: str) -> None:
    """Documented mutually-exclusive combos must reject with a useful message."""
    result = _run_cli(argv)
    assert result.returncode != 0, (
        f"{label}: expected non-zero exit, got 0. stdout={result.stdout[:200]!r}"
    )
    combined = result.stderr + result.stdout
    assert fragment in combined, (
        f"{label}: expected stderr fragment {fragment!r}, got stderr={result.stderr[:300]!r}"
    )
