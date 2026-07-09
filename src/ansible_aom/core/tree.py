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

from collections import defaultdict

from ansible_aom.core.inspect_model import StatusCounts
from ansible_aom.core.models import RunState, Status
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
    "run_state_host_counts",
    "run_state_status_counts",
]


def _bump(counts: StatusCounts, status: Status) -> StatusCounts:
    if status == Status.OK:
        return StatusCounts(
            ok=counts.ok + 1,
            changed=counts.changed,
            failed=counts.failed,
            skipped=counts.skipped,
            unreachable=counts.unreachable,
        )
    if status == Status.CHANGED:
        return StatusCounts(
            ok=counts.ok,
            changed=counts.changed + 1,
            failed=counts.failed,
            skipped=counts.skipped,
            unreachable=counts.unreachable,
        )
    if status == Status.FAILED:
        return StatusCounts(
            ok=counts.ok,
            changed=counts.changed,
            failed=counts.failed + 1,
            skipped=counts.skipped,
            unreachable=counts.unreachable,
        )
    if status == Status.SKIPPED:
        return StatusCounts(
            ok=counts.ok,
            changed=counts.changed,
            failed=counts.failed,
            skipped=counts.skipped + 1,
            unreachable=counts.unreachable,
        )
    if status == Status.UNREACHABLE:
        return StatusCounts(
            ok=counts.ok,
            changed=counts.changed,
            failed=counts.failed,
            skipped=counts.skipped,
            unreachable=counts.unreachable + 1,
        )
    return counts


def run_state_status_counts(state: RunState) -> StatusCounts:
    counts = StatusCounts()
    for play in state.plays.values():
        for task in play.tasks.values():
            for host_state in task.hosts.values():
                if host_state.status == Status.RUNNING:
                    continue
                counts = _bump(counts, _effective_status(host_state))
    return counts


def run_state_host_counts(state: RunState) -> dict[str, StatusCounts]:
    host_counts: dict[str, StatusCounts] = defaultdict(StatusCounts)
    for play in state.plays.values():
        for task in play.tasks.values():
            for host, host_state in task.hosts.items():
                if host_state.status == Status.RUNNING:
                    continue
                host_counts[host] = _bump(host_counts[host], _effective_status(host_state))
    return {host: counts for host, counts in host_counts.items() if counts.total > 0}
