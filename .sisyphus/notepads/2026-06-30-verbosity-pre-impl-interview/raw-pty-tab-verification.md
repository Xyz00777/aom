# Raw PTY Tab Verification: Does `aom inspect <sid>` surface full `stderr.log`?

## 1. Does the inspect TUI have a tab/panel/section that shows `stderr.log` content?

**No. There is no "Raw PTY" tab, no stderr tab, and no session-wide stderr panel in the inspect TUI.**

The inspect TUI (`src/ansible_aom/tui/screens/inspect.py`) is a **three-pane layout** (Runs | Tasks | Detail), not a tabbed view:

- **Runs pane** (left): `ListView` of sessions
- **Tasks pane** (middle): `Tree` of plays → groups → tasks → hosts
- **Detail pane** (right): `RichLog` showing per-(task, host) detail

There are no tabs. The Detail pane is a single `RichLog` widget (`_DetailLog`, line 328) that shows only **per-task, per-host** information. The code explicitly acknowledges this gap:

```python
# Line 796-802 in src/ansible_aom/tui/screens/inspect.py
def _render_detail_block(self, block: DetailBlock) -> str:
    """Render the per-task detail body.

    Everything here is specific to the focused (task, host) pair —
    session-wide content (the session ``stderr.log``) belongs in a
    separate view, not under each task, because re-rendering the same
    text on every cursor move was confusing.
    """
```

The `DetailBlock` model (`src/ansible_aom/core/inspect_model.py`, line 522-544) also confirms this:

```python
# Line 522-529 in src/ansible_aom/core/inspect_model.py
@dataclass(frozen=True)
class DetailBlock:
    """Right-pane data for a focused (task, host) pair.

    Everything here is *per task × host*. Session-wide info
    (``stderr.log``, overall stats) belongs elsewhere — including the
    session stderr in this block was confusing because it didn't change
    when navigating between tasks.
    """
```

The `build_detail_block` function (line 574) explicitly discards the session parameter:

```python
# Line 585-588 in src/ansible_aom/core/inspect_model.py
def build_detail_block(
    session: dict,
    task_node: TaskTreeNode,
    host_node: TaskTreeNode | None,
) -> DetailBlock:
    del session  # session-wide content lives elsewhere now
```

## 2. If yes: how is it loaded? Is it the full content, or truncated? Is there a flag to enable it, or is it always visible?

**N/A — the tab does not exist.**

## 3. If no: where does `stderr.log` content go? Is it accessible at all via `aom inspect`? What command/flag would surface it?

### In the TUI (`aom inspect <sid>` — no flags)

