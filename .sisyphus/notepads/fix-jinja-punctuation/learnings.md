# Fix Jinja Punctuation — Learnings

## 2026-06-26: Jinja + adjacent punctuation breaks template match

### Bug
Preflight task names like ``Ensure {{ user }}'s home exists`` (where
punctuation is glued to a Jinja expression) failed to match their
resolved runtime names like ``Ensure angie-sidecar's home exists``.
The preflight entry stayed PENDING in the tree forever while the
resolved runtime task appeared as a separate RUNNING line.

### Root cause
``_is_template_match`` in ``src/ansible_aom/core/tree_projection.py``
(stripped ``{{ ... }}`` to get a "skeleton" string, then split on
whitespace and verified each skeleton word appeared as a subsequence
in the runtime name. Punctuation adjacent to a Jinja expression
(``'s`` after ``{{ user }}``) became a separate skeleton word after
``.split()``, but in the runtime name it was attached to the resolved
value as part of a single word. So skeleton tokens
``["Ensure", "'s", "home", "exists"]`` vs runtime tokens
``["Ensure", "angie-sidecar's", "home", "exists"]`` failed at the
``'s`` vs ``angie-sidecar's`` mismatch.

The same bug existed in the inline template-match loop inside
``_graft_or_match_task`` in ``src/ansible_aom/core/run_state.py``
(around lines 463-482 pre-fix) — it was a near-duplicate of
``_is_template_match`` with the same broken word-subsequence logic.

### Fix
Switched from a whitespace-tokenized subsequence match to a
**character-level fragment-substring match**:

1. Split the preflight name on ``{{ ... }}`` (not on whitespace). The
   resulting list has the static text fragments interleaved with the
   Jinja expressions; we keep only the static fragments (filter out
   empty strings from leading/trailing placeholders).
2. Walk the fragments in order, using ``str.find(fragment, cursor)`` to
   locate each one in the runtime name starting after the previous
   match. The Jinja expressions are implicit wildcards — each fragment
   consumes only the characters it explicitly contains, and the
   characters between successive fragment matches are absorbed as the
   resolved variable's contribution.

This is a stricter match than the old token-subsequence check: it
requires the static fragments to appear in the runtime name in
exactly the order they appear in the preflight name, with no extra
characters between them other than what the placeholders absorb.

### Where it lives
- **Canonical implementation**: ``_is_template_match`` in
  ``src/ansible_aom/core/tree_projection.py:127``. This is the
  function used by 5 call sites within ``tree_projection.py`` itself
  (``_pick_runtime``, ``_emit_preflight_entries``, the role-counting
  pass around line 1559, etc.).
- **Mirror loop**: ``_graft_or_match_task`` in
  ``src/ansible_aom/core/run_state.py:462-490``. This is an inline
  re-implementation of the same algorithm. The mirror exists because
  ``run_state.py`` is the upstream module that ``tree_projection.py``
  imports, so ``run_state.py`` can't import ``_is_template_match``
  from ``tree_projection`` without creating a circular import.

### Why not extract a shared helper
The project's recent consolidation work (``grumpi-fixes`` learnings)
prefers extracting duplicated logic into a canonical helper module.
However, the natural home for this helper (``core/tree_projection.py``)
depends on ``core/run_state.py`` (it imports ``RunState``), so
``run_state.py`` cannot import from it. Two viable options:

1. Put the helper in ``core/models.py`` (which is already imported by
   both modules). This would expand ``models.py`` (currently pure data
   classes and a small set of accessors) with a string-matching
   function that's orthogonal to the model layer.
2. Create a new ``core/template_match.py`` module. This adds a new
   file for one ~15-line function.

Both options add complexity to consolidate ~10 lines of duplicated
loop body. The decision was to update the inline loop with the same
algorithm and leave a comment pointing to the canonical
implementation, so the two stay in sync conceptually even though they
are physically separate. If a third call site appears, or if the
algorithm grows more complex, that's the right moment to extract.

### Tests added (TDD-first)
Three new tests appended to
``tests/unit/test_template_variable_names.py``:

- ``test_template_variable_with_punctuation_suffix``: the user's exact
  reported case (``Ensure {{ user }}'s home exists`` vs
  ``Ensure angie-sidecar's home exists``). Failed before the fix.
- ``test_template_variable_with_punctuation_prefix``: punctuation
  *before* the Jinja expression (``Deploy for {{ user }}!`` vs
  ``Deploy for angie-sidecar!``). Failed before the fix.
- ``test_template_variable_in_middle_with_punctuation``: two Jinja
  expressions in the middle (``Copy {{ src }} to {{ dest }}`` vs
  ``Copy /etc/a to /etc/b``). Regression guard for the no-punctuation
  case — passes before AND after the fix.

### Verification
- ``uv run pytest tests/unit/test_template_variable_names.py -v`` —
  8 passed (5 pre-existing + 3 new).
- ``uv run pytest tests/ -q -n auto`` — 2862 passed, 6 skipped (the
  3 new tests are part of the 2862; baseline before this change was
  2859 passed per the task spec).
- ``uv run mypy src/ansible_aom`` — clean (74 source files).
- ``uv run ruff check src/ansible_aom/core/tree_projection.py
  src/ansible_aom/core/run_state.py tests/unit/test_template_variable_names.py``
  — clean.

### Key insights
- **Whitespace tokenization is fragile against any text where the
  resolution changes the token boundaries.** A static-fragment match
  on the *raw* preflight string (not the Jinja-stripped skeleton)
  survives any number of resolved-variable side effects: punctuation
  gluing, embedded spaces inside the variable's value, hyphens,
  etc. The constraint is that the resolved value's characters between
  successive static fragments just become the wildcard payload.
- **The bug existed in two places because ``run_state.py`` is the
  upstream module.** This is a layering observation worth capturing:
  ``run_state.py`` defines the state object that ``tree_projection.py``
  consumes, so any consolidation that would require
  ``run_state.py`` to import from ``tree_projection.py`` is blocked
  by the existing import order. Future "fix the same bug in two
  places" tasks in this codebase should expect this pattern.
- **The fragment list after ``_TEMPLATE_RE.split`` may include empty
  strings** (from a leading or trailing ``{{ ... }}``). The
  truthiness filter ``[f for f in ... if f]`` drops these. The
  cursor-advancing logic in the match loop also implicitly handles
  the empty-fragment case correctly because ``str.find("", n)``
  returns ``n`` and ``n + 0 == n``, so an empty fragment never
  blocks the cursor from advancing (the next fragment will be
  searched from the same position).
- **Test docstrings are not comments** — they're test purpose
  statements, identical to BDD-style ``# given``/``# when``/``# then``
  markers in their intent. The existing 5 tests in
  ``test_template_variable_names.py`` all use docstrings to explain
  what they test, and the 3 new tests follow the same convention.
