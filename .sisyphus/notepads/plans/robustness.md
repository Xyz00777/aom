# Robustness hardening plan

**Goal:** *Best-effort continuation — even when something weird happens.*

The TDD foundation already covers a lot of happy-path and named-edge
behaviour. This plan is about the **unspecified weird** cases: a JSONL
line gets truncated mid-write, a host returns a 500 MB stdout blob, a
plugin emits a custom event AOM has never seen, the locale is broken,
the user's terminal is 40×10, the disk fills up. None of these should
crash AOM. The user should always reach the final summary, even if
the picture is incomplete.

The catalogue below lists the gaps **in priority order**. Each entry
follows the same shape: **Symptom → Root cause → Fix → Tests** so each
one can ship as its own TDD slice.

---

## R1. Corrupted / partial JSONL mid-stream

**Priority:** high — most likely real-world failure mode (network
hiccup, callback bug, host with very long output truncated by buffering).

**Symptom.** A line arrives that starts with `{` but ends mid-string,
or contains a `_event` value AOM doesn't know. Today
`JsonLineStream.feed_line` logs and drops; `PtyStreamParser._is_json`
silently returns False; `RunState.handle_event` falls through to
`logger.debug`. No tests pin behaviour for *truncated-but-syntactically-
restartable* JSON.

**Root cause.** The parser is line-oriented. If pexpect splits a
JSONL event across two reads (common on long `stdout` results), the
first half is bad-JSON-dropped and the second half is bad-JSON-dropped.
We never re-join.

**Fix.**
1. Add a *carry buffer* to `JsonLineStream`: if a line starts with `{`
   but `json.loads` fails with `Unterminated string` / `Expecting...`,
   stash the partial in `self._carry` and prepend it to the next line
   before parsing. Cap the buffer at, say, 1 MB — if a single event
   really is larger than that, log + drop, don't OOM.
2. Treat any `_event` value not in the known dispatch map as a
   "warning at DEBUG, ignored" — already true in `RunState.handle_event`
   but worth pinning with a test so it stays that way.

**Tests** (`tests/unit/test_parser.py`):
- TC: `feed_line("{\"_event\":\"x\",\"msg\":\"hel")` returns `[]`
  (no event yet), and the *next* call with `"lo\"}"` yields the
  full event.
- TC: same scenario with 100 chunks all 10 chars apart.
- TC: carry buffer overflow (>1 MB) drops without raising.
- TC: unknown `_event` value reaches `RunState.handle_event` without
  raising; existing state is unmodified.

**Estimated size:** ~80 LoC + ~120 test LoC. One slice.

---

## R2. Very long task output / runaway hosts

**Priority:** high — `register` + `debug` on a host that returns the
contents of `/var/log/messages` will hand AOM a single multi-MB JSONL
event today.

**Symptom.** No crash, but: the renderer's log path
`self._display.print_log(...)` calls Rich's `print` on a huge string,
which can stall Textual's render thread; the session writer happily
serialises the full payload to `events.jsonl`, ballooning disk usage;
the parser's `_plaintext_lines: list[str]` grows unbounded.

**Root cause.** No size limits anywhere along the path.

**Fix.**
1. In `compact/renderer.py::_emit_event_log`, cap any printed `msg`
   field at e.g. 4 KB with a `… (truncated, N bytes)` suffix. The
   full payload still lands in `events.jsonl`, so `aom inspect show`
   can dump it later.
2. In `core/parser.py`, cap `_plaintext_lines` at the same 50 000
   line bound the log panel uses (move the constant to `core/state`
   so it's shared).
3. In `core/session.py::record_event`, optionally gzip-rotate
   `events.jsonl` when it exceeds, say, 100 MB. Probably out of
   scope for this pass — note it.

**Tests:**
- TC: event with `msg` = 1 MB string is logged with `…(truncated`
  suffix; renderer doesn't slow down measurably (no assertion on
  time, just that it returns).
- TC: 60 000 plaintext lines produces exactly 50 000 retained
  entries.

**Estimated size:** ~40 LoC + ~80 test LoC.

---

## R3. Disk-full mid-run

**Priority:** medium — already handled at `start_session`, not at
`record_event`. A run that fills the disk **partway** will start
raising on every event.

**Symptom.** `SessionManager.record_event` does `open(path, "a")` and
re-raises any OSError. `_SessionSink.record_event` already catches
that, but the catch logs `at DEBUG` per event — at 1000 events/sec
that's a flood and we keep retrying the broken disk.

**Fix.**
1. `_SessionSink` learns to **disable itself on the first OSError**:
   set a `_disabled = True` flag in the except branch; every
   subsequent call returns immediately. Renderer still gets every
   event; recording just stops mid-run.
2. Add a one-time `[WARNING] session recording disabled (disk
   write failed: ...)` line to `renderer.add_warning` so the user
   sees it in the panel, not just in debug logs.

