# R1 — JSONL Carry Buffer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop dropping JSONL events when pexpect splits one across two reads — stash the partial in a 1 MB carry buffer and rejoin on the next chunk; pin existing fall-through behaviour for unknown `_event` values.

**Architecture:** `JsonLineStream.feed_line` gains a `self._carry: str` attribute. When `json.loads` raises `JSONDecodeError` on a line that started with `{`, the line is stored in `_carry` (if it fits under a 1 MB cap) and prepended to the next `feed_line` input. Over-cap partials are dropped with a `WARNING` log; the carry is cleared so subsequent well-formed lines parse standalone. `RunState.handle_event` is left untouched — its existing `else: logger.debug(...)` branch already swallows unknown events without mutating state, and we pin that with a test so R5 (which adds a counter on top) doesn't silently regress this contract.

**Tech Stack:** Python 3.14, pytest, `json` (stdlib), `logging` (stdlib). No new runtime deps. Tests live in `tests/unit/test_parser.py` alongside the existing `JsonLineStream` suite.

---

## File Map

| File | Role |
|------|------|
| `src/ansible_aom/core/parser.py` | Add `_CARRY_LIMIT` constant, `_carry` attribute, carry-and-rejoin logic in `JsonLineStream.feed_line` |
| `tests/unit/test_parser.py` | Add `TestJsonLineStreamCarryBuffer` and `TestRunStateUnknownEvent` test classes |

No new files. No public API changes — `JsonLineStream.feed_line` keeps its `(line: str) -> list[dict]` signature; the carry is internal.

---

## Pre-flight

Confirm baseline is green before touching anything.

- [ ] **Step 0.1: Verify baseline tests pass**

Run: `uv run pytest tests/unit/test_parser.py -q`
Expected: all tests pass (the existing `TestJsonLineStreamBasics` class and friends).

- [ ] **Step 0.2: Confirm `JsonLineStream` exists at expected location**

Run: `grep -n "^class JsonLineStream" src/ansible_aom/core/parser.py`
Expected output: a single line like `45:class JsonLineStream:` (line number may differ).

If the class isn't there, stop — this plan assumes the current parser layout.

---

## Task 1: Pin two-chunk join behaviour with a failing test

**Files:**
- Test: `tests/unit/test_parser.py` (add new class after `TestJsonLineStreamBasics`)

The first failure case to fix: a single JSONL event arrives split across two `feed_line` calls. Today both halves are dropped. The test must fail before we add the carry buffer.

- [ ] **Step 1.1: Locate insertion point in test file**

Run: `grep -n "^class TestJsonLineStream\|^class TestPtyStreamParser" tests/unit/test_parser.py`
Expected: shows `class TestJsonLineStreamBasics`, then later classes like `TestPtyStreamParserPhases`. We will insert a new class `TestJsonLineStreamCarryBuffer` directly after `TestJsonLineStreamBasics` (look for the end of that class — the line before the next `class T...` declaration).

- [ ] **Step 1.2: Write the failing test**

Add this class to `tests/unit/test_parser.py` immediately after `TestJsonLineStreamBasics`:

```python
class TestJsonLineStreamCarryBuffer:
    """R1: PTY can split a JSONL event across reads. The first half on its
    own is unparseable JSON; the parser must stash it and rejoin with the
    next chunk instead of dropping both halves."""

    def test_two_chunk_join_yields_full_event(self):
        """Half a JSONL line then the rest should yield one event."""
        parser = JsonLineStream()
        assert parser.feed_line('{"_event":"v2_runner_on_ok","hosts":{"web1":{"msg":"hel') == []
        result = parser.feed_line('lo"}}}')
        assert len(result) == 1
        assert result[0]["_event"] == "v2_runner_on_ok"
        assert result[0]["hosts"]["web1"]["msg"] == "hello"
```

- [ ] **Step 1.3: Run the new test and watch it fail**

Run: `uv run pytest tests/unit/test_parser.py::TestJsonLineStreamCarryBuffer::test_two_chunk_join_yields_full_event -v`
Expected: FAIL. The first `feed_line` call returns `[]` (correct — `json.loads` raises and the partial is dropped today). The second `feed_line` call also returns `[]` because `'lo"}}}'` doesn't start with `{`, so the assertion `len(result) == 1` fails with something like `assert 0 == 1`.

- [ ] **Step 1.4: Add the carry buffer to `JsonLineStream`**

Modify `src/ansible_aom/core/parser.py`. Replace the existing `JsonLineStream` class definition with this version (the docstring, the new `_CARRY_LIMIT` constant, the new `_carry` attribute, and the carry logic in `feed_line`):