**The full `stderr.log` content is NOT accessible.** The TUI only shows per-task `module_stderr` (the stderr output of individual Ansible modules, captured in the JSONL event's `hosts.<host>.stderr` / `hosts.<host>.module_stderr` field). This is **not** the same as `stderr.log`, which contains:

- Ansible warnings (`[WARNING]: ...`)
- Preflight errors
- SSH debug output (when `-vvvv` is used)
- Callback loading messages
- Connection lock messages
- Any other stderr emitted by `ansible-playbook` outside the JSONL stream

### In the text mode (`aom inspect --text`)

**Only a 20-line tail of `stderr.log` is shown, and only for failed sessions.**

```python
# Lines 152-168 in src/ansible_aom/inspect/text.py
def _render_stderr_tail(session: dict, max_lines: int = 20) -> list[str]:
    tail: list[str] = (session.get("stderr") or [])[-max_lines:]
    if not tail:
        return []
    return ["stderr.log (tail)", "─" * 17, *tail]


def render_session(session: dict) -> str:
    # ...
    if summary.status == "failed":
        parts.append("")
        parts.extend(_render_stderr_tail(session))
    return "\n".join(parts) + "\n"
```

Key observations:
- **Truncated**: Only the last 20 lines (`max_lines=20`).
- **Conditional**: Only shown when `summary.status == "failed"`. Successful sessions get zero stderr content.
- **No flag to increase**: There is no `--show-stderr` or `--full-stderr` flag.

### In the CLI (`aom inspect --debug`)

The `--debug` flag shows `diagnostics.json` content, which includes a `pty_bytes` counter but **not the actual stderr content**:

```python
# Lines 114-123 in src/ansible_aom/inspect/formatters.py
for key in (
    "events_received",
    "render_calls",
    "log_writes",
    "pty_bytes",
    "pexpect_timeouts",
    "stall_count_max",
):
    if key in counters:
        lines.append(f"  {key:<24} {counters[key]:>10}")
```

### How `stderr.log` is loaded

The session loader (`src/ansible_aom/session/store.py`, lines 759-763) loads the full stderr content into memory:

```python
# Lines 759-763 in src/ansible_aom/session/store.py
if stderr_file.exists():
    with open(stderr_file) as f:
        result["stderr"] = f.read().splitlines()
else:
    result["stderr"] = []
```

So `session["stderr"]` is a list of all lines — the data is available. It's just not surfaced in the TUI.

## 4. Code evidence (file path + line numbers)

| What | File | Lines |
|------|------|-------|
| TUI has no tabs — three-pane layout | `src/ansible_aom/tui/screens/inspect.py` | 1-31 (docstring), 548-556 (compose) |
| Detail pane is a single `RichLog` | `src/ansible_aom/tui/screens/inspect.py` | 328-351 (`_DetailLog` class) |
| Comment: stderr.log "belongs in a separate view" | `src/ansible_aom/tui/screens/inspect.py` | 800-802 |
| DetailBlock model: "session-wide info belongs elsewhere" | `src/ansible_aom/core/inspect_model.py` | 522-529 |
| `build_detail_block` discards session param | `src/ansible_aom/core/inspect_model.py` | 585-588 |
| Per-task `module_stderr` shown (not stderr.log) | `src/ansible_aom/tui/screens/inspect.py` | 840-843 |
| Text mode: only 20-line tail, only for failed | `src/ansible_aom/inspect/text.py` | 152-168 |
| Session loader reads full stderr.log | `src/ansible_aom/session/store.py` | 759-763 |
| stderr.log is recorded on disk | `src/ansible_aom/session/store.py` | 243-244, 314, 360-372 |
| Brainstorm claim (Q8=A): "Tabbed DetailBlock: ... Raw PTY" | `docs/brainstorms/2026-06-29-verbosity-handling.md` | 37 |
| Post-research decision: "Raw PTY tab must surface full stderr.log" | `docs/brainstorms/2026-06-30-verbosity-pre-impl-interview.md` | 33, 39 |

## 5. Verdict

**FAIL** — The full `stderr.log` content is **not accessible** via `aom inspect <sid>` with no flags.

| Access path | Shows stderr.log? | Details |
|-------------|-------------------|---------|
| `aom inspect <sid>` (TUI) | **No** | No tab, no panel, no keybind. Only per-task `module_stderr` in Detail pane. |
| `aom inspect --text` | **Partial** | Last 20 lines only, and only for failed sessions. |
| `aom inspect --debug` | **No** | Shows `pty_bytes` counter, not content. |
| `aom inspect --json` | **No** | Only with `--debug`, shows diagnostics.json. |

### What needs to happen

The brainstorm (Q8=A) and the post-research decision both assume a "Raw PTY" tab exists. It does not. Phase 4 (storage extension) and Phase 7 (inspect TUI) of the v1 plan both need to **create** this tab from scratch:

1. **Add a "Raw PTY" tab (or equivalent) to the inspect TUI Detail pane** that reads `session["stderr"]` (already loaded by `load_session`) and displays it in full.
2. **Add a `--show-stderr` / `--full-stderr` flag to `aom inspect --text`** (or increase the default 20-line tail to "all lines").
3. **Remove the `status == "failed"` gate** on the text-mode stderr tail — successful sessions may also have useful stderr content (warnings, SSH debug).

The data is already on disk at `~/.local/state/aom/sessions/<sid>/stderr.log` and already loaded into `session["stderr"]` by `load_session()`. The gap is purely in the UI layer.
