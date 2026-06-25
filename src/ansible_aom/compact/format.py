"""Pure formatters for the compact renderer.

Every public function here takes domain types (``RunState``,
``TreeProjection``, lists of ``PlayDefinition``) plus terminal hints
(width, ascii_mode, colorize) and returns plain strings or string
lists. No I/O. No subprocess. No timer. No Rich Live.

Extracted from ``compact/renderer.py`` per ARCHITECTURE.md §7.3 so
the lifecycle class (CompactRenderer) can stay focused on Rich Live
orchestration. Snapshot tests in ``tests/compact/`` exercise these
functions directly.
"""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING

from ansible_aom.core.duration import format_age, format_duration_compact
from ansible_aom.core.heartbeat import LivenessState
from ansible_aom.core.icons import (
    STATUS_ICONS,
    STATUS_ICONS_ASCII,
    get_running_frame,
    get_status_color,
)
from ansible_aom.core.models import (
    PlayDefinition,
    RoleGroupDefinition,
    RunState,
    Status,
    TaskDefinition,
)
from ansible_aom.core.tree import TreeProjection

if TYPE_CHECKING:
    from ansible_aom.session.history import PriorRun

# =============================================================================
# ANSI color helpers
# =============================================================================
#
# Display writes raw bytes via ``sys.stdout.write``, so we embed SGR
# escape sequences directly rather than going through Rich's markup
# parser. Colors are gated on ``is_tty`` and the ``NO_COLOR`` env var
# (https://no-color.org) so non-TTY output (pipes, CI, redirected to
# file) and users who set NO_COLOR see plain ASCII.

_RESET = "\x1b[0m"
_DIM = "\x1b[2m"
_BOLD = "\x1b[1m"
_GREEN = "\x1b[32m"
_YELLOW = "\x1b[33m"
_RED = "\x1b[31m"
_MAGENTA = "\x1b[35m"
_CYAN = "\x1b[36m"


def _color_enabled(is_tty: bool) -> bool:
    """True if we should emit SGR codes — TTY only, NO_COLOR honored."""
    return is_tty and not os.environ.get("NO_COLOR")


def _wrap(text: str, code: str, colorize: bool) -> str:
    """``text`` wrapped in an SGR sequence, or plain ``text`` if not colorising."""
    if not colorize or not text:
        return text
    return f"{code}{text}{_RESET}"


_SGR_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_sgr(text: str) -> str:
    """Strip SGR escapes so visible-length comparisons are accurate."""
    return _SGR_RE.sub("", text)


def _truncate_visible(text: str, width: int, *, colorize: bool = False) -> str:
    """Truncate to `width` visible chars while preserving any open SGR
    state by appending RESET. SGR escapes are zero-width.

    `colorize=False` (the default) means the input string is plain ASCII
    with no SGR codes — in that mode the RESET is suppressed so the
    output stays pure ASCII (`NO_COLOR` / non-TTY contract).
    """
    if width <= 1:
        return text[:width]
    visible = 0
    out: list[str] = []
    i = 0
    while i < len(text) and visible < width - 1:
        if text[i] == "\x1b":
            j = text.find("m", i)
            if j == -1:
                break
            out.append(text[i : j + 1])
            i = j + 1
        else:
            out.append(text[i])
            visible += 1
            i += 1
    out.append("…")
    if colorize:
        out.append(_RESET)
    return "".join(out)


# R2: per-event ``msg`` cap for live-display lines. A task that does
# register-then-debug on a host returning multi-MB stdout would otherwise
# stall Rich's render thread; the full payload still lands in
# events.jsonl, so ``aom inspect show`` can dump the untruncated form.
_MSG_DISPLAY_CAP = 4096


def _truncate_msg(msg: str) -> str:
    """Cap a JSONL ``msg`` field for live display.

    The suffix includes the original byte length so the user knows how
    much was hidden — important for grep'ing the right session later.
    """
    if len(msg) <= _MSG_DISPLAY_CAP:
        return msg
    return f"{msg[:_MSG_DISPLAY_CAP]}…(truncated, {len(msg)} bytes)"


