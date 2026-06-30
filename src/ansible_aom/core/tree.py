r"""Re-export shim for :mod:`ansible_aom.core.tree_projection`.

All symbols have moved to ``core/tree_projection.py``. This module
re-exports them for backward compatibility. Import directly from
``core.tree_projection`` in new code.

Migration TODO: once every caller imports directly from
``ansible_aom.core.tree_projection``, this shim can be deleted.
Verify with:

    grep -rn 'from ansible_aom.core.tree ' src/ tests/
    grep -rn 'from ansible_aom.core import tree' src/ tests/
    grep -rn 'ansible_aom\.core\.tree\b' src/ tests/

When both return nothing, delete this file.
"""

from __future__ import annotations

from ansible_aom.core.tree_projection import (
    _ROW_LEASE_LIMIT,
    _ROW_LEASE_TTL,
    _TEMPLATE_RE,
    HostRow,
    TreeKind,
    TreeLine,
    TreeProjection,
    _collapse_role_path,
    _collapse_role_path_aggressive,
    _count_domain_entities,
    _effective_status,
    _host_leaf_label,
    _is_meta_task,
    _is_template_match,
    _more_footer,
    _name_role_chain,
    _play_target_hostnames,
    _RowLease,
    _template_skeleton,
    _truncate_two_level,
)

__all__ = [
    "HostRow",
    "TreeKind",
    "TreeLine",
    "TreeProjection",
    "_RowLease",
    "_TEMPLATE_RE",
    "_ROW_LEASE_LIMIT",
    "_ROW_LEASE_TTL",
    "_collapse_role_path",
    "_collapse_role_path_aggressive",
    "_count_domain_entities",
    "_effective_status",
    "_host_leaf_label",
    "_is_meta_task",
    "_is_template_match",
    "_more_footer",
    "_name_role_chain",
    "_play_target_hostnames",
    "_template_skeleton",
    "_truncate_two_level",
]
