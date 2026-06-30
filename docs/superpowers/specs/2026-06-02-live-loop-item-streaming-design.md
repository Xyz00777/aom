# Live per-item loop streaming

**Status:** design approved 2026-06-02
**Scope:** callback plugin + compact renderer + TUI task tree + history totals + inspect counting safety

## Problem

When a host iterates over a loop (`with_items`, `loop:`, `community.general.homebrew`
over many formulae, etc.), AOM shows nothing until the **entire loop finishes**, then
dumps every per-item line at once. The user cannot see progress mid-loop — a 40-item
loop looks identical to a wedged task until the very end.

### Root cause (confirmed)

`ansible.posix.jsonl` (which `runner.py` hard-codes as `ANSIBLE_STDOUT_CALLBACK`)
**deliberately drops per-item events.** Its `__getattribute__` hook intercepts only:

```python
('v2_runner_on_ok', 'v2_runner_on_failed', 'v2_runner_on_unreachable', 'v2_runner_on_skipped')
```

The per-item hooks — `v2_runner_item_on_ok/failed/skipped` — fall through to
`CallbackBase`, whose implementations are **no-ops**. So during a loop, ansible fires
those item hooks in real time, but the jsonl callback writes nothing. The only thing
that reaches AOM is the single aggregate `v2_runner_on_ok` event at the very end,
carrying the full `results[]` array.

Commit `0318fa8` ("render per-item loop results in streaming log") is therefore **not**
streaming — it splits the *end-of-loop* aggregate into per-item lines that all appear at
once. The data to do better is simply not on the wire.

ansible's **default** stdout callback implements `v2_runner_item_on_ok`, which is why
plain `ansible-playbook` streams loop items live. We need the same data.

## Goal

Show each loop item **as it completes**, everywhere AOM renders:

1. **Compact streaming log** — one line per item, live (the core ask).
2. **TUI task tree** — a count on the looped task row (`3/12`, or `(3 items)` when the
   total is unknown). Nothing fancier.
3. **`aom inspect` replay** — replays show the same live ordering as the live run.

### Out of scope

- Per-item duration timing (ansible doesn't time individual items; the per-task summary
  still reports total wall time).
- Any change to non-looped task rendering — must be byte-for-byte unchanged.
- Mid-loop progress for modules that don't emit item events (some custom modules); we
  render whatever item events arrive and fall back gracefully.

## Architecture

Five components. Each lands and is testable independently; they share one event schema.

```
ansible subprocess                          AOM process
──────────────────                          ───────────
aom_jsonl callback  ──JSONL──▶  PtyStreamParser ──▶ renderer (compact)
  (subclass of                                 └──▶ TreeProjection (TUI)
   ansible.posix.jsonl)                         └──▶ session sink ──▶ inspect replay
  + v2_runner_item_on_ok/failed/skipped
```

### Event schema (the contract)

Each item event reuses the **exact envelope** `ansible.posix.jsonl` already emits for
`v2_runner_on_ok`, so every existing consumer already knows the shape:

```json
{
  "_event": "v2_runner_item_on_ok",      // or _failed / _skipped
  "_timestamp": "<ISO 8601 UTC>",
  "task": { "name": ..., "id": "<uuid>", "path": "file.yml:NN", "duration": {...} },
  "hosts": { "<host>": { ...single item result..., "_ansible_item_label": ..., "item": ... } }
}
```

`hosts[host]` is **one item's** result (not an aggregate). The item label is
`_ansible_item_label` when ansible computed one, else the raw `item` value — identical to
`core.inspect_model._make_loop_item` and the renderer's existing `_loop_item_lines`.

**Invariant:** the aggregate `v2_runner_on_ok/failed` still arrives at loop end, intact,
carrying the full `results[]`. Item events are **additive**. The aggregate remains the
source of truth for final state. This is what keeps `inspect_model.build_detail_block`
and the bulk of `tree.py` unchanged.

## Component 1 — the callback plugin