```python
class JsonLineStream:
    """Parses JSON lines from a mixed JSON/plaintext stream.

    Pexpect can split a JSONL event across two reads on a slow link or a
    very long ``msg`` payload. To avoid dropping both halves, a partial
    line that looks like JSON (starts with ``{`` but fails to parse) is
    stashed in ``_carry`` and prepended to the next ``feed_line`` input.
    The carry is hard-capped at ``_CARRY_LIMIT`` bytes — past that we
    assume the stream is wedged and drop rather than grow without bound.
    """

    # 1 MB. Real ansible events are usually <10 KB; a single event larger
    # than this is almost certainly a bug or a pathological host output.
    _CARRY_LIMIT = 1_000_000

    def __init__(self) -> None:
        self._non_json_handler: Callable[[str], None] | None = None
        self._carry: str = ""

    def feed_line(self, line: str) -> list[dict]:
        """Parse a line and return zero or more JSON events.

        Returns empty list for:
        - Empty lines
        - Invalid JSON (stored as carry if line started with ``{``)
        - JSON without _event field
        """
        # Prepend any pending partial from a previous call so a JSONL
        # event split across two reads is rejoined.
        if self._carry:
            line = self._carry + line
            self._carry = ""

        line = line.strip()
        if not line:
            return []

        if not line.startswith("{"):
            if self._non_json_handler:
                self._non_json_handler(line)
            return []

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            # Stash as carry if there's room, otherwise drop. Without
            # the cap a runaway/garbage stream would grow ``_carry``
            # without bound.
            if len(line) <= self._CARRY_LIMIT:
                self._carry = line
                return []
            logger.warning("Invalid JSON line (carry overflow, dropped): %s", line[:100])
            if self._non_json_handler:
                self._non_json_handler(line)
            return []

        if "_event" not in data:
            logger.warning("JSON missing _event field: %s", line[:100])
            return []

        return [data]

    def set_non_json_handler(self, handler: Callable[[str], None]) -> None:
        """Set handler for non-JSON lines."""
        self._non_json_handler = handler
```

Key changes vs. the previous version:
1. New class docstring documenting the carry-buffer contract.
2. New `_CARRY_LIMIT = 1_000_000` class constant.
3. New `self._carry: str = ""` instance attribute.
4. New "prepend carry" block at the top of `feed_line` (before the `strip()`).
5. The `except json.JSONDecodeError` branch now stashes if under the cap, drops if over, and clears the carry to empty when over-cap.
6. The over-cap branch keeps the existing `_non_json_handler` notification path for symmetry with the pre-R1 behaviour.

- [ ] **Step 1.5: Run the test again — must pass**

Run: `uv run pytest tests/unit/test_parser.py::TestJsonLineStreamCarryBuffer::test_two_chunk_join_yields_full_event -v`
Expected: PASS.

- [ ] **Step 1.6: Run the full parser suite to confirm nothing regressed**

Run: `uv run pytest tests/unit/test_parser.py -q`
Expected: all tests pass (the existing `TestJsonLineStreamBasics` tests should still be green — the carry only kicks in when `json.loads` raises).

- [ ] **Step 1.7: Commit**

```bash
git add src/ansible_aom/core/parser.py tests/unit/test_parser.py
git commit -m "feat(parser): carry buffer for partial JSONL lines (R1)

JsonLineStream now stashes a JSON line that starts with { but fails to
parse, prepending it to the next chunk so an event split across two
pexpect reads is rejoined instead of both halves being dropped.

Hard-capped at 1 MB so a wedged stream can't grow the buffer without
bound — past the cap the partial is dropped and the next well-formed
line parses standalone."
```

---

## Task 2: Pin many-chunk slow-drip behaviour

**Files:**
- Test: `tests/unit/test_parser.py` (extend `TestJsonLineStreamCarryBuffer`)

A 100-chunk slow-drip is the realistic "very long output through a slow PTY" case. The carry must keep accumulating across many failed parses, not just one.

- [ ] **Step 2.1: Add the test**

Append this method to the `TestJsonLineStreamCarryBuffer` class in `tests/unit/test_parser.py`:

```python
    def test_many_small_chunks_join(self):
        """A 100-chunk slow-drip split still yields exactly one event."""
        full = '{"_event":"v2_playbook_on_start","msg":"' + ("x" * 200) + '"}'
        parser = JsonLineStream()
        chunk_size = max(1, len(full) // 100)
        events: list[dict] = []
        for i in range(0, len(full), chunk_size):
            events.extend(parser.feed_line(full[i : i + chunk_size]))
        assert len(events) == 1
        assert events[0]["_event"] == "v2_playbook_on_start"
```

- [ ] **Step 2.2: Run the test — should pass already**

