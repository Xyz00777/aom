# Task-log diff implementation plan

> For agentic workers: use subagent-driven-development for the implementation and fresh-context review.

**Goal:** Show captured module diffs beneath changed live/replayed task results.

**Architecture:** Pure diff formatting in `core/diff.py`; indentation and ANSI styling in compact rendering. Existing result/item branches determine visibility, attribution and duplicate suppression.

**Tech stack:** Python standard-library `difflib` and JSON, existing Rich/compact display.

## 1. Pure formatter

Own `src/ansible_aom/core/diff.py` and `tests/unit/test_diff.py`.

- [x] Write and run a failing exact-output test for a changed text line:

```python
result = {"changed": True, "diff": {"before": "x=1\n", "after": "x=2\n"}}
assert format_result_diff(result) == ["--- before", "+++ after", "@@ -1 +1 @@", "-x=1", "+x=2"]
```

- [x] Implement `format_result_diff(result: Mapping[str, object]) -> list[str]` as a pure projection. Suppress unchanged/no-log/censored payloads; preserve headers, prepared/string diffs, lists, mapping contents, binary/oversize notices and surrogate-safe output. Use standard-library unified hunks; do not modify input.
- [x] Add independent expected outputs for these forms, equal before/after, missing final newline, and no-log suppression. Run the focused tests green.

## 2. Compact wiring

Own `src/ansible_aom/compact/renderer.py` and `tests/compact/test_task_diff.py`.

- [x] Write and run failing tests through `update_state` for host diffs and loop item diffs, including an aggregate following streamed items.
- [x] Append indented formatted lines to existing per-event output batches. Apply existing renderer colors to diff lines; retain plain output. Keep parent no-log/censor suppression through aggregate-loop fallback.
- [x] Pin multi-host attribution, exactly-once streamed/aggregate loop output, hidden-state suppression, and empty renderer startup args (replay). Existing status lines remain unchanged.
- [x] Run new tests and existing loop/batching/replay tests. Keep one print operation per existing event batch.

## 3. Verification and delivery

- [x] Run a real temporary playbook using `--check --diff` and inspect captured output.
- [x] Verify semantic mutations in isolated source copies: drop a hunk line, ignore no-log, bypass hide-state, or repeat aggregate loop diffs. Distinguish assertions from crashes.
- [x] Get fresh-context review of contracts, secrets suppression and simplicity.
- [x] Run Ruff, mypy and the combined full suite with the known Ansible collection setup. Parent owns commits and version hooks; no worker stages or commits shared checkout changes.
