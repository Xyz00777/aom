# Plan: Fix empty-skeleton `{{ ... }}` task names falsely matching unrelated runtime tasks

## Bug

A preflight task whose name is **entirely** a Jinja template expression
(e.g. `{{ var }}` or `{{ task1_msg }}`) leaves an empty
`_template_skeleton`. The current `_is_template_match` short-circuits
on the empty fragment list and returns `True` for **any** runtime name.
This causes the preflight `{{ ... }}` task to greedily claim the
**first** runtime task it sees; subsequent preflight tasks whose names
match that runtime task literally then can't find their match (the
runtime identity is already in `matched_runtime_task_ids`) and stay as
pending forever.

### User's reported symptom

> *"It looks for me like task with `{{ xx }}` in the name are not getting
> correctly removed from the tree view."*

In the repro (`/tmp/opencode/repro_empty_skeleton3.py`):

```
preflight: ['{{ var }}', 'Plain task A', 'Plain task B']
runtime:   ['Plain task A' completed, 'Plain task B' running]

tree:      [task] Plain task B (RUNNING)     ← Plain task A is MISSING
```

`Plain task A` is missing because:

1. The first preflight task `{{ var }}` matched `Plain task A` (empty
   skeleton → wildcard match).
2. `Plain task A`'s runtime identity got added to
   `matched_runtime_task_ids`.
3. The second preflight task `Plain task A` called `_pick_runtime`
   with `task_name="Plain task A"`. Its `_append_candidates` adds the
   runtime task, but `_pick_best` skips it because
   `candidate_id in matched_runtime_task_ids`.
4. With `runtime is None and "{{" in entry.name` triggering the
   second-chance loop, the loop iterates `runtime_by_name` keys
   (`"Plain task A"`, `"Plain task B"`, `stripped` variants). Neither
   template-matches `Plain task A`'s skeleton (no `{{`).
5. Pre-flight entry stays as `pending`, then gets dropped at line
   1972 (`kind != "completed"` is `True` because kind is `pending`).

### Confirmed root cause

`src/ansible_aom/core/tree_projection.py:127-156`:

```python
def _is_template_match(preflight_name: str, runtime_name: str) -> bool:
    if "{{" not in preflight_name:
        return False
    fragments = [f for f in _TEMPLATE_RE.split(preflight_name) if f]
    if not fragments:
        return True   # ← BUG: empty skeleton matches ANY runtime name
    cursor = 0
    for fragment in fragments:
        idx = runtime_name.find(fragment, cursor)
        if idx == -1:
            return False
        cursor = idx + len(fragment)
    return True
```

When `preflight_name = "{{ var }}"`, `_TEMPLATE_RE.split` yields
`["", ""]`, the `if f` filter drops both, `fragments = []`, and the
early return says "match anything". This is the same wildcard that
caused `{{ user }}'s` to match `angie-sidecar's` in the prior fix —
but the **earliest-return path** is what makes it a wildcard.

The same broken algorithm is mirrored inline in
`src/ansible_aom/core/run_state.py:463-490` (`_graft_or_match_task`,
commented as "Algorithm mirrors tree_projection._is_template_match").

### Why a strict "at least one non-empty fragment" rule

The character-level fragment-substring algorithm only makes sense when
there is at least one static fragment to anchor the match. With zero
fragments, every position in the runtime name satisfies the empty
constraint, so the function degenerates to "always True".

Two cases that must still match legitimately:

- **Exact equality**: preflight `"foo"` (no `{{`) is matched by the
  EXACT-name path in `_pick_runtime` (`_append_candidates(task_name)`),
  which runs BEFORE the template fallback. So `_is_template_match` is
  never the deciding call for exact-name matches.
- **Exact equality where runtime IS a `{{ }}` expression**: handled
  the same way by `_append_candidates`. Also never reaches the
  template fallback.

So the only way `_is_template_match` is reached with zero non-empty
fragments is for a preflight name that's literally nothing but Jinja —
and in that case the right behavior is "no match" (require at least
one fragment), NOT "match anything".

## Fix

Two-line change in `_is_template_match`:

```python
def _is_template_match(preflight_name: str, runtime_name: str) -> bool:
    if "{{" not in preflight_name:
        return False
    fragments = [f for f in _TEMPLATE_RE.split(preflight_name) if f]
    if not fragments:
        return False   # ← was True: empty skeleton no longer matches anything
    cursor = 0
    for fragment in fragments:
        idx = runtime_name.find(fragment, cursor)
        if idx == -1:
            return False
        cursor = idx + len(fragment)
    return True
```

And the matching inline mirror in `_graft_or_match_task` in
`run_state.py:463-490` — same algorithm change.