Run: `uv run pytest tests/unit/test_parser.py::TestJsonLineStreamCarryBuffer::test_many_small_chunks_join -v`
Expected: PASS. The carry already handles repeated accumulation: each chunk after the first is `_carry + chunk`, which fails to parse, and the whole thing gets re-stashed. Only the final chunk produces a valid `json.loads`, returning the event.

If it fails, the most likely cause is the carry being cleared too eagerly — re-read Step 1.4 and ensure `self._carry = ""` happens *only* in the `if self._carry:` prepend block at the top of `feed_line`, not in the `except` branch (the `except` branch only sets `_carry` to the new partial; the `_carry = ""` already happened during the prepend).

- [ ] **Step 2.3: Commit**

```bash
git add tests/unit/test_parser.py
git commit -m "test(parser): pin many-chunk slow-drip carry-buffer rejoin (R1)"
```

---

## Task 3: Pin overflow-drop behaviour at the 1 MB cap

**Files:**
- Test: `tests/unit/test_parser.py` (extend `TestJsonLineStreamCarryBuffer`)

The carry must not grow without bound. When a single partial exceeds 1 MB, the parser drops it and continues — the next well-formed line must parse standalone, not get poisoned by a stale carry.

- [ ] **Step 3.1: Add the test**

Append this method to the `TestJsonLineStreamCarryBuffer` class in `tests/unit/test_parser.py`:

```python
    def test_carry_buffer_overflow_drops_without_raising(self):
        """One pathologically large partial event is dropped, not OOM'd,
        and a subsequent well-formed line parses cleanly."""
        parser = JsonLineStream()
        # First chunk is a partial JSON that's already larger than the
        # 1 MB cap. Storing it as carry would be unbounded growth — the
        # parser must drop it.
        oversized = '{"_event":"x","msg":"' + ("a" * 1_100_000)
        assert parser.feed_line(oversized) == []
        # After the drop, the carry must be empty so the next line is
        # parsed standalone.
        result = parser.feed_line('{"_event":"v2_playbook_on_start"}')
        assert len(result) == 1
        assert result[0]["_event"] == "v2_playbook_on_start"
```

- [ ] **Step 3.2: Run the test — should pass**

Run: `uv run pytest tests/unit/test_parser.py::TestJsonLineStreamCarryBuffer::test_carry_buffer_overflow_drops_without_raising -v`
Expected: PASS. The first `feed_line` call hits the `len(line) <= self._CARRY_LIMIT` check, falls into the `else` branch, logs the warning, and returns `[]` — and crucially, never sets `self._carry`. The second call sees an empty carry and parses the well-formed line directly.

If it fails because the second `feed_line` returns `[]`: the over-cap branch is leaking the partial into `_carry`. Re-check Step 1.4: the over-cap branch should only `logger.warning(...)` and return `[]`; it must not assign to `self._carry`.

- [ ] **Step 3.3: Commit**

```bash
git add tests/unit/test_parser.py
git commit -m "test(parser): pin 1 MB carry-buffer overflow drop behaviour (R1)"
```

---

## Task 4: Sanity check — well-formed lines bypass the carry path

**Files:**
- Test: `tests/unit/test_parser.py` (extend `TestJsonLineStreamCarryBuffer`)

A regression-only test: confirm the carry path doesn't accidentally interfere with the happy path. If a future refactor moves the `self._carry` prepend or the `self._carry = ""` reset into the wrong place, this test will catch it.

- [ ] **Step 4.1: Add the test**

Append this method to the `TestJsonLineStreamCarryBuffer` class in `tests/unit/test_parser.py`:

```python
    def test_well_formed_line_does_not_use_carry(self):
        """Sanity: a normal line in one go bypasses the carry path."""
        parser = JsonLineStream()
        result = parser.feed_line('{"_event":"v2_playbook_on_start"}')
        assert len(result) == 1
        # And a subsequent line still parses fine.
        result2 = parser.feed_line('{"_event":"v2_runner_on_ok","hosts":{}}')
        assert len(result2) == 1
```

- [ ] **Step 4.2: Run the test — should pass**

Run: `uv run pytest tests/unit/test_parser.py::TestJsonLineStreamCarryBuffer::test_well_formed_line_does_not_use_carry -v`
Expected: PASS.

- [ ] **Step 4.3: Run the full carry-buffer suite together**

Run: `uv run pytest tests/unit/test_parser.py::TestJsonLineStreamCarryBuffer -v`
Expected: 4 passed (`test_two_chunk_join_yields_full_event`, `test_many_small_chunks_join`, `test_carry_buffer_overflow_drops_without_raising`, `test_well_formed_line_does_not_use_carry`).

- [ ] **Step 4.4: Commit**

```bash
git add tests/unit/test_parser.py
git commit -m "test(parser): pin well-formed-line bypass of carry path (R1)"
```

