"""AOM (Ansible Output Monitor) - nom-style terminal interface for ansible-playbook.

See SPECIFICATION.md for full details.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

__author__ = "Xyz00777"
__copyright__ = "Copyright 2026, Xyz00777"
__license__ = "GPL-3.0-or-later"

try:
    # Single source of truth: whatever pip / uv installed. Avoids the
    # two-source-of-truth bug where ``pyproject.toml`` got bumped but
    # this file stayed stale, leaving ``aom --version`` to lie about
    # the actually-installed code.
    __version__ = _pkg_version("ansible-aom")
except PackageNotFoundError:  # pragma: no cover - only hit before install
    # Running straight from a source checkout without ``pip install -e .``;
    # fall back to a sentinel so callers still get a string.
    __version__ = "0.0.0+unknown"
