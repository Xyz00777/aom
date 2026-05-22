# Tree view for the compact renderer

**Status:** design approved 2026-05-19
**Scope:** compact renderer only (TUI deferred). Behaviour is identical
under `strategy: linear` and `strategy: free`; the design is motivated by
`free` but does not branch on strategy.

## Problem

The compact renderer currently shows a single status bar plus the most
recent task header. Under `strategy: linear` that's fine — every host is
on the same task. Under `strategy: free`, hosts race ahead independently;
at any moment different hosts are on different tasks. The user cannot
see:

1. Which task each host is *currently* on.
2. How far ahead the leading hosts are vs. the laggards.
3. Where within the playbook/role/include hierarchy the active work
   sits.

The goal is a small bottom-of-terminal tree (nom-style) plus a
per-host summary table that together answer those questions at a glance,
without claiming a full-screen TUI.

## Goal

Add two new rendering segments under the status bar:

1. **Tree** — a transient hierarchical view of *currently running*
   playbook → play → role/include/import → task, with the running hosts
   listed as leaf lines under each task.
2. **Per-host summary** — one row per host showing cumulative
   per-status counts plus the task that host is on right now.

Both are visible only while at least one task is running. After
PLAY RECAP the tree disappears; the per-host summary collapses to its
counts.

Out of scope:

- Historical task-duration cache / `∅ estimated` column (deferred; line
  format leaves room — see `format_running_host_line` notes).
- Keybinds to hide/resize the tree in compact mode (compact is
  non-interactive; that belongs to `--tui`).
- Progress bars for per-task progress (no Ansible analogue to nom's
  byte transfers).
- TUI-mode rendering. The data structures defined here are reusable;
  wiring into the Textual app is deferred until the TUI is being
  touched.

## Architecture

Three layers, mirroring the existing `core/` vs infrastructure split.

```
state.py / parser.py                       ← infrastructure
   │ events update RunState (already wired)
   ▼
core/tree.TreeProjection                   ← pure logic, no I/O
   │ TreeProjection.from_run_state(state) → TreeProjection
   │ TreeProjection.host_rows()            → list[HostRow]
   │ TreeProjection.tree_lines(budget)     → list[TreeLine]
   ▼
compact/renderer.format_tree_block(...)    ← formats + colourises
compact/renderer.format_host_rows(...)     ← formats + colourises
```

`TreeProjection` lives in `core/` because pruning + ordering + status
derivation are pure transformations on `RunState`. No imports of
`compact/` or anything Textual. The renderer is the only thing that
knows about ANSI, glyph fallbacks, terminal width.

## Decision: tree leaf shape (PQ2 — host leaves under running tasks)

A running task shows all hosts as leaves with status-specific icons
(● OK, ◐ RUNNING, ○ SKIPPED, etc.). Completed tasks (no RUNNING hosts)
disappear from the tree entirely. Tasks where no host is currently
running are pruned.

```
site.yml
└─ play: deploy webservers
   └─ role: webserver
      └─ ◐ Install nginx  (1 ok, 2 running)
            web1 ◐ 12s
            web2 ◐  8s
```

Format strings:

```text
task line:      "{glyph} {task_name}  ({n_ok} ok[, {n_changed} changed]"
                "[, {n_running} running][, {n_failed} failed]"
                "[, {n_unreachable} unreachable][, {n_skipped} skipped])"
host child:     "  {hostname} {glyph} {elapsed}"
                # future: append " (∅ {estimate})" once historical cache
                # lands — leave this slot intentionally for that work.
```

The task line always shows the parenthesised summary; zero-count
statuses are omitted from inside it. An all-running task renders as
`(2 running)`; a partially-finished one as `(1 ok, 2 running)`. The
task glyph is the current `Status.RUNNING` animation frame (reusing
`get_running_frame`) because the task line only appears while the task
is running.

## Decision: per-host summary row (PQ3 — counts + current task, worst-status colour)

```
web1   ● 5  ◆ 2                on: Install nginx       ◐ 12s
web2   ● 3                       on: Configure firewall  ◐  5s
web3   ● 7                       (idle)
db1    ● 3              ⊝ 1     unreachable
web4   ● 2  ✖ 1                 on: Restart service     ◐  3s
```

Format:

```text
"{hostname}   {count_cells}   {current_task_suffix}"
```

- **hostname** coloured by *worst observed status seen on this host*:
  `FAILED → red`, `UNREACHABLE → magenta`, `CHANGED → yellow`, otherwise
  the default foreground (counts cells already carry their own colours,
  so green for an all-ok host stays implicit).