---

## Task 5: Pin unknown-event fall-through in `RunState.handle_event`

**Files:**
- Test: `tests/unit/test_parser.py` (add new class `TestRunStateUnknownEvent` after `TestJsonLineStreamCarryBuffer`)

R1's spec calls out: "Treat any `_event` value not in the known dispatch map as a 'warning at DEBUG, ignored' — already true in `RunState.handle_event` but worth pinning with a test so it stays that way." We add tests only — no production change. This guards the contract that R5 (which adds an unknown-events counter on top) must preserve.

- [ ] **Step 5.1: Confirm the existing fall-through behaviour by reading the source**

Run: `grep -n "Unknown event type\|handler_map\|else:" src/ansible_aom/core/models.py | head -20`
Expected: shows `handler_map.get(event_type)` followed by `if handler:` and `else:` / `logger.debug(f"Unknown event type: ...")`. The unknown branch only logs at DEBUG and never touches state.

- [ ] **Step 5.2: Write the pinning tests**

Add this class to `tests/unit/test_parser.py` immediately after `TestJsonLineStreamCarryBuffer`:

```python
class TestRunStateUnknownEvent:
    """R1 pin: an unknown _event value reaches RunState.handle_event without
    raising and does not mutate state. The existing implementation logs at
    DEBUG and returns; this test stops a refactor from quietly changing that
    contract (e.g. R5 will later add a counter on top of the same branch)."""

    def test_unknown_event_does_not_raise(self):
        state = RunState(playbook="test.yml")
        # Should not raise.
        state.handle_event({"_event": "v2_playbook_on_include", "foo": "bar"})

    def test_unknown_event_leaves_plays_empty(self):
        state = RunState(playbook="test.yml")
        state.handle_event({"_event": "v2_some_future_event"})
        assert state.plays == {}

    def test_unknown_event_does_not_set_start_time(self):
        state = RunState(playbook="test.yml")
        state.handle_event(
            {
                "_event": "v2_some_future_event",
                "_timestamp": "2026-04-20T10:00:00Z",
            }
        )
        assert state.start_time is None
        assert state.status == Status.PENDING
```

`RunState` and `Status` are already imported at the top of the test file (see lines 22-31 of the existing import block). If you've reordered the file and they aren't, add them to the existing `from ansible_aom.core.models import (...)` block.

- [ ] **Step 5.3: Run the new tests — must pass without any production change**

Run: `uv run pytest tests/unit/test_parser.py::TestRunStateUnknownEvent -v`
Expected: 3 passed. If any test fails, stop — that means the existing fall-through behaviour is not what the spec assumes, and we need to investigate before continuing (the spec explicitly says R1 should not change `RunState`).

- [ ] **Step 5.4: Commit**

```bash
git add tests/unit/test_parser.py
git commit -m "test(state): pin unknown-_event fall-through in handle_event (R1)"
```

---

## Task 6: Final verification

The plan is intentionally bite-sized; this last step is the "is everything still green together" guard the project's CLAUDE.md mandates after every change.

- [ ] **Step 6.1: Run the full unit suite**

Run: `uv run pytest tests/unit/ -q`
Expected: all tests pass. No new failures introduced.

- [ ] **Step 6.2: Run the full test suite**

Run: `uv run pytest tests/ -q`
Expected: all tests pass.

- [ ] **Step 6.3: Run linters and type checker**

Run: `uv run ruff format && uv run ruff check --fix && uv run mypy src/ansible_aom`
Expected: no formatting changes (or only the new code being formatted), no lint errors, no mypy errors. The carry-buffer change uses only stdlib types and a single `str` attribute — mypy should accept it without any annotation gymnastics.

- [ ] **Step 6.4: Commit any formatting fixups (if `ruff format` changed anything)**

If `ruff format` modified files:

```bash
git add -u
git commit -m "chore(parser): apply ruff format to R1 carry-buffer changes"
```

If nothing changed, skip the commit.

---

## Done

R1 is complete when:
- `JsonLineStream` has a `_carry: str` attribute and `_CARRY_LIMIT = 1_000_000` class constant.
- A JSONL event split across N `feed_line` calls yields exactly one event on the final call.
- A partial larger than 1 MB is dropped, the carry is cleared, and the next well-formed line parses standalone.
- `RunState.handle_event` is unchanged; three pin tests guarantee unknown events don't raise and don't mutate state.
- All tests in `tests/` pass; ruff and mypy are clean.

Out of scope (do not add): schema validation of event payloads, metrics on carry usage, surfacing carry events to the renderer, the R5 unknown-events counter, the R2 `msg`-truncation cap. Each of those is its own slice in `.sisyphus/notepads/plans/robustness.md`.
