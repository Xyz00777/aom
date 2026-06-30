"""AOM (Ansible Output Monitor) - nom-style terminal interface for ansible-playbook.

See SPECIFICATION.md for full details.
"""

import hashlib
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path

__author__ = "Xyz00777"
__copyright__ = "Copyright 2026, Xyz00777"
__license__ = "GPL-3.0-or-later"

try:
    # Single source of truth: whatever pip / uv installed. Intentionally
    # the *installed* metadata even for editable installs — if it's
    # stale relative to the repo's pyproject.toml, the user wants to
    # SEE that mismatch (it's a signal to reinstall).
    #
    # Why editable installs go stale: ``uv tool install --editable .``
    # symlinks the source tree (so .py changes take effect live) but
    # writes a fixed copy of the package metadata at install time. The
    # ``.dist-info`` entry that ``importlib.metadata.version`` reads is
    # NOT updated when pyproject.toml changes. Bump → ``uv tool install
    # --reinstall --editable .`` to refresh.
    __version__ = _pkg_version("ansible-aom")
except PackageNotFoundError:  # pragma: no cover - only hit before install
    # Running straight from a source checkout without ``pip install -e .``;
    # fall back to a sentinel so callers still get a string.
    __version__ = "0.0.0+unknown"


def _compute_source_hash() -> str:
    """Short stable hash of every .py source file under the package.

    Companion to ``__version__``. The version comes from the installed
    metadata and can be stale relative to the live source (editable
    installs don't refresh ``.dist-info`` on file changes). The source
    hash, by contrast, is computed at call time from the actual files
    Python is importing — so if the user wonders "is my running aom
    actually the version I think it is?", comparing hashes against a
    known-good checkout answers it.

    Computed lazily on demand (``__version__`` is just a string at
    import time) so the hashing cost only hits when someone calls
    ``--version`` or reads ``source_hash()``. Skips ``__pycache__``,
    tests, and non-Python files. First 12 hex chars of SHA-256 —
    enough collision resistance for "did the source change?" with
    cheaper formatting than the full 64.
    """
    pkg_dir = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    # Sort paths so the hash is deterministic across filesystems with
    # different directory-iteration order.
    for path in sorted(pkg_dir.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            digest.update(path.read_bytes())
        except OSError:
            continue
    return digest.hexdigest()[:12]


def source_hash() -> str:
    """Public wrapper for ``_compute_source_hash``. Cached on first call."""
    global _CACHED_SOURCE_HASH
    if _CACHED_SOURCE_HASH is None:
        _CACHED_SOURCE_HASH = _compute_source_hash()
    return _CACHED_SOURCE_HASH


_CACHED_SOURCE_HASH: str | None = None