# ansible-playbook flags worth surfacing as a status-bar chip. Each
# entry pairs the flag aliases with the (label, colour) chip.
_MODE_FLAGS: tuple[tuple[frozenset[str], str, str], ...] = (
    (frozenset({"--check", "-C"}), "DRY RUN", _YELLOW),
    (frozenset({"--diff", "-D"}), "DIFF", _CYAN),
)


def _compute_mode_label(args: list[str], colorize: bool) -> str:
    """Render the status-bar mode chip(s) from ansible-playbook args.

    Multiple chips render space-joined (`DRY RUN DIFF`). Each chip is
    colour-wrapped only if ``colorize`` is True so non-TTY consumers
    still see the label without escape codes around it.

    The detection is conservative: only literal flag aliases (no
    ``--check=foo`` style suffixes — those don't exist for these
    flags in ansible-playbook) so a stray substring in some other
    arg can't trigger a false chip.
    """
    chips: list[str] = []
    args_set = set(args)
    for aliases, label, color in _MODE_FLAGS:
        if args_set & aliases:
            chips.append(_wrap(label, color, colorize))
    return " ".join(chips)


# =============================================================================
# Module-Level Formatting Functions
# =============================================================================


def format_status_bar(
    playbook: str,
    hosts_completed: int,
    hosts_total: int,
    warnings: int,
    deprecations: int,
    elapsed_seconds: float,
    tasks_completed: int = 0,
    tasks_total: int = 0,
    ascii_mode: bool = False,
    colorize: bool = False,
    mode_label: str = "",
    liveness: LivenessState | None = None,
    remaining_seconds: float | None = None,
) -> str:
    """Format the status bar for compact mode display.

    Args:
        playbook: Path to the playbook file.
        hosts_completed: Number of hosts that completed.
        hosts_total: Total number of hosts.
        warnings: Number of warnings encountered.
        deprecations: Number of deprecations encountered.
        elapsed_seconds: Elapsed time in seconds.
        tasks_completed: Tasks past PENDING/RUNNING. Suppressed when 0.
        tasks_total: Total tasks from preflight. Segment is omitted when 0
            (no preflight definitions, or only dynamic include_tasks).
        colorize: If True, segments are wrapped in SGR escape codes —
            playbook path dimmed, separators dimmed, completed
            host/task counters in green, warning glyph in yellow,
            deprecation glyph in magenta, elapsed dimmed. Off by
            default so the function stays pure-string and snapshot
            tests aren't disturbed.

    Returns:
        Formatted status bar string. Task segment included only when
        ``tasks_total > 0``::

            "playbook │ X/Y hosts │ A/B tasks │ ⚠ N ✱ N │ H:MM:SS"

    Example:
        >>> format_status_bar("site.yml", 3, 10, 2, 1, 323)
        'site.yml │ 3/10 hosts │ ⚠ 2 ✱ 1 │ 0:05:23'
    """
    elapsed_int = int(elapsed_seconds)
    elapsed_h = elapsed_int // 3600
    elapsed_m = (elapsed_int % 3600) // 60
    elapsed_s = elapsed_int % 60
    elapsed_str = f"{elapsed_h}:{elapsed_m:02d}:{elapsed_s:02d}"

    sep_glyph = "|" if ascii_mode else "│"
    warn_glyph = "!" if ascii_mode else "⚠"
    deprec_glyph = "*" if ascii_mode else "✱"

    # Counter colouring: green only when the run is in fact complete
    # (X==Y and at least one). Stays default otherwise to avoid
    # nagging the user with progress hues during a normal in-flight run.
    hosts_seg = f"{hosts_completed}/{hosts_total} hosts"
    if hosts_total > 0 and hosts_completed == hosts_total:
        hosts_seg = _wrap(hosts_seg, _GREEN, colorize)

    parts = []
    if mode_label:
        # Mode chip(s) sit before the playbook path so the user sees
        # them immediately even on a narrow terminal that truncates
        # later segments. The caller renders the chip with its own
        # colour (yellow for DRY RUN, cyan for DIFF) — we don't
        # re-style here so a no-colour run gets a plain ``DRY RUN``.
        parts.append(mode_label)
    parts.extend([_wrap(playbook, _DIM, colorize), hosts_seg])

    if tasks_total > 0:
        tasks_seg = f"{tasks_completed}/{tasks_total} tasks"
        if tasks_completed == tasks_total:
            tasks_seg = _wrap(tasks_seg, _GREEN, colorize)
        parts.append(tasks_seg)

    if warnings > 0:
        parts.append(_wrap(f"{warn_glyph} {warnings}", _YELLOW, colorize))
    if deprecations > 0:
        parts.append(_wrap(f"{deprec_glyph} {deprecations}", _MAGENTA, colorize))

    if liveness is not None:
        # Hug the preceding segment (no separator pipe) so it reads as
        # an annotation on it rather than a peer counter. ``parts`` is
        # never empty here — at minimum the hosts segment is present.
        live_glyph_unicode = {"live": "●", "working": "○", "stuck": "!"}
        live_glyph_ascii = {"live": "*", "working": "o", "stuck": "!"}
        live_color = {"live": _GREEN, "working": _DIM, "stuck": _RED}
        glyph = (live_glyph_ascii if ascii_mode else live_glyph_unicode)[liveness.level]
        live_seg = _wrap(f"{glyph} {liveness.age_s}s", live_color[liveness.level], colorize)
        # Annotate non-default reasons so the user can tell *why* the
        # dot is the colour it is. ``pty`` on LIVE and ``stuck`` on
        # STUCK are the expected default cases and stay un-annotated to
        # keep the bar terse; the interesting cases (CPU-promoted LIVE,
        # silent WORKING, CPU-rescued WORKING past stuck) are tagged.
        annotated_reasons = {("live", "cpu"), ("working", "silent"), ("working", "cpu")}
        if (liveness.level, liveness.reason) in annotated_reasons:
            reason_seg = _wrap(f"({liveness.reason})", _DIM, colorize)
            live_seg = f"{live_seg} {reason_seg}"
        parts[-1] = f"{parts[-1]} {live_seg}"

    parts.append(_wrap(elapsed_str, _DIM, colorize))

    if remaining_seconds is not None:
        # Hug the elapsed segment (single space, no separator pipe) so the
        # ETA reads as an annotation on the clock — "elapsed, ~this much
        # left" — rather than a peer counter. Dimmed like elapsed itself.
        eta_seg = _wrap(f"~{format_duration_compact(remaining_seconds)} left", _DIM, colorize)
        # Two spaces (not one): with no separator pipe, the wider gap keeps
        # the ETA visually distinct from the elapsed clock it annotates.
        parts[-1] = f"{parts[-1]}  {eta_seg}"

    sep = _wrap(sep_glyph, _DIM, colorize)
    return f" {sep} ".join(parts)