- **count_cells** reuses existing `_format_count_cells` semantics: only
  non-zero counts are emitted, each with its own colour. The `skipped`
  count is included (dim ○ icon), and the `skipped` column appears in
  the table only when any host has a non-zero skipped count.
- **current_task_suffix** is one of:
  - `on: <task name>  ◐ <elapsed>` — host is currently RUNNING a task
    (cyan, running animation frame for the glyph).
  - `(idle)` — host is between tasks (no active task, run is still
    going). Dim.
  - `unreachable` — host is in UNREACHABLE terminal state. Magenta.
  - empty — once the run has finished (after PLAY RECAP), suppress
    entirely.

The current-task suffix is the `free`-strategy payoff: a user looking at
five hosts can immediately see whether they are on the same task or
fanned out.

## Tree lifecycle

| Condition | Tree visible? | Host rows visible? | Tree content |
|---|---|---|---|
| Preflight / before first task | no | no | — |
| Any task RUNNING somewhere | **yes** | yes (if `host_count > 1`) | running tasks; only RUNNING hosts shown as leaves |
| Between fast-completing tasks (no host RUNNING, but playbook in flight) | **yes (sticky)** | yes (if `host_count > 1`) | most recently active task per play, with all its host leaves showing terminal status |
| PLAY RECAP done (`v2_playbook_on_stats`) | no | yes, but `on:` suffix suppressed | — |

**Sticky mode** (2026-05-20 amendment): under linear strategy especially,
fast tasks may finish before a render frame can fire, leaving the tree
to flicker on/off. To avoid this, the tree stays visible whenever the
playbook is in flight. When no task is currently RUNNING the tree falls
back to showing the most recently active task with all its host
leaves rendered at their terminal status — informative content during
the transient gap, no animation, no stale state once the next task
starts running (which immediately switches back to the running view).

Host rows display whenever the run targets more than one host (count
comes from preflight `--list-hosts`, not from "hosts seen in events so
far"); under a single-host run they're redundant with the tree and
status bar. This applies regardless
of strategy — `strategy: free` is detected from
`v2_playbook_on_play_start.strategy` if present, but the rendering is
not gated on it. The same code path renders both `linear` (typically
one task line with all hosts under it) and `free` (multiple task lines
with subsets of hosts).

## Height budget & pruning

The tree's vertical budget (lines available for tree content, excluding
the per-host summary, status bar, and surrounding blank lines):

```python
tree_budget = clamp(
    terminal_rows // 3 + active_host_count // 3,
    minimum=5,
    maximum=25,
)
```

- `active_host_count` = number of hosts whose state is `Status.RUNNING`
  *right now* (not total inventory, not "ever ran").
- Baseline `rows // 3` is nom's `targetRatio = 3`.
- `+ active_host_count // 3` scales modestly with concurrency: 12 hosts
  active in `free` adds +4 lines; 3 hosts adds +1.
- Clamp `[5, 25]`: 5 to stay usable on short terminals; 25 to keep the
  scrolling log dominant.

**Invariants the pruner must preserve:**

1. Every **active role** (a role that contains at least one task whose
   state is `Status.RUNNING` on at least one host) gets **≥ 1** visible
   line in the tree.
2. Every host currently RUNNING gets **≥ 1** visible line *somewhere*
   — either a tree leaf or its host-row's `on: ...` suffix. The host
   row counts toward satisfying this invariant, so when host rows are
   visible the tree pruner can collapse host leaves freely.

**Pruning order (drop lowest priority first when over budget):**

1. Collapse host children: keep the task line + its
   `(N ok, M running)` summary, drop individual host leaves.
2. Within a role with many running tasks, drop running tasks beyond the
   first N (each role keeps at least one task line — invariant 1).
3. Collapse a role into a single role-summary line of the form
   `└─ role: <name>  ({running_task_count} tasks running on
   {host_count} hosts)` — preserves invariant 1.

Failed and changed tasks are **not** pinned. Once a task is no longer
running anywhere, it leaves the tree; its outcome lives in the
per-host counts and (later) in the inspect/history view. This keeps the
tree a "what's happening right now" surface rather than a scrolling
recap.

Width:

