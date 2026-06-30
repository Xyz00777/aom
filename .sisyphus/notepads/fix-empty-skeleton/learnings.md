# Fix Empty-Skeleton Template Match — Learnings

## 2026-06-26: Empty-skeleton `{{ ... }}` preflight names greedily match any runtime task

### Bug
A preflight task whose name is entirely a Jinja template expression (e.g.
`{{ var }}` or `{{ xx }}`) left an empty `_template_skeleton` after
splitting on `{{ ... }}`. The `_is_template_match` function short-circuited
on the empty fragment list and returned `True` for ANY runtime name,
causing the preflight `{{ ... }}` task to greedily claim the first runtime
task it saw. Subsequent preflight tasks that should match that runtime task
literally couldn't find their match (the runtime identity was already in
`matched_runtime_task_ids`) and stayed pending forever — appearing to
never get "removed from the tree view" when the runtime completed.

### Root cause
In `_is_template_match` (`src/ansible_aom/core/tree_projection.py:148`):
```python
fragments = [f for f in _TEMPLATE_RE.split(preflight_name) if f]
if not fragments:
    return True   # ← BUG: empty skeleton matches ANY runtime name
```
When `preflight_name = "{{ var }}"`, `_TEMPLATE_RE.split` yields `["", ""]`,
the `if f` filter drops both, `fragments = []`, and the early return says
"match anything". The same bug existed in the inline mirror at
`_graft_or_match_task` (`src/ansible_aom/core/run_state.py:477-479`).

Additionally, in `_emit_preflight_entries`, when `_is_template_match` now
correctly returns `False` for all candidates, the `{{ var }}` entry with
`runtime is None` would still be emitted as a pending orphan (it would
never match any future runtime task). A secondary fix skips entirely
pre_flight entries whose names have empty skeletons and no runtime match.

### Fix
1. **`_is_template_match`** (`tree_projection.py:148`): Changed
   `return True` → `return False` for the empty-fragments branch. A
   preflight name with zero static fragments cannot anchor a match; the
   exact-equality path in `_pick_runtime` handles the case where preflight
   and runtime names are literally identical.

2. **Inline mirror** (`run_state.py:477-479`): Changed
   `leaf = tdef; break` → `continue` for the empty-fragments branch. Same
   algorithm change, mirrored in place per project convention.

3. **`_emit_preflight_entries`** (`tree_projection.py:1933-1940`): After the
   template-match fallback loop, if `runtime is None` and the preflight
   name has an empty skeleton (`fragments = []`), skip the entry entirely
   (`continue`) — it can never match any runtime task and would otherwise
   appear as a permanent pending orphan in the tree.

4. **Docstring** (`tree_projection.py:127-144`): Added a paragraph to the
   `_is_template_match` docstring documenting the new contract: the
   function requires at least one non-empty static fragment; pure-template
   names return `False`.

5. **Comment** (`run_state.py:463-475`): Extended the inline comment block
   to note that entirely-templated preflight names cannot match via the
   loop and are handled by the caller's direct name comparison path.

### Where it lives
- **Canonical implementation**: `_is_template_match` in
  `src/ansible_aom/core/tree_projection.py:127-156`. Used by 5+ call sites
  within `tree_projection.py` (`_pick_runtime`, `_emit_preflight_entries`,
  role-counting pass, etc.).
- **Mirror loop**: `_graft_or_match_task` in
  `src/ansible_aom/core/run_state.py:463-495`. Inline re-implementation of
  the same algorithm, kept separate because `run_state.py` is the upstream
  module.
- **Emission guard**: `_emit_preflight_entries` in
  `src/ansible_aom/core/tree_projection.py:1933-1940`. Skips preflight
  entries with empty skeletons that have no runtime match.

### Why not extract a shared helper
Same rationale as the prior `fix-jinja-punctuation` fix: `run_state.py`
is the upstream module that `tree_projection.py` imports, so extracting
`_is_template_match` into a shared module would either create a circular
import or expand `models.py` with string-matching logic orthogonal to its
purpose. The project convention is to update both copies in place with the
same algorithm change and leave comments pointing to the canonical
implementation.

### Tests added (TDD-first)
Three new tests appended to `tests/unit/test_template_variable_names.py`:

- `test_empty_skeleton_does_not_swallow_unrelated_task`: integration test
  — preflight `["{{ var }}", "Plain task A", "Plain task B"]`, runtime
  completes A then starts B. Asserts Plain task B is in the tree and
  `{{ var }}` is NOT. Before the fix, `{{ var }}` stole Plain task A's
  match, causing A to disappear entirely.
- `test_empty_skeleton_is_template_match_returns_false`: direct unit test
  of `_is_template_match("{{ var }}", "Plain task A")` returns `False`.
  Before the fix it returned `True`.
- `test_empty_skeleton_against_itself_returns_false`: direct unit test of
  `_is_template_match("{{ var }}", "{{ var }}")` returns `False`. Even
  when both names are identical Jinja expressions, no static fragment
  exists to anchor a match; exact-equality path handles this case.

### Verification
- `uv run pytest tests/unit/test_template_variable_names.py -v` —
  11 passed (8 pre-existing + 3 new).
- `uv run pytest tests/ -q -n auto` — 2870 passed, 6 skipped (baseline
  was 2862 passed per the prior fix; +8 from new tests across the suite).
- `uv run mypy src/ansible_aom` — clean (74 source files).
- `uv run ruff check src/ansible_aom/core/tree_projection.py
  src/ansible_aom/core/run_state.py tests/unit/test_template_variable_names.py`
  — clean.

### Key insights
- **Empty fragment lists degenerate to wildcards.** When `_TEMPLATE_RE.split`
  produces only empty strings (which the `if f` filter removes), the
  fragment-substring algorithm has no constraints and every runtime name
  satisfies vacuously. The fix is to require ≥1 non-empty static fragment.
- **The fix required TWO changes, not just one.** Changing `_is_template_match`
  alone wasn't sufficient — `_emit_preflight_entries` also needed to skip
  entries with empty skeletons and no runtime match, because they would
  otherwise appear as permanent pending orphans in the tree. The
  `_is_template_match` fix prevents the greedy claim; the emission guard
  prevents the orphan from appearing.
- **Mirror-function policy confirmed again.** The `run_state.py` inline loop
  needed the same algorithm change. The project's convention of keeping
  both copies in sync (not extracting a shared helper) remains the right
  call — the upstream module constraint hasn't changed.
- **TDD-first confirmed the exact failure mode.** Writing the integration
  test first revealed that the fix required both the `_is_template_match`
  change AND the emission guard. Without TDD, the emission guard might
  have been missed because the unit tests alone (which test `_is_template
  _match` in isolation) don't exercise the tree projection pipeline.
- **Completed tasks are dropped from the tree.** The integration test
  initially asserted that "Plain task A" would appear in the tree, but
  completed tasks are filtered out by `_classify(runtime) == "completed"`.
  The correct assertion is that `{{ var }}` does NOT appear and Plain
  task B DOES appear — Plain task A completes and is correctly dropped.