def _format_count_cells(
    ok: int,
    changed: int,
    skipped: int,
    failed: int,
    unreachable: int,
    *,
    ascii_mode: bool,
    colorize: bool,
) -> list[str]:
    """Render non-zero status count cells.

    Order: ok, changed, skipped, failed, unreachable.

    Returned as a list of styled segments so callers can space-join or
    place them inside other layouts. Existing ``format_host_summary``
    behaviour is preserved by joining with a single space.
    """
    icons = STATUS_ICONS_ASCII if ascii_mode else STATUS_ICONS
    cells: list[str] = []
    if ok > 0:
        cells.append(_wrap(f"{icons[Status.OK]} {ok} ok", _GREEN, colorize))
    if changed > 0:
        cells.append(_wrap(f"{icons[Status.CHANGED]} {changed} changed", _YELLOW, colorize))
    if skipped > 0:
        cells.append(_wrap(f"{icons[Status.SKIPPED]} {skipped} skipped", _DIM, colorize))
    if failed > 0:
        cells.append(_wrap(f"{icons[Status.FAILED]} {failed} failed", _RED, colorize))
    if unreachable > 0:
        cells.append(
            _wrap(
                f"{icons[Status.UNREACHABLE]} {unreachable} unreachable",
                _MAGENTA,
                colorize,
            )
        )
    return cells


