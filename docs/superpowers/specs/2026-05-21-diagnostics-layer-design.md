# AOM Diagnostics Layer — Design Plan

**Status:** Proposed — implementation queued first (before perf plan).
**Date:** 2026-05-21
**Motivation:** Real 14-host, ~thousands-of-tasks run died with exit 139 (SIGSEGV) after AOM printed its preflight summary, before the first JSONL event flowed. AOM has almost no self-diagnostics today (`--verbose` and `AOM_TRACE=1`), so we cannot tell whether the fault was in pexpect, psutil, or somewhere else. This plan adds a deliberate diagnostics layer so the *next* time something breaks, the user can flip a switch, re-run, and we get the data we need without guessing.

## 1. What we want answered, by failure class

**Exit 139 (SIGSEGV) in C extension.** `faulthandler` C-level traceback pointing to a specific frame (pexpect, blessed, Rich's C accelerators). Without it we only know "something blew up in native code." The critical signal is the fault address and the Python frame stack at the moment of the fault.

**OOM / unbounded memory growth.** Max RSS at completion vs. at spawn; `tracemalloc` top-N allocators if enabled. The critical signal is peak RSS delta from process start to first-JSONL-event vs. total.

**Render storm (event rate overwhelms the render loop).** Events-received counter vs. render-call counter; wall-clock time between `update_state` calls. If `events_received >> render_calls` the driver is being throttled somewhere unexpected. Also: how many events arrived before AOM crashed, and what was the last event type.

**ansible-playbook itself misbehaved (bad exit, wrong callback).** Raw exit code at subprocess close, the value of `ANSIBLE_STDOUT_CALLBACK` as AOM set it, and any stderr captured before the first JSONL event. Did we get *zero* JSONL events, and if so what was in stderr? This distinguishes "callback not installed" from "crash before first event."

**Prompt misdetection (playbook blocks waiting for stdin).** `AOM_TRACE_PEXPECT=1` already covers this. The gap is we do not record which stall branch fired and how many consecutive TIMEOUTs elapsed before it. Adding `stall_count` to the lifecycle marks closes that.

**Session-write errors.** `_SessionSink._disable` is called but nothing is persisted. We need the disable reason and the event index at which recording stopped. Currently that only goes to `logger.debug` (silent unless `--verbose`).

## 2. Diagnostic surface

| Name | Default | What it produces | Where it lands | Cost-when-off | Cost-when-on |
|------|---------|-----------------|----------------|---------------|--------------|
| `faulthandler` (unconditional) | always on | C-level stack on SIGSEGV/SIGFPE to stderr | stderr | single `faulthandler.enable()` syscall at import; negligible | — |
| `AOM_WATCHDOG=<secs>` | off | `faulthandler.dump_traceback_later` periodic dump | stderr (fd 2) | zero | one timer thread + periodic write to stderr |
| `AOM_DEBUG=1` | off | DEBUG logger, lifecycle marks (9 named checkpoints), `RendererStats` at exit | stderr | zero (env check once) | ~1 μs per mark; one `getrusage` call at exit |
| `AOM_TRACE_PEXPECT=1` | off | per-loop pexpect transition (rename of `AOM_TRACE`) | stderr | zero | one `write` per pexpect iteration |
| `AOM_TRACE=1` | off | alias for `AOM_TRACE_PEXPECT=1` for one release; emits deprecation note once | stderr | zero | — |
| `AOM_TRACE_EVENTS=1` | off | event type + running counter every 100 events | stderr | zero | one counter increment per event |
| `AOM_PROFILE=1` | off | `cProfile` of `_drive` loop | `~/.local/state/aom/profile/<session_id>.pstats` | zero | profiler overhead ~5-10% |
| `AOM_TRACEMALLOC=1` | off | `tracemalloc` top-20 snapshot at completion | stderr | zero | ~10% memory overhead |
| `diagnostics.json` | written when session is recorded | counters, lifecycle timestamps, RSS, env vars | session dir next to `meta.json` | written only on recording path; cheap | always written when recording is on |

**Rename decision:** `AOM_TRACE` becomes an alias for `AOM_TRACE_PEXPECT` for one release cycle. Both names are checked in `_trace_enabled()`. After one release the alias is removed.

**Overlap with `--verbose`:** `--verbose` sets `logging.DEBUG` and prints a one-time env dump. Under the new plan `AOM_DEBUG=1` does the same plus lifecycle marks. The two are orthogonal: `--verbose` is for the argparse path, `AOM_DEBUG=1` works for all entry points including `aom inspect`, `aom replay`, and the TUI. `--verbose` should continue to work unchanged; internally it calls `diagnostics.activate_debug()` so both paths share the same code.

## 3. Module layout

**New file: `src/ansible_aom/core/diagnostics.py`**

Pure module, zero I/O imports at module scope (I/O calls happen inside functions gated on flags). Responsibilities:

- Parse all `AOM_*` env vars once, expose boolean flags and validated values.
- `install_from_env()` — entry point called by every composition root; idempotent.
- `enable_faulthandler()` — wraps `faulthandler.enable()` and optionally `dump_traceback_later`.
- `lifecycle_mark(name)` — logs a named timestamp if `AOM_DEBUG` active; no-op otherwise.
- `RendererStats` dataclass — fields: `events_received`, `render_calls`, `log_writes`, `state_size_bytes`, `max_rss_kb`. Pure value object.
- `collect_stats(state, renderer) -> RendererStats` — called at completion.
- `build_diagnostics_record(stats, lifecycle_marks, env_snapshot) -> dict` — builds the JSON-serialisable dict for `diagnostics.json`. Pure.

Does NOT import: `compact`, `tui`, `renderer`, `ansible`, `session`, `drivers`, `inspect`, `rerun`.

**Call sites (thin wrappers, 1-3 lines each):**

- `src/ansible_aom/cli.py` — call `diagnostics.install_from_env()` at the top of `main()`, before any imports of infrastructure packages.
- `src/ansible_aom/ansible/runner.py` — call `lifecycle_mark` at: preflight-start, preflight-end, spawn, first-event, last-event, completion. Also pass the `session_id` to the diagnostics record writer at `_SessionSink.end()`.
- `src/ansible_aom/compact/renderer.py` — increment `RendererStats.render_calls` in `_render_status_panel`; increment `log_writes` in `print_log`; read `state_size_bytes` via `sys.getsizeof` at completion.
- `src/ansible_aom/session/store.py` — write `diagnostics.json` in `end_session()`; read it back in `load_session()`.
- `src/ansible_aom/inspect/cli.py` — `install_from_env()` call; add `--debug` flag that reads and displays `diagnostics.json`.
- `src/ansible_aom/drivers/replay.py` and `src/ansible_aom/drivers/live.py` — `install_from_env()` when these are the composition root (replay path).

**Why `core/` for this:** `RendererStats`, `build_diagnostics_record`, `lifecycle_mark` are all pure computation. `install_from_env` itself only reads `os.environ` and calls `faulthandler`/`tracemalloc` stdlib — no pexpect, no Rich, no Textual. Placing it in `core/` lets both `compact` and `tui` paths share it without either needing to know about the other.

## 4. Lifecycle

`install_from_env()` runs once at process start. It is idempotent via a module-level `_installed: bool` guard.

**What it installs:**

1. `faulthandler.enable(file=sys.stderr)` — unconditional (always, before any subprocess is spawned).
2. If `AOM_WATCHDOG=N`: `faulthandler.dump_traceback_later(N, repeat=True, file=sys.stderr)`.
3. If `AOM_DEBUG=1`: sets `logging.getLogger("ansible_aom")` to DEBUG, registers `atexit` handler to call `_dump_lifecycle_marks()`.
4. If `AOM_TRACEMALLOC=1`: `tracemalloc.start()`.
5. If `AOM_PROFILE=1`: constructs a `cProfile.Profile()` stored as `_profiler` module-level.

**Teardown:**

- `faulthandler` stays active until process death — no teardown needed.
- `AOM_WATCHDOG` timer is cancelled in an `atexit` handler to avoid a spurious dump after clean exit.
- `AOM_PROFILE` profiler is stopped and dumped in `finally` of `_drive()` in `runner.py`, not in `atexit`, so the dump captures the right scope.
- `AOM_TRACEMALLOC` snapshot taken in the `stop()` method of `CompactRenderer` and `AOMApp`.

**KeyboardInterrupt survival:** `faulthandler` and `AOM_WATCHDOG` survive because they operate at the OS/C level. The `atexit` handler for lifecycle marks also fires on clean SIGINT (Python's `KeyboardInterrupt` path propagates through `finally` blocks). If the process receives a bare `SIGKILL` or `SIGTERM` without `KeyboardInterrupt`, the watchdog timer is the only thing that fires.

**Uniform across entry points:**

- `aom <playbook>` → `cli.main()` calls `install_from_env()`.
- `aom inspect` → `inspect/cli.main()` calls `install_from_env()`.
- `aom replay` → `drivers/replay.cli_main()` calls `install_from_env()`.
- `aom rerun` → `rerun/cli.main()` calls `install_from_env()`.
- TUI path: same as compact — `cli.main()` covers it.

## 5. Session-recorded diagnostics

**File:** `<session_dir>/<session_id>/diagnostics.json`

**Schema (version 1):**

```json
{
  "schema_version": 1,
  "session_id": "<uuidv7>",
  "aom_version": "<version string>",
  "lifecycle": {
    "preflight_start_ms": 1716300000000,
    "preflight_end_ms":   1716300001200,
    "spawn_ms":           1716300001350,
    "first_event_ms":     1716300002100,
    "last_event_ms":      1716300045000,
    "completion_ms":      1716300045050
  },
  "counters": {
    "events_received": 4821,
    "render_calls": 312,
    "log_writes": 14,
    "pty_bytes": 198432,
    "stall_count_max": 3,
    "pexpect_timeouts": 88,
    "session_recording_disabled": false,
    "session_disable_reason": null
  },
  "resources": {
    "max_rss_kb": 84320,
    "tracemalloc_peak_kb": null
  },
  "event_histogram": {
    "v2_playbook_on_task_start": 4200,
    "v2_runner_on_ok": 400,
    "v2_runner_on_failed": 21,
    "v2_playbook_on_stats": 1
  },
  "env_snapshot": {
    "ANSIBLE_STDOUT_CALLBACK": "ansible.posix.jsonl",
    "TERM": "xterm-256color",
    "AOM_DEBUG": "1"
  },
  "host_count": 14,
  "playbook_task_count": 1200
}
```

`event_histogram` is always computed from the JSONL stream regardless of debug flags — it is cheap (one dict increment per event) and high-value for post-mortem. All other fields default to `null` when the corresponding feature was off.

**`aom inspect --debug <session>`** (new flag):

Reads `diagnostics.json` from the session dir and prints:

1. Lifecycle timeline with ms deltas between marks.
2. Event-type histogram sorted by count descending.
3. Resource summary (RSS, stall max, timeouts).
4. Any env vars that differ from current environment.
5. If `session_recording_disabled=true`, the reason.

Backward compatibility: if `diagnostics.json` is absent (session predates this feature), `inspect --debug` prints "No diagnostics available for this session (recorded before v<X>)." `load_session()` in `session/store.py` returns `diagnostics=None` in that case and all callers must guard on `None`.

## 6. Sequence and dependencies

**Phase 1 — Foundation (parallel-shippable, zero risk to existing behavior).** Implement `core/diagnostics.py`: env parsing, `install_from_env`, `faulthandler`, `lifecycle_mark`, `RendererStats`, `build_diagnostics_record`. Pure module, no call sites yet. Tests prove it is a no-op with no env set.

**Phase 2 — Faulthandler hookup (tiny blast radius).** Add `install_from_env()` call at the top of `cli.py` main, `inspect/cli.py` main, `drivers/replay.py` cli_main, `rerun/cli.py` main. Also `AOM_TRACE_PEXPECT` alias in `runner.py`. These are one-liner additions; tests confirm faulthandler is enabled.

**Phase 3 — Lifecycle marks in runner (medium risk, only adds log calls).** Add the 6 `lifecycle_mark` calls in `runner.py`. Add `event_histogram` counter in `_feed`. Add stall/timeout counters. Tests drive these through a fake `pexpect.spawn` and assert marks were recorded.

**Phase 4 — RendererStats collection in CompactRenderer (medium risk).** Add counter increments in `_render_status_panel`, `print_log`, `update_state`. Wire `collect_stats` call in `stop()`. Tests patch a renderer through its protocol and assert counters match event feed.

**Phase 5 — diagnostics.json write/read (independent of Phase 4, but needs Phase 3 counters).** `SessionManager.end_session()` calls `build_diagnostics_record()` and writes `diagnostics.json`. `load_session()` reads it. Tests round-trip the JSON schema.

**Phase 6 — `aom inspect --debug` (needs Phase 5).** Add `--debug` flag to `inspect/cli.py`. Implement the text formatter in `inspect/formatters.py`. Tests assert the histogram is printed correctly for a known `diagnostics.json` fixture.

**Phase 7 — Optional profiling and tracemalloc (highest risk, last).** `AOM_PROFILE=1` and `AOM_TRACEMALLOC=1` wiring. These involve `cProfile` and `tracemalloc` which have non-trivial overhead. Tests use a tiny synthetic run to verify the pstats file is created.

**Parallel with perf-improvement spec:** Phases 1 and 2 are purely additive and touch no hot paths. Phases 3-5 add counters that do one integer increment per event — compatible with any perf work that doesn't restructure `_feed`. The two efforts must coordinate only if perf restructures `_drive` or `_feed` signatures.

## 7. Tests to write first (TDD-first order)

**`tests/unit/test_diagnostics.py`** (Phases 1-2)

- `TC-D01`: `install_from_env()` with empty env is a complete no-op — `faulthandler` is enabled, no watchdog thread created, logger level unchanged, `tracemalloc` not started.
- `TC-D02`: `AOM_WATCHDOG=5` calls `faulthandler.dump_traceback_later` with `timeout=5`. Patching `faulthandler.dump_traceback_later` and asserting it was called with the right args.
- `TC-D03`: `AOM_DEBUG=1` sets `ansible_aom` logger to DEBUG.
- `TC-D04`: `lifecycle_mark` with `AOM_DEBUG=0` does nothing (mark list stays empty).
- `TC-D05`: `lifecycle_mark` with `AOM_DEBUG=1` records a mark with a monotonic timestamp. Two marks have non-decreasing timestamps.
- `TC-D06`: `build_diagnostics_record` returns a dict that passes `json.dumps` round-trip without error and contains all required top-level keys.
- `TC-D07`: `AOM_TRACE_PEXPECT=1` and `AOM_TRACE=1` both result in `_trace_enabled()` returning True (tests the alias).

**`tests/unit/test_faulthandler.py`** (Phase 2)

- `TC-D08`: `faulthandler.is_enabled()` is True after `install_from_env()` regardless of env vars. Safe to assert without triggering an actual segfault.

**`tests/unit/test_diagnostics_counters.py`** (Phase 3)

- `TC-D09`: Feed 50 events through `_feed` with `AOM_TRACE_EVENTS=1`; assert stderr captured 0 lines (counter logs every 100), then feed 50 more and assert one log line appears.
- `TC-D10`: `event_histogram` in `build_diagnostics_record` correctly counts event types from a list of 3 distinct types with varying frequencies.
- `TC-D11`: Stall counter increments logged at the right threshold.

**`tests/unit/test_diagnostics_json_roundtrip.py`** (Phase 5)

- `TC-D12`: `SessionManager.end_session()` writes `diagnostics.json`; `load_session()` returns `session["diagnostics"]` as a dict with `schema_version == 1`.
- `TC-D13`: Old session directory without `diagnostics.json` → `load_session()` returns `session["diagnostics"] == None`, no exception raised.

**`tests/unit/test_inspect_debug.py`** (Phase 6)

- `TC-D14`: `aom inspect --debug` with a session that has a known `diagnostics.json` fixture → stdout contains the event-type histogram header and the top event name.
- `TC-D15`: `aom inspect --debug` with a session missing `diagnostics.json` → prints the "no diagnostics available" fallback string, exits 0.

## 8. Out of scope / explicit non-goals

- Real-time OpenTelemetry/Prometheus export. The diagnostics layer writes to local files and stderr; no network sinks.
- Structured JSON logging for the renderer panel content (task names, host results). That would bloat the session artifacts and is a different concern from crash forensics.
- Any change to the on-disk `events.jsonl` or `meta.json` format — `diagnostics.json` is a separate side-car file, backward-incompatible session changes are out of scope.
- Per-event timing histograms with sub-millisecond precision (overkill; we only need event counts and lifecycle wall-clock marks).
- Anything that adds overhead on the `_feed` hot path beyond a single `dict.__setitem__` per event for the histogram counter.
- Crash reporters that send data to a remote endpoint.

## 9. Open questions

**OQ-1: Should `faulthandler.enable()` be unconditional?** The plan above makes it unconditional. The only argument against is theoretical: a future C extension that installs its own `SIGSEGV` handler and expects no competition. In practice `faulthandler` is compatible with all common Python extensions and the Linux signal stack. Recommendation: unconditional. If the user has a hard constraint (e.g., running inside a sanitizer harness), gate it on `AOM_DEBUG=1` or a dedicated `AOM_FAULTHANDLER=0` opt-out.

**OQ-2: Should `diagnostics.json` be written for all recorded sessions or only when `AOM_DEBUG=1`?** The plan writes it for all recorded sessions (it is cheap: one JSON write per run). The `event_histogram` alone is worth always-on because it answers "did we receive any JSONL events at all?" in post-mortem without `--debug`. If disk space is a concern on high-frequency CI machines, gate the richer fields (`env_snapshot`, `tracemalloc`) on `AOM_DEBUG=1` and always write the lean schema (lifecycle timestamps + histogram + counters). Recommendation: always-on for the lean schema, opt-in for the verbose fields.

**OQ-3: Alias removal timeline for `AOM_TRACE`.** The plan retains `AOM_TRACE` as an alias for one release. The `meta.json` version is `"1.2"` — if we increment to `"1.3"` on this feature landing, the alias can be dropped at `"1.4"`.