**Tests** (`tests/integration/test_runner_session_recording.py`):
- TC: patch `SessionManager.record_event` to raise OSError on the
  3rd call; run produces a session dir with only 2 events recorded,
  exit code remains 0, renderer.add_warning is called exactly once
  with a "session recording disabled" message.

**Estimated size:** ~30 LoC + ~50 test LoC.

---

## R4. Terminal smaller than minimum

**Priority:** medium — spec says 24×80 minimum, behaviour today is
"render anyway and let Rich wrap badly".

**Symptom.** On an 8×40 terminal the compact panel wraps the status
bar across 3 lines and `_row_count()` undercounts, so the next refresh
leaves stale ghost lines.

**Fix.**
1. `compact/display.py::start()` reads
   `shutil.get_terminal_size()`. If `(cols, rows) < (80, 24)`, print
   a one-line warning **outside any DEC frame** and **degrade
   gracefully**: turn off the live panel entirely, fall back to a
   plain log-only stream.
2. SIGWINCH handler (already exists for `_row_count` self-heal)
   re-checks the size; if a previously-small terminal grows past
   the threshold, re-enable the live panel.

**Tests:**
- TC: `Display.start(force_size=(40, 8))` enters degraded mode;
  `_live` is None; `update()` falls through to `print`.
- TC: SIGWINCH to (120, 40) re-enables the panel.

**Estimated size:** ~50 LoC + ~80 test LoC.

---

## R5. Unknown ansible-playbook event types

**Priority:** medium — ansible-core occasionally adds new `_event`
values across minor versions. Today they hit `logger.debug` and
disappear.

**Symptom.** A new `v2_playbook_on_include` event (real example from
ansible-core 2.21) arrives; AOM processes nothing. The user sees no
indication that something happened.

**Fix.**
1. `RunState._unknown_events: dict[str, int]` counts each unknown
   `_event` name.
2. On `v2_playbook_on_stats` (end of run), the renderer surfaces a
   one-line summary `(N unknown events: foo×3, bar×1)` if any were
   seen — visible-but-quiet.

**Tests:**
- TC: 3 events with `_event="v2_playbook_on_include"` increment the
  counter; the final completion line includes a summary fragment.

**Estimated size:** ~30 LoC + ~50 test LoC.

---

## R6. Encoding edge cases (non-UTF-8 locale, mojibake)

**Priority:** low — already partially handled (ASCII fallback when
`LANG`/`LC_*` aren't UTF-8). But: a single task `msg` containing
invalid UTF-8 bytes today gets `codec_errors="replace"`'d by pexpect.
That's a renderer-only concern; the bytes are still on disk as `?`
characters.

**Symptom.** `aom inspect show` later shows `???????` where the
original payload was.

**Fix.**
1. Switch pexpect to `codec_errors="surrogateescape"` so the bytes
   round-trip into `events.jsonl` losslessly.
2. The renderer still does `.encode("utf-8", "replace").decode()`
   before display — surrogates can't render.

**Tests:**
- TC: feed a fake-ansible-command that emits a UTF-8-invalid byte
  sequence; on-disk `events.jsonl` round-trips byte-exact;
  renderer's printed line contains `?` not surrogate codepoint.

**Estimated size:** ~20 LoC + ~40 test LoC. Tricky to set up
because pexpect's encoding is configured at spawn time.

---

## R7. Ctrl-C race with completion

**Priority:** low — already mostly handled, has one race.

**Symptom.** User hits Ctrl+C *between* the playbook finishing and
`handle_completion` returning. The KeyboardInterrupt handler runs,
sends SIGINT to a child that no longer exists, sets exit 130 over
the real exit code.

**Fix.** Wrap the `_drive` return value in a local and check it
before unconditionally returning 130 from the KeyboardInterrupt
branch — if the child exited cleanly first, return its real code.

**Tests:** none that pin this without flakiness; document as a known
limitation. Could add a unit test that mocks the timing.

**Estimated size:** ~10 LoC. Skip unless someone hits it.

---

## R8. Hangs on the wait-for-EOF

**Priority:** low — if ansible-playbook leaves an orphan grandchild
holding the PTY open (rare with become_user nested forks), pexpect
sits on EOF forever.

**Fix.** After receiving a `v2_playbook_on_stats` event, start a
30-second EOF watchdog. If EOF doesn't fire within that window,
log a warning and treat it as a synthetic EOF.

**Estimated size:** ~30 LoC + ~50 test LoC.

---

## Suggested execution order

The blast-radius order, not the difficulty order:

1. **R1** (corrupted JSONL) — most common real failure, smallest
   blast radius if we get it wrong.
2. **R2** (long output) — second most common, also visible.
3. **R3** (disk-full) — silent today, easy to hit on small CI.
4. **R5** (unknown events) — easy slice, raises visibility for
   future-version drift.
5. **R4** (small terminal) — quality-of-life, well-defined.
6. **R6/R7/R8** — defer until someone hits them in the wild.

R1 + R2 + R3 + R5 is one good "robustness pass" pull request:
~180 LoC of source, ~300 LoC of tests, all TDD, all green.
