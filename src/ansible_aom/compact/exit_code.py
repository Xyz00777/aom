"""Backward-compat re-export shim for ``determine_exit_code``.

The canonical implementation lives in :mod:`ansible_aom.core.exit_code`.
This module is kept as a re-export so historical imports of
``ansible_aom.compact.exit_code.determine_exit_code`` (and the
``from ansible_aom.compact.renderer import determine_exit_code`` re-export
chain) continue to work. See ARCHITECTURE.md §7.3.
"""

from __future__ import annotations

from ansible_aom.core.exit_code import determine_exit_code  # noqa: F401