def _compute_tree_budget(rows: int, active_hosts: int) -> int:
    """Tree height budget in lines.

    Baseline ~½ of terminal rows; +1 line per 3 active hosts; clamped to
    [8, 40]. The tree shares the bottom panel with the status bar (1 line)
    and the host table (header + N host rows). For a 24-row terminal the
    baseline is 12, which fits the active play structure with its running
    hosts and shows several upcoming plays beyond.

    Previous formula (`rows // 3`, max 25) gave only 8 lines on a 24-row
    terminal — enough for 2–3 plays but not their tasks or host leaves.
    The larger budget lets the tree show deeper structure while the log
    area above still gets at least rows // 2 for streaming output.
    """
    return max(8, min(60, rows // 2 + active_hosts // 3))


def format_host_summary(
    hostname: str,
    ok: int,
    changed: int,
    skipped: int,
    failed: int,
    unreachable: int,
    ascii_mode: bool = False,
    colorize: bool = False,
) -> str:
    """Format a host summary line with status icons.

    Only includes non-zero counts in the output.

    Args:
        hostname: The hostname.
        ok: Number of OK tasks.
        changed: Number of changed tasks.
        skipped: Number of skipped tasks.
        failed: Number of failed tasks.
        unreachable: Number of unreachable tasks.
        ascii_mode: Use ASCII fallback glyphs (no Unicode).
        colorize: Wrap each status segment in its semantic SGR
            colour (ok=green, changed=yellow, skipped=dim,
            failed=red, unreachable=magenta). Hostname is dimmed.
            Off by default to keep the function pure-string for tests.

    Returns:
        Formatted host summary with icons: "hostname: ● N ok, ◆ M changed, ..."

    Example:
        >>> format_host_summary("web1", 12, 3, 1, 0, 0)
        'web1: ● 12 ok ◆ 3 changed ○ 1 skipped'
    """
    cells = _format_count_cells(
        ok,
        changed,
        skipped,
        failed,
        unreachable,
        ascii_mode=ascii_mode,
        colorize=colorize,
    )
    return " ".join([_wrap(f"{hostname}:", _DIM, colorize), *cells])


# --- Worst-status → SGR colour mapping for the hostname cell ---------------
# Failed hosts go red; unreachable magenta; changed yellow. OK/SKIPPED/PENDING
# stay default-foreground (the count cells already carry their own colour).
_HOSTNAME_COLOR_BY_WORST: dict[Status, str] = {
    Status.FAILED: _RED,
    Status.UNREACHABLE: _MAGENTA,
    Status.CHANGED: _YELLOW,
}


def format_host_rows(
    projection: TreeProjection,
    *,
    width: int,
    ascii_mode: bool = False,
    colorize: bool = False,
    animation_frame: int = 0,
) -> list[str]:
    """Render the per-host overview as a column-aligned table.

    Header row + one row per host. Columns:

        host  ok  changed  [skipped]  failed  [unreachable]  on

    The ``skipped`` and ``unreachable`` columns are omitted unless at
    least one host has a non-zero count — keeps the common case
    tight. Counts are right-aligned; hostname and ``on:`` suffix
    are left-aligned.
    """
    rows = projection.host_rows()
    if not rows:
        return []

    include_skipped = any(row.counts.get(Status.SKIPPED, 0) > 0 for row in rows)
    include_unreachable = any(row.counts.get(Status.UNREACHABLE, 0) > 0 for row in rows)

    # Column widths: header label vs widest value, whichever is longer.
    hostname_width = max(len("host"), *(len(r.hostname) for r in rows))
    ok_width = max(len("ok"), *(len(str(r.counts.get(Status.OK, 0))) for r in rows))
    changed_width = max(len("changed"), *(len(str(r.counts.get(Status.CHANGED, 0))) for r in rows))
    skipped_width = (
        max(len("skipped"), *(len(str(r.counts.get(Status.SKIPPED, 0))) for r in rows))
        if include_skipped
        else 0
    )
    failed_width = max(len("failed"), *(len(str(r.counts.get(Status.FAILED, 0))) for r in rows))
    unreachable_width = (
        max(len("unreachable"), *(len(str(r.counts.get(Status.UNREACHABLE, 0))) for r in rows))
        if include_unreachable
        else 0
    )

    out: list[str] = []

    # --- Header ----------------------------------------------------------
    header_parts: list[str] = [
        f"{'host':<{hostname_width}}",
        f"{'ok':>{ok_width}}",
        f"{'changed':>{changed_width}}",
    ]
    if include_skipped:
        header_parts.append(f"{'skipped':>{skipped_width}}")
    header_parts.append(f"{'failed':>{failed_width}}")
    if include_unreachable:
        header_parts.append(f"{'unreachable':>{unreachable_width}}")
    header_parts.append("on")
    header_line = "  ".join(header_parts)
    if colorize:
        header_line = _wrap(header_line, _DIM, colorize)
    if len(_strip_sgr(header_line)) > width:
        header_line = _truncate_visible(header_line, width, colorize=colorize)
    out.append(header_line)

    # --- Data rows -------------------------------------------------------
    for row in rows:
        hostname_color = _HOSTNAME_COLOR_BY_WORST.get(row.worst_status or Status.OK)
        host_text = f"{row.hostname:<{hostname_width}}"
        host_seg = _wrap(host_text, hostname_color, colorize) if hostname_color else host_text

        cells = [
            _count_cell(
                row.counts.get(Status.OK, 0),
                width=ok_width,
                color=_GREEN,
                colorize=colorize,
            ),
            _count_cell(
                row.counts.get(Status.CHANGED, 0),
                width=changed_width,
                color=_YELLOW,
                colorize=colorize,
            ),
        ]
        if include_skipped:
            cells.append(
                _count_cell(
                    row.counts.get(Status.SKIPPED, 0),
                    width=skipped_width,
                    color=_DIM,
                    colorize=colorize,
                )
            )
        cells.append(
            _count_cell(
                row.counts.get(Status.FAILED, 0),
                width=failed_width,
                color=_RED,
                colorize=colorize,
            )
        )
        if include_unreachable:
            cells.append(
                _count_cell(
                    row.counts.get(Status.UNREACHABLE, 0),
                    width=unreachable_width,
                    color=_MAGENTA,
                    colorize=colorize,
                )
            )

        icons = STATUS_ICONS_ASCII if ascii_mode else STATUS_ICONS
        if row.current_task is not None:
            elapsed = int(row.current_elapsed_s or 0)
            glyph = get_running_frame(animation_frame)
            suffix = f"{row.current_task}  {_wrap(f'{glyph} {elapsed}s', _CYAN, colorize)}"
        elif row.failed_task is not None and row.failed_status == Status.FAILED:
            suffix = f"{icons[Status.FAILED]} {row.failed_task}"
            suffix = _wrap(suffix, _RED, colorize)
        elif row.failed_task is not None and row.failed_status == Status.UNREACHABLE:
            suffix = f"{icons[Status.UNREACHABLE]} {row.failed_task}"
            suffix = _wrap(suffix, _MAGENTA, colorize)
        elif row.worst_status == Status.UNREACHABLE:
            suffix = _wrap("unreachable", _MAGENTA, colorize)
        else:
            suffix = _wrap("(idle)", _DIM, colorize)

        line = "  ".join([host_seg, *cells, suffix])
        if len(_strip_sgr(line)) > width:
            line = _truncate_visible(line, width, colorize=colorize)
        out.append(line)

    return out


def _count_cell(value: int, *, width: int, color: str, colorize: bool) -> str:
    """Right-align ``value`` in a fixed-width cell; dim zero values.

    A literal zero painted in the count's normal colour fights with the
    hostname for attention even though it carries no information; dim
    the zero so the eye lands on actual non-zero outcomes.
    """
    text = f"{value:>{width}}"
    if value == 0:
        return _wrap(text, _DIM, colorize)
    return _wrap(text, color, colorize)


# Tree drawing glyphs. ASCII variants chosen to be unambiguous in plain
# terminals: "\-" is the last-child marker, "+-" is intermediate.
_TREE_LAST_UNICODE = "└─ "
_TREE_MID_UNICODE = "├─ "
_TREE_LAST_ASCII = "\\- "
_TREE_MID_ASCII = "+- "
# Vertical-spine continuation: drawn under non-last ancestors so the
# child's branch glyph connects visually to its parent. Plain spaces
# under a last ancestor (its subtree is the only one left at that depth,
# so no spine is needed).
_TREE_PIPE_UNICODE = "│  "
_TREE_PIPE_ASCII = "|  "
_TREE_GAP = "   "

# Map status-colour names (from core.icons.get_status_color) to SGR codes
# defined in this module. Keys must match the strings returned by
# get_status_color() exactly.
_COLOR_NAME_TO_SGR: dict[str, str] = {
    "green": _GREEN,
    "yellow": _YELLOW,
    "red": _RED,
    "magenta": _MAGENTA,
    "cyan": _CYAN,
    "dim": _DIM,
}


def format_tree_block(
    projection: TreeProjection,
    budget: int,
    *,
    width: int,
    ascii_mode: bool = False,
    colorize: bool = False,
    animation_frame: int = 0,
) -> list[str]:
    """Render the tree block as a list of lines.

    Returns an empty list when the projection says the tree should be
    hidden. The renderer caller stitches this list into the bottom panel.
    """
    if not projection.is_tree_visible():
        return []

    lines = projection.tree_lines(budget=budget)
    if not lines:
        return []

    # Determine "last child at depth D" by looking ahead: a line is the
    # last child of its parent if no following line at depth ≥ D-1 has
    # depth == D. We compute a parallel `is_last` list.
    is_last: list[bool] = []
    for i, ln in enumerate(lines):
        if ln.has_tail_after:
            # A "more tasks" footer follows this line at the same or
            # deeper depth. The renderer demotes this line's branch
            # glyph from └─ to ├─ and keeps the parent spine running,
            # so the cut is visually traceable from the top of the
            # window down to the footer.
            is_last.append(False)
            continue
        last = True
        for j in range(i + 1, len(lines)):
            if lines[j].depth < ln.depth:
                break
            if lines[j].depth == ln.depth:
                last = False
                break
        is_last.append(last)

    last_glyph = _TREE_LAST_ASCII if ascii_mode else _TREE_LAST_UNICODE
    mid_glyph = _TREE_MID_ASCII if ascii_mode else _TREE_MID_UNICODE
    pipe_glyph = _TREE_PIPE_ASCII if ascii_mode else _TREE_PIPE_UNICODE
    icons = STATUS_ICONS_ASCII if ascii_mode else STATUS_ICONS

    def _ancestor_chain_indent(idx: int) -> str:
        """Render the indent prefix for line ``idx`` as a chain of
        ``│  `` / ``   `` segments — one per ancestor depth (1..D-1).

        For each ancestor depth, walk backwards to the most recent line
        at that depth and consult its precomputed ``is_last`` flag. A
        non-last ancestor contributes the vertical spine; a last
        ancestor contributes plain spaces.
        """
        target = lines[idx]
        segments: list[str] = []
        for d in range(1, target.depth):
            ancestor_is_last = True
            for k in range(idx - 1, -1, -1):
                if lines[k].depth == d:
                    ancestor_is_last = is_last[k]
                    break
                if lines[k].depth < d:
                    break
            segments.append(_TREE_GAP if ancestor_is_last else pipe_glyph)
        return "".join(segments)

    out: list[str] = []
    for i, (ln, last) in enumerate(zip(lines, is_last)):
        indent = _ancestor_chain_indent(i)
        # Branch glyph: depth 0 has none; depth>0 normally has ├─ / └─ EXCEPT
        # host leaves under a task, which render as plain-indented children
        # (spec section "Tree leaf shape" — the user-approved preview shows
        # `   web1 ◐ 12s`, not `├─ web1 ◐ 12s`), and the "more tasks"
        # footers (inner + outer) which hang off the spine as leaves too.
        if ln.depth == 0:
            branch = ""
        elif ln.kind in ("host", "more"):
            branch = ""
        else:
            branch = last_glyph if last else mid_glyph

        # Per-line glyph (status icon for task/host/more footer; none for play/role).
        glyph_seg = ""
        if ln.kind in ("task", "host", "more") and ln.status is not None:
            if ln.status == Status.RUNNING and not ascii_mode:
                # get_running_frame returns a Unicode quadrant glyph; only
                # safe outside ASCII mode. ASCII mode falls through to the
                # plain icon map (which uses "@" for RUNNING).
                g = get_running_frame(animation_frame)
            else:
                g = icons.get(ln.status, "?")
            color_name = get_status_color(ln.status)
            color_code = _COLOR_NAME_TO_SGR.get(color_name, "")
            glyph_seg = (_wrap(g, color_code, colorize) + " ") if color_code else (g + " ")

        # Host leaves render as "<hostname> <glyph> <elapsed>s".
        if ln.kind == "host":
            elapsed = int(ln.elapsed_s or 0)
            label_seg = f"{ln.label} {glyph_seg}{_wrap(f'{elapsed}s', _DIM, colorize)}"
            text = f"{indent}{branch}{label_seg}"
        else:
            text = f"{indent}{branch}{glyph_seg}{ln.label}"

        if len(_strip_sgr(text)) > width:
            text = _truncate_visible(text, width, colorize=colorize)
        out.append(text)
    return out


def _count_role_group_tasks(group: RoleGroupDefinition) -> int:
    """Recursively count leaf tasks inside a ``RoleGroupDefinition``.

    ``RoleGroupDefinition.tasks`` may contain nested ``RoleGroupDefinition``
    entries (for nested roles), so this helper recurses into them.  It
    also applies the same parent-stub-skipping rule used at the play
    level: a ``TaskDefinition`` with non-empty ``.children`` is an
    ``include_tasks`` placeholder, not a leaf — only its children count.
    Plain leaf ``TaskDefinition`` entries count as 1.
    """
    total = 0
    for entry in group.tasks:
        if isinstance(entry, RoleGroupDefinition):
            total += _count_role_group_tasks(entry)
        elif isinstance(entry, TaskDefinition):
            if entry.children:
                total += len(entry.children)
            else:
                total += 1
        else:
            total += 1
    return total


def _count_tasks(play: PlayDefinition) -> int:
    """Count leaf TaskDefinitions in a play, expanding any RoleGroupDefinition.

    Dynamic ``include_tasks`` children are grafted onto their parent
    ``TaskDefinition`` at runtime via ``TaskDefinition.children``.  Such a
    parent stub is a placeholder, not a leaf — only its children count.
    Regular leaf ``TaskDefinition`` entries count as 1.  Nested
    ``RoleGroupDefinition`` entries are expanded recursively via
    ``_count_role_group_tasks`` so the status-bar denominator reflects
    the true total once dynamic tasks have expanded.
    """
    total = 0
    for entry in play.tasks:
        if isinstance(entry, RoleGroupDefinition):
            total += _count_role_group_tasks(entry)
        elif isinstance(entry, TaskDefinition):
            if entry.children:
                total += len(entry.children)
            else:
                total += 1
        else:
            total += 1
    return total


def count_total_tasks(definitions: list[PlayDefinition]) -> int:
    """Sum of leaf tasks across all preflight play definitions.

    Used for the status bar's `X/Y tasks` segment. Returns 0 for an empty
    list, which the renderer treats as "no preflight data — suppress the
    segment". Dynamic ``include_tasks`` children are counted when they
    have been grafted onto their parent ``TaskDefinition`` via
    ``TaskDefinition.children``; ``import_tasks`` are counted statically.
    """
    return sum(_count_tasks(play) for play in definitions)


def count_total_tasks_seen(definitions: list[PlayDefinition], state: RunState) -> int:
    """Running upper bound on task count for the status-bar denominator.

    Preflight ``--list-tasks`` only sees static + ``import_tasks``. Dynamic
    ``include_tasks`` expand at runtime so a playbook with 4 visible tasks
    may actually announce 30 once includes resolve. We take the maximum
    of the preflight total (including grafted children), the runtime
    announced count, and the include cache task count so the ratio
    ``completed / total`` never displays N > total.

    Before any runtime event arrives, falls back to the preflight count
    (avoids showing ``0/0`` during preflight).
    """
    runtime = sum(len(play.tasks) for play in state.plays.values())
    cached = sum(entry.task_count for entry in state._include_cache.values())
    return max(count_total_tasks(definitions), runtime, cached)


def count_completed_tasks(state: RunState) -> int:
    """Count tasks across all plays whose hosts have all reached terminal state.

    The state machine populates ``TaskRunState.hosts`` from two events:
    ``v2_runner_on_start`` (with ``status=RUNNING``) and the terminal
    handlers (ok / failed / skipped / unreachable, with the appropriate
    terminal status). A task counts as completed only when its hosts
    dict is non-empty AND no host is still in RUNNING — i.e. every host
    that began the task has produced a terminal result.

    For the status bar this is a monotonic, ansible-faithful progress
    signal: linear-strategy plays advance one task at a time, so the
    previous task's host results land before the next task starts.
    Multi-host free-strategy plays can briefly under-count while a
    fast-finishing host has its terminal event but its slower peer is
    still running — acceptable for a coarse indicator.
    """
    total = 0
    for play in state.plays.values():
        for task in play.tasks.values():
            if task.hosts and all(hs.status != Status.RUNNING for hs in task.hosts.values()):
                total += 1
    return total


def collect_tags(definitions: list[PlayDefinition]) -> list[str]:
    """Unique tags across every leaf TaskDefinition, alphabetically sorted.

    Used for the startup tag preview line. Expands ``RoleGroupDefinition``
    entries (including nested ones from role-in-role data) so tags inside
    role groups still surface.
    """
    seen: set[str] = set()
    for play in definitions:
        for entry in play.tasks:
            if isinstance(entry, RoleGroupDefinition):
                _collect_role_group_tags(entry, seen)
            else:
                seen.update(entry.tags)
    return sorted(seen)


def _collect_role_group_tags(group: RoleGroupDefinition, seen: set[str]) -> None:
    for inner in group.tasks:
        if isinstance(inner, RoleGroupDefinition):
            _collect_role_group_tags(inner, seen)
        else:
            seen.update(inner.tags)


def format_preflight_summary(
    definitions: list[PlayDefinition],
    *,
    prior_run: "PriorRun | None" = None,
) -> str | None:
    """Render a one-shot startup summary of plays/tasks/hosts from preflight.

    Printed once before any JSONL events flow, giving the user a sense
    of what's about to run — nom-style. Returns None for an empty list
    so the renderer can skip emitting it.

    Format::

        PLAY [Setup web servers] (webservers, 2 hosts, 3 tasks)
        PLAY [Setup database]    (dbservers, 1 host, 2 tasks)

    The bracketed name comes from the play's `name`. Host count uses
    `resolved_hosts` when populated; falls back to the raw `hosts`
    pattern when --list-hosts failed for that play.

    When ``prior_run`` is supplied (a completed session with matching
    run-config + host count, looked up by
    :func:`ansible_aom.session.history.find_previous_run`), a
    "Last run: N tasks in T (D ago)" line is appended below the
    per-play summary. ``None`` for ``prior_run`` means either no
    matching history exists, or the caller chose not to look one up —
    the line is silently omitted in both cases.
    """
    if not definitions:
        return None

    lines: list[str] = []
    for play in definitions:
        host_count = len(play.resolved_hosts)
        task_count = _count_tasks(play)

        if host_count > 0:
            host_part = f"{play.hosts}, {host_count} host" + ("s" if host_count != 1 else "")
        else:
            host_part = play.hosts or "0 hosts"

        task_part = f"{task_count} task" + ("s" if task_count != 1 else "")

        lines.append(f"PLAY [{play.name}] ({host_part}, {task_part})")

    tags = collect_tags(definitions)
    if tags:
        lines.append(f"Tags: {', '.join(tags)}")

    if prior_run is not None:
        tasks_word = "task" if prior_run.task_count == 1 else "tasks"
        lines.append(
            f"Last run: {prior_run.task_count} {tasks_word} in "
            f"{format_duration_compact(prior_run.duration_seconds)} "
            f"({format_age(prior_run.end_time)})"
        )

    return "\n".join(lines)


def format_failure_recap(state: RunState, colorize: bool = False) -> list[str]:
    """Build per-failure lines naming the host and task that went wrong.

    Returns one line per (host, task) pair that ended in FAILED or
    UNREACHABLE. Empty list when nothing failed — handle_completion uses
    that as a signal to suppress the recap section entirely.

    Format::

        FAILED: web2 — install nginx
        UNREACHABLE: db1 — gather facts

    With ``colorize=True``, the leading ``FAILED:`` / ``UNREACHABLE:``
    label is wrapped in the same colour the host summary uses for the
    matching count (red / magenta).
    """
    lines: list[str] = []
    for play in state.plays.values():
        for task in play.tasks.values():
            for hostname, host_state in task.hosts.items():
                if host_state.status == Status.FAILED:
                    label = _wrap("FAILED", _RED, colorize)
                    lines.append(f"{label}: {hostname} — {task.name}")
                elif host_state.status == Status.UNREACHABLE:
                    label = _wrap("UNREACHABLE", _MAGENTA, colorize)
                    lines.append(f"{label}: {hostname} — {task.name}")
    return lines