New file `src/ansible_aom/ansible/callback/aom_jsonl.py` (under AOM's existing
GPL-3.0-or-later — no licensing concern, same license as the parent):

```python
from ansible_collections.ansible.posix.plugins.callback import jsonl

class CallbackModule(jsonl.CallbackModule):
    CALLBACK_NAME = 'aom_jsonl'   # matches filename; no dot (a dot implies an FQCN)

    def v2_runner_item_on_ok(self, result):     self._emit_item('v2_runner_item_on_ok', result)
    def v2_runner_item_on_failed(self, result):  self._emit_item('v2_runner_item_on_failed', result)
    def v2_runner_item_on_skipped(self, result): self._emit_item('v2_runner_item_on_skipped', result)

    def _emit_item(self, name, result):
        host, task = result._host, result._task
        item_result = result._result.copy()
        item_result['action'] = task.action
        task_result = self._find_result_task(host, task)   # reuse parent
        envelope = {
            'task': task_result['task'],
            'hosts': {host.name: item_result},
        }
        self._write_event(name, envelope)                  # reuse parent
```

It reuses the parent's `_write_event`, `_find_result_task`, schema, and
`AnsibleJSONEncoder`. It does **not** delete the `_task_map` entry or stamp a
task-duration end — the loop is still running; the parent's aggregate handler does that
when the loop finishes.

Strategy note: works under both linear and free strategies — the item hooks fire
regardless of `_is_lockstep`, and `_find_result_task` already handles both.

### Component 2 — runner wiring + packaging

`runner.py`:

```python
callback_dir = _bundled_callback_dir()   # via importlib.resources
if callback_dir is not None:
    env["ANSIBLE_CALLBACK_PLUGINS"] = str(callback_dir)
    env["ANSIBLE_STDOUT_CALLBACK"] = "aom_jsonl"
else:
    env["ANSIBLE_STDOUT_CALLBACK"] = "ansible.posix.jsonl"   # graceful fallback
```

- Ship the plugin as package data (`pyproject.toml` `[tool.hatch.build]` includes
  `src/ansible_aom/ansible/callback/`).