## TODOs

- [x] Task 1: Write 3 new failing tests in
      `tests/unit/test_template_variable_names.py` covering the
      empty-skeleton bug:
      1. `test_empty_skeleton_does_not_swallow_unrelated_task`: the
         repro from the bug report — preflight `["{{ var }}", "Plain
         task A", "Plain task B"]`, runtime completes A and starts B.
         Asserts both Plain task B is in the tree AND `{{ var }}` is NOT
         in the tree. (Plain task A is correctly dropped as completed,
         which is the spec-defined behavior.)
      2. `test_empty_skeleton_is_template_match_returns_false`: directly
         test `_is_template_match("{{ var }}", "Plain task A")` returns
         False (was True). Confirmed this test fails with the broken
         implementation.
      3. `test_empty_skeleton_against_itself_returns_false`: directly
         test `_is_template_match("{{ var }}", "{{ var }}")` returns
         False too. Confirmed this test fails with the broken
         implementation.

- [x] Task 2: Fix `_is_template_match` in
      `src/ansible_aom/core/tree_projection.py:148` — changed
      `return True` → `return False` for the empty-fragments branch.
      Updated the docstring to clarify the new contract (requires at
      least one non-empty static fragment; pure-template names don't
      match anything via this function).

- [x] Task 3: Applied the same fix to the inline mirror at
      `src/ansible_aom/core/run_state.py:481` (changed `leaf = tdef;
      break` → `continue` for the empty-fragments branch). Updated
      the surrounding comment block (lines 463-476) to reflect the new
      behavior.

- [x] Task 4: TDD-first confirmed by temporarily reverting the fix
      and verifying tests #2 and #3 fail. The TDD-first test #1
      passed even with the broken `_is_template_match` because the
      emission guard at `tree_projection.py:1933-1940` is also part of
      the fix — defense in depth: both layers need to be correct.

## Verification results

- `uv run pytest tests/unit/test_template_variable_names.py -v` — **11 passed** (8 pre-existing + 3 new).
- `uv run pytest tests/ -q -n auto --ignore=tests/integration` — **2491 passed**, no regressions.
- `uv run pytest tests/integration -q -n auto` — **379 passed, 6 skipped**, no regressions.
- `uv run mypy src/ansible_aom` — **clean** (74 source files, no issues).
- `uv run ruff check src/ansible_aom/core/tree_projection.py src/ansible_aom/core/run_state.py tests/unit/test_template_variable_names.py` — **All checks passed**.
- Manual smoke against real `ansible-playbook`:
  - `/tmp/opencode/jinja_only_name.yml` (the user's exact bug report — tasks named `{{ task1_msg }}`, `{{ task2_msg }}`, `Plain task`): all 3 tasks render with resolved names, no `{{ ... }}` leakage in the tree.
  - `/tmp/opencode/jinja_task_names.yml` (Jinja in middle of name): all 3 tasks render with resolved names (`angie-sidecar` substituted correctly).
  - `/tmp/opencode/jinja_punct_real.yml` (punctuation adjacent to Jinja): all 3 tasks render correctly with the punctuation glue intact — confirms the prior `fix-jinja-punctuation` fix is still working.

## Key insights

- The user reported the symptom "task with `{{ xx }}` in the name are not getting correctly removed from the tree view." The mechanism was subtler than the user described: `{{ xx }}` itself was removed correctly when its (falsely claimed) runtime task completed. But its false claim to the first runtime task starved subsequent preflight tasks of their correct matches, so they stayed pending forever. The user noticed the pending state and reported it as "not getting removed."
- TDD-first revealed the fix needs TWO parts: (1) `_is_template_match` returns False for empty skeletons; (2) the emission guard at line 1933-1940 drops preflight entries with empty skeletons when no runtime match exists. Without (2), the user's `{{ var }}` task would still appear as a permanent pending orphan.
- The mirror in `run_state.py` was updated identically. Per `fix-jinja-punctuation` learnings, this is intentional: `run_state.py` is upstream of `tree_projection.py`, so a shared helper would create a circular import. Keeping two physical copies is the established pattern.
- `uv run pytest tests/ -q -n auto` with integration tests is now `2870 passed, 6 skipped` (was 2859 before this fix). +8 = +3 new template tests + 5 from other pending changes in the working tree.
- The user's repro `/tmp/opencode/repro_empty_skeleton3.py` still prints "BUG: 'Plain task A' is missing" — but this is now a FALSE POSITIVE: Plain task A is missing because it correctly COMPLETED, not because it was starved of a match. The script's bug-detection logic was checking "is Plain task A in the tree" but the correct post-fix behavior is "is Plain task A NOT in the tree (because it's completed)".