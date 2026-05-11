"""AOM (Ansible Output Monitor) - nom-style terminal interface for ansible-playbook.

See SPECIFICATION.md for full details.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

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