- **Graceful fallback:** if the bundled dir can't be resolved, fall back to plain
  `ansible.posix.jsonl` (today's behavior). A packaging glitch never breaks a run — it
  just loses live item streaming.

## Component 3 — compact renderer (the core ask)

In `CompactRenderer._emit_event_log`, add three branches for the item events. Refactor
the existing `_loop_item_lines` to expose a single-result formatter:

- `_format_loop_item_line(host, raw) -> str` — formats one item result
  (`ok/changed/failed/skipping: [host] => (item=<label>)`), the colour logic already in
  `_loop_item_lines`.
- On each `v2_runner_item_on_*` event → emit that one line immediately.

**Dedup (critical).** Track `self._streamed_loop_items: set[tuple[str, str]]` keyed by
`(host, task_id)`. On each item event, add the key. When the aggregate
`v2_runner_on_ok/failed` arrives:

- if `(host, task_id)` is in the set → **skip** the per-item expansion (already streamed
  live); the aggregate's own host line stays suppressed for loops as today.
- if **not** in the set (plugin fell back to plain jsonl, or module emitted no item
  events) → run the existing end-of-loop `_loop_item_lines` expansion unchanged.

This guarantees **full backward compatibility**: with plain jsonl, behavior is identical
to today; with `aom_jsonl`, items stream and the aggregate adds nothing per-item.

Register `v2_runner_item_on_ok/failed/skipped` as **known** event names so they never
appear in the renderer's `unknown_events` report.

## Component 4 — TUI task tree (count only)

`TaskRunState` (or the per-host run state) gains an item counter incremented on each
item event for that `(task, host)`. The looped task row renders:

- **`N/total`** when a total is known for that host (see Component 5).
- **`(N items)`** when no total is known, resolving to **`total/total`** once that
  host's aggregate event lands (`len(results)`).

Resolution is **per host** — each host's count and total are tracked independently
(hosts iterate loops at their own pace, especially under the free strategy).

`tree.py` counting safety: `StatusCounts.add_event` and the projection ingest must
**ignore** `v2_runner_item_on_*` for host/task status counting — the aggregate still
arrives and is the source of truth. Without this, items double-count. The item events
feed **only** the loop counter, not the ok/changed/failed tallies.

## Component 5 — loop totals from history (the `N/total` polish)

Today's `PriorRun` (`session/history.py`) carries only `task_count`, `host_count`,
`duration` — no per-task loop data, so totals can't come from it as-is. But the matched
prior session's full JSONL recording **is** on disk, and its aggregate events carry
`len(hosts[host].results)` per task per host.

Extend the prior-run lookup to also mine **loop totals**:

- New field on the prior-run payload: `loop_totals: dict[str, dict[str, int]]` keyed by
  `task_key -> {host -> item_count}`, where `task_key` is the task `path`
  (`file.yml:NN`) — stable across runs.
- Built by scanning the matched prior session's recorded `v2_runner_on_ok/failed`
  events for entries whose `hosts[host]` has a non-empty `results` array.
- The TUI projection consults `loop_totals[task_key][host]` to show `N/total` live.
- **Fallback per host:** if absent (first run, or loop length changed) → running count
  `(N items)`, then resolve to `total/total` at the aggregate.

The compact streaming log does **not** use totals — it just prints each item line as it
arrives.

## Inspect / replay

Item events are recorded by the session sink automatically (raw event passthrough), so
`aom inspect` **replays** them through the same renderer + projection — replay matches
live for free. `inspect_model.build_detail_block` is unchanged: it still builds
`LoopItem`s from the aggregate's `results[]`.

## Phased implementation plan

Each phase is independently testable and shippable.

1. **Plugin + schema** — write `aom_jsonl.py`; assert (integration test against real
   `ansible-playbook` over a loop fixture) that `v2_runner_item_on_*` JSONL lines are
   emitted with the documented envelope.
2. **Runner wiring + packaging** — bundle the plugin, wire the env vars with graceful
   fallback; test that the fallback path selects plain jsonl when the dir is missing.
3. **Compact streaming + dedup** — render item lines live; dedup against the aggregate;
   verify non-looped tasks and the plain-jsonl fallback path are byte-for-byte unchanged.
4. **TUI running count** — per-host counter, `(N items)` → `total/total` resolution;
   tree counting ignores item events (no double-count).
5. **History loop totals** — extend prior-run lookup with `loop_totals`; TUI shows
   `N/total` live when a prior run is matched, else falls back to phase 4 behavior.

## Testing

- **Unit (compact):** item event → one line; dedup suppresses aggregate expansion when
  items streamed; aggregate expansion still runs when no items streamed (fallback);
  non-looped tasks unaffected.
- **Unit (tree):** item events increment the per-host loop counter but do **not** change
  status counts; `(N items)` vs `N/total` rendering; per-host independence.
- **Unit (history):** `loop_totals` mined correctly from a recorded prior session;
  per-host keys; absent task_key → no total.
- **Integration (real ansible):** loop fixture emits item events; full pipeline streams
  them; `aom inspect` replay matches live ordering.
- **Regression:** plain-jsonl fallback path reproduces today's exact output.

## Open risks

- Plugin must import `ansible_collections.ansible.posix.plugins.callback.jsonl` at
  runtime inside the ansible env. If `ansible.posix` is absent, the plugin import fails
  and ansible errors at startup. Mitigation: the graceful fallback in Component 2 keys
  off resolving the bundled dir, not off whether the import will succeed — consider a
  preflight check that `ansible.posix` is installed (it already must be, since today's
  code depends on `ansible.posix.jsonl`).
- `task_key` by path assumes the playbook file:line is stable between the prior run and
  the current one. If the playbook changed, the total may be stale — acceptable, since
  it only affects the `N/total` display and resolves correctly at the aggregate anyway.