- Task names: middle-truncate with `…` to fit `terminal_cols`.
- Hostnames: right-truncate with `…`. Hostname abbreviation
  (nom's collision-free algorithm, Print.hs L321–350) is a future
  enhancement, not in this design.

## Ordering & include/import handling

- Children render in **source order** — the order Ansible announced
  them in JSONL events. Not alphabetical.
- `import_tasks` is expanded by `--list-tasks`; preflight already gives
  us the structure. The tree can pre-shape itself even before the first
  task runs (though it stays hidden until a task is RUNNING).
- `include_tasks` is **not** in preflight. The first
  `v2_playbook_on_task_start` for an included task slots the node in
  under its including task. Once placed, the slot is stable.
- Role grouping uses the existing `RoleGroupDefinition`: tasks inside a
  role appear under a `role: <name>` branch.

## Data model: `core/tree.py`

```python
from dataclasses import dataclass
from ansible_aom.core.models import RunState, Status

@dataclass(frozen=True)
class TreeLine:
    depth: int                   # indentation level
    kind: Literal["playbook", "play", "role", "task", "host"]
    label: str                   # rendered text (pre-colour)
    glyph: str | None            # status icon, if any
    status: Status | None        # for colour selection
    elapsed_s: float | None      # for "◐ 12s" suffixes

@dataclass(frozen=True)
class HostRow:
    hostname: str
    counts: dict[Status, int]    # only non-zero entries
    worst_status: Status | None  # drives hostname colour
    current_task: str | None     # None → idle / done
    current_elapsed_s: float | None

class TreeProjection:
    @classmethod
    def from_run_state(cls, state: RunState) -> "TreeProjection": ...

    def is_tree_visible(self) -> bool: ...        # any task RUNNING?
    def is_host_summary_visible(self) -> bool: ...# host_count > 1 and run started
    def tree_lines(self, budget: int) -> list[TreeLine]: ...
    def host_rows(self) -> list[HostRow]: ...
```

No I/O, no ANSI. Everything is a pure function of `RunState`. Tests
exercise it by building `RunState` fixtures (already a common pattern
in `tests/unit/`) and asserting on the projection.

## Renderer integration: `compact/renderer.py`

Two new pure formatters alongside the existing `format_status_bar`:

```python
def format_tree_block(
    projection: TreeProjection,
    budget: int,
    *,
    width: int,
    ascii_mode: bool = False,
    colorize: bool = False,
) -> list[str]: ...

def format_host_rows(
    projection: TreeProjection,
    *,
    width: int,
    ascii_mode: bool = False,
    colorize: bool = False,
) -> list[str]: ...
```

`format_host_summary` (the existing function at `renderer.py:218`) gets
reused inside `format_host_rows` for the count-cells portion; the new
function wraps it with the worst-status hostname colour and the
`on: ...` suffix.

`CompactRenderer` (the live rendering driver) gains:

- One more region in the fixed bottom panel: status bar → tree block →
  host rows.
- Re-render trigger: existing tick path is sufficient; the projection
  is rebuilt each render. Cost is O(tasks × hosts), bounded by the
  budget — fine at 4 FPS.

The tree block + host rows count toward the bottom panel's line total
that the existing ANSI cursor-management logic tracks (the same logic
that already handles status-bar row count after the recent
`strip-ansi-before-row-count` fix in `12071de`).

## Status-icon colour mapping

Reuses the existing `STATUS_COLORS` table verbatim. No new colours are
introduced. Hostname-level colour selection picks one of the existing
status colours via the worst-status rule above.

## Testing

Pattern matches `tests/compact/` (snapshot tests against fixed terminal
output) and `tests/unit/` (projection logic).

- `tests/unit/test_tree_projection.py` — pure-data tests:
  - Empty `RunState` → tree invisible, host rows empty.
  - Single host, linear: one task line, one host leaf.
  - Three hosts, free, fanned out: three task lines, host leaves only
    under the task each host is on.
  - Pruning: budget=5 with 10 running tasks across 2 roles → invariant
    1 holds (each role keeps ≥1 line).
  - Pruning: collapsed-host case shows `(N ok, M running)` summary.
  - Worst-status selection per host.
  - `include_tasks` appears mid-run and slots correctly.
- `tests/compact/test_tree_render.py` — snapshot tests:
  - Tree visible + host rows together, fixed width.
  - ASCII fallback mode (no Unicode glyphs).
  - `colorize=False` path produces pure-string output (matches existing
    convention).
- Property-style coverage of the height clamp: random terminal sizes ×
  random host counts → budget always in `[5, 25]`.

## Open notes (deferred but signposted)

- The host-child line format `"  {hostname} {glyph} {elapsed}"` leaves
  room for `" (∅ {estimate})"` once the historical task-duration cache
  exists. The cache is its own design.
- Hostname abbreviation (nom Print.hs L321–350) is deferred; we
  right-truncate with `…` until host counts justify it.
- Once the TUI is being touched, `TreeProjection` should be the same
  type that feeds the Textual tree widget — no parallel data model.
