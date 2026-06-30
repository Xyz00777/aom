# Plan: Fix `--hide-state` hiding error message on failed loop items

## Bug

When running `aom --hide-state ok,skipped main.yml` against a playbook with a
`with_items` loop where one item fails, the failed item's error message is
silently dropped. The status panel shows `(1 failed)` but the log above shows
the failed item as `ok:` with no message:

```
TASK [Reconcile Firefly ownership on restore] ******
changed: [privatepodman] => (item=...)         ← changed items shown
changed: [privatepodman] => (item=...)         ← changed items shown
ok: [privatepodman] => (item=...)             ← FAILED item shown as "ok:"!
[time] Reconcile Firefly ownership on restore — 5.0s  (1 failed)
```

The same issue occurs for skipped items rendered as `ok:` (without `--hide-state`).

## Root cause

`CompactRenderer._format_loop_item_line(host, raw)` (in
`src/ansible_aom/compact/renderer.py`, ~line 1475) decides which prefix
(`failed:` / `skipping:` / `changed:` / `ok:`) to render by inspecting
`raw.get("failed")` / `raw.get("skipped")` / `raw.get("changed")`.

The `aom_jsonl` callback's per-item events (`v2_runner_item_on_failed`,
`v2_runner_item_on_skipped`) **do not** set `failed`/`skipped` flags on the
per-item payload — those flags only land on the *aggregate* host result
in the final `v2_runner_on_failed`/`v2_runner_on_ok` event after the loop
ends. So:

- `v2_runner_item_on_ok` payload → `changed: false` set → renders as `ok:` ✓
- `v2_runner_item_on_failed` payload → `failed` missing → renders as `ok:` ✗
- `v2_runner_item_on_skipped` payload → `skipped` missing → renders as `ok:` ✗

The aggregate path works correctly because the aggregate event's
`results[].failed` IS set. But once any item has been streamed live, the
aggregate path skips expansion for that host (dedup against
`_streamed_loop_items`), so the aggregate never gets a chance to re-render
the failed/skipped item correctly.

## Fix

`_format_loop_item_line` already takes `host` and `raw` as positional
args. Add an optional `event_type: str | None = None` parameter that, when
supplied, takes precedence over `raw.get(...)`. The streaming call sites
(`v2_runner_item_on_*` branch in `_emit_event_log`) pass the event's
`_event` so the per-item hook becomes the authoritative state signal.

The aggregate call site (`_loop_item_lines` → `_format_loop_item_line`)
keeps the current `event_type=None` path, which still works because the
aggregate's `results[].failed`/`results[].skipped` are correctly set.

## TODOs

- [x] Task 1: Write failing tests that reproduce both the user's scenario
      and the underlying skipped-item bug (TDD-first per AGENTS.md).
- [x] Task 2: Fix `_format_loop_item_line` to accept `event_type` and use
      it as the authoritative state source. Update streaming call sites
      to pass the event type. Aggregate call site stays unchanged.
- [x] Task 3: Update existing `test_loop_item_streaming.py` tests whose
      fixtures set `failed=True` / `skipped=True` (an incorrect
      assumption about the real callback payload) so the new fixture
      helper `_aom_jsonl_item_event` documents the real shape. Existing
      assertions must still pass.
- [x] F1: Run full suite + mypy + ruff. Manual smoke: run AOM on a
      playbook with one failed loop item + `--hide-state ok,skipped`
      and confirm the failed item's `msg` is now visible.

## Verification results

- `uv run pytest tests/compact/test_loop_item_streaming.py tests/compact/test_hide_state.py -q`: 44 passed (10 new)
- `uv run pytest tests/ -q`: 2885 passed, 6 skipped, 1 xfailed (no regressions)
- `uv run mypy src/ansible_aom`: Success, no issues in 69 files
- `uv run ruff check src/ansible_aom/compact/renderer.py tests/compact/test_loop_item_streaming.py tests/compact/test_hide_state.py`: All checks passed
- Manual smoke (`aom --hide-state ok,skipped` on a failing loop): the failed item now renders as `failed: [localhost] => (item=...) => Destination directory /opt/firefly/missing does not exist`. Pre-fix it was `ok: [localhost] => (item=...)` with no msg.