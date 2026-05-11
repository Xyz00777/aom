# Feature plans — detailed slices

Six features, ordered by **expected user impact divided by effort**.
Each entry is a fully-specified slice: scope, design, test outline,
risks, estimated size. Pick any one off the top of the stack and it
ships in a single TDD session.

---

## F1. Live TUI widget refresh (the missing piece from roadmap #9)

**Why first.** Roadmap #9 wired the runner into a Textual worker but
left the widgets inert — the `MainScreen` is mounted, state mutates
on every event, but nothing on screen actually changes during a run.
The plumbing is in; we just need to pulse the widgets.

**Scope.**
- A periodic refresh (e.g. `set_interval(0.2, self._refresh_widgets)`
  in `AOMApp.on_mount`) reads `self.run_state` and calls
  `MainScreen.update_from_state(self.run_state)`.
- `add_warning` and `print_log` also nudge the screen: a `Counter`
  reactive on `MainScreen` ticks each call, log_lines feed into
  `LogPanel.write_line` via `call_from_thread`.
- TaskTree gains a `populate_from_definitions(defs)` method called
  the first time `set_definitions` lands; subsequent state changes
  update node icons in place.

**Design notes.**
- Don't mutate widgets from the worker thread. Use `call_from_thread`
  inside `add_warning` / `print_log` / `update_state` to schedule a
  small "dirty" flag; the periodic refresh consumes the flag.
- 0.2s tick is enough; nom uses ~200ms. Battery-friendly.
- Final state (after `handle_completion`) does one last refresh and
  changes the title to include the exit indicator (✓ / ✖).

**Tests.**
- Pilot test mounts the app, feeds three task_start events, asserts
  `TaskTree` has three nodes after one tick. (`pilot.pause(0.3)`.)
- Pilot test feeds an `add_warning` call from a worker thread,
  asserts the warning count in the `StatusBar` widget updates.
- Existing `tests/tui/test_panels.py` still passes — these are data
  layer tests, unaffected.

**Risks.**
- Race between the dirty-flag write (worker) and read (UI tick).
  Use `threading.Event` or just an `int` counter — Python's GIL
  covers single int writes.
- Textual's `set_interval` callbacks are async; widget query inside
  them can throw if the screen isn't mounted yet — guard with
  `if not self.is_mounted: return`.

**Size.** ~150 LoC src + ~200 LoC tests. One slice.

---

## F2. `aom replay <session-id>` — turn the recorder into a time machine

**Why second.** The session writer is already shipping in every run
(roadmap #14). Adding a replay command means every recorded session
becomes a watchable nom-style stream — great for post-mortems,
demoing runs without re-running them, and **regression-testing the
renderer** against real production output.

**Scope.**
- New subcommand: `aom replay <session-id> [--speed N] [--compact|--tui]`
- Reads `~/.local/state/aom/sessions/<id>/events.jsonl` and the
  matching `meta.json`.
- Feeds events into the renderer of choice at the configured speed
  (default: 1× real time using the `_timestamp` deltas; `--speed
  10` = 10× faster; `--speed 0` = as-fast-as-possible).
- `meta.json["status"]` chooses the final completion state.

**Design notes.**
- Implement as a new `ReplaySource` parallel to `runner.run_playbook`:
  shares the renderer interface, no pexpect. Lives in
  `src/ansible_aom/replay.py`.
- Speed control: between events, `time.sleep(delta * (1 / speed))`
  where `delta` comes from consecutive `_timestamp` fields.
- `Ctrl+C` mid-replay = stop and call `handle_completion(130,
  "crashed")` like the runner does.
- The `--compact` / `--tui` flags reuse the renderer factory.
- Inventory autodetect, preflight, and password-prompt logic are
  all skipped — `set_definitions` gets reconstructed from the
  recorded events instead (every play_start / task_start in the
  JSONL is enough to repopulate the tree).

**CLI integration.**
- Add to `aom`'s argparse dispatcher (alongside the `inspect`
  branch in `cli.main`).
- Help epilog gains one line: `aom replay <id> [--speed N]`.

**Tests.**
- Unit: given a fake `events.jsonl` with 3 events, replay calls
  `renderer.update_state` exactly 3 times in order; final
  `handle_completion` is called with the meta status.
- Unit: `--speed 0` produces no sleeps (mock `time.sleep`, assert
  zero calls).
- Unit: `--speed 2` halves sleep durations vs `--speed 1`.
- Integration: record a fake run via `run_playbook` against a
  stub-event generator, then immediately replay it — both produce
  the same renderer call sequence.

**Risks.**
- Timestamps in real ansible JSONL are sometimes out of order
  (events buffered in different threads). Guard `delta < 0` →
  treat as 0.
- Very long sleeps (a real 8-hour run replayed at 1×) — document
  `--speed` as the answer; no UI work needed.

**Size.** ~200 LoC src + ~250 LoC tests. One slice.

---

## F3. `--no-record` opt-out

**Why third.** Small, addresses a real concern (every CI run writes
to disk; some users with sensitive playbooks don't want events
persisted at all). Logical follow-up to F2 since replay clarifies
what gets recorded.

**Scope.**
- New `--no-record` flag in `cli.create_parser`.
- Threaded through to `run_playbook(playbook, args, renderer,
  session_dir=None, record=True)` — when `record=False`, runner
  skips the `_SessionSink` instantiation entirely.
- `AOMApp.__init__` gains the same `record: bool = True` flag,
  forwarded to its worker.

**Tests.**
- Unit: `aom --no-record site.yml` produces no session directory
  under `session_dir` after the run.
- Unit: `aom site.yml` (default) still writes one (existing test
  unchanged).
- CLI test: `--no-record` propagates through to the runner.

**Risks.** None substantial. Watch out: `--no-record` is *only* the
session writer; debug logs from `--verbose` are unaffected.

**Size.** ~30 LoC src + ~60 LoC tests. Half a slice; could ride
along with F2 if delivered together.

---

## F4. `aom rerun --failed` — retry only what broke

**Why fourth.** Best UX win on long playbooks where one task per host
fails. The compact recap already lists `FAILED: web2 — Install
nginx`; this turns that list into an action.

**Scope.**
- New subcommand: `aom rerun [<session-id>] [--failed] [--unreachable]
  [--changes-only]`.
- Reads the last completed session (or the named one) from
  `~/.local/state/aom/sessions/`.
- Derives a host list from the recorded failures.
- Re-invokes `ansible-playbook` with `--limit web2,web3` (and the
  original tags/extra-vars from meta) so only the broken hosts
  re-run.
- Same renderer flow as `aom <playbook>`.

**Design notes.**
- `core/session.load_session` already parses the events; add a
  pure helper `collect_failed_hosts(session) -> set[str]` and
  `collect_unreachable_hosts(session) -> set[str]`.
- The hardest part is meta accounting: we need to know which
  playbook to re-run. Add `playbook` + `original_args` to
  `meta.json` (already storing `playbook`; just need to add
  `ansible_args`).
- Confirm-before-run: print the limit string and ask Y/n unless
  `--yes`.

**Tests.**
- Unit: `collect_failed_hosts` against fixture session → exact set.
- Unit: `--unreachable` includes both UNREACHABLE and FAILED hosts
  (`UNREACHABLE` is a strict subset of "things to retry").
- Unit: rerun command line construction includes `--limit web2,web3`
  and forwards original tags.
- Integration: fake session with 2 failed hosts → rerun launches
  with the right limit string.

**Risks.**
- Some failures are deterministic (bad config) and re-running won't
  help. That's the user's call; AOM shouldn't second-guess.
- Hosts that *succeeded* on the first run can change state if the
  rerun happens hours later. Document that `rerun` is a convenience,
  not a transaction.

**Size.** ~250 LoC src + ~300 LoC tests. One slice.

---

## F5. Shell completion (`aom --install-completion bash|zsh|fish`)

**Why fifth.** Tab-complete for `--tui`, `--verbose`, `inspect` /
`replay` / `rerun`, *and* live tag/host completion from the nearest
inventory. Punches above its weight for power users.

**Scope.**
- Use `argcomplete` (already a Python stdlib-adjacent convention).
- Add `argcomplete.autocomplete(parser)` at the top of
  `cli.create_parser`.
- New flag `aom --install-completion <shell>` emits the appropriate
  rc-file snippet to stdout for the user to source.
- Custom completer for session IDs: lists `~/.local/state/aom/
  sessions/*` and returns IDs.
- Optional ambitious bit: a completer for `--tags` that runs
  `--list-tasks` against the current playbook and feeds the tag set.

**Tests.**
- Unit: `aom --install-completion bash` prints a snippet containing
  `complete -F` and the program name.
- Unit: session-id completer with a populated fake state-dir
  returns expected list.
- Skip integration tests — they'd need a real shell.

**Risks.**
- `argcomplete` adds a runtime dependency; tiny package though.
- Tag-completion is potentially slow (it runs --list-tasks) — cache
  per-cwd-per-playbook with mtime check.

**Size.** ~150 LoC src + ~150 LoC tests.

---

## F6. JSON / JSONL output mode (`aom --format json`)

**Why sixth.** CI-friendliness. The compact view is nice for humans;
machines want structure.

**Scope.**
- New flag: `--format {compact,json,jsonl}` (default `compact`).
- `json`: at end of run, emit a single object to stdout with
  `playbook`, `exit_code`, `started_at`, `ended_at`, `duration_s`,
  `hosts: {hostname: {ok, changed, failed, unreachable}}`,
  `tasks_failed: [{host, task, msg}, ...]`. No streaming output.
- `jsonl`: stream one event per JSONL event, with AOM-added fields
  `aom_phase` / `aom_elapsed_s`. Useful for pipe-to-jq.

**Design notes.**
- New `JsonRenderer` / `JsonlRenderer` satisfying the Renderer
  Protocol. Lives in `src/ansible_aom/json_renderer.py`.
- Factory function `create_renderer(...)` gains the `format` arg
  (or rename `tui_mode` to `mode`).
- Status icons skipped; this is for `jq -r '.tasks_failed[].host'`.

**Tests.**
- Unit: feed fixture events to `JsonRenderer`; final output parses
  as JSON and has the expected schema.
- Unit: `JsonlRenderer` emits one object per `update_state` call.
- Unit: exit code matches `determine_exit_code(state)`.

**Risks.**
- Schema lock-in. Mark v0.1 schema with a `"schema_version": 1`
  field so we can evolve later.

**Size.** ~180 LoC src + ~250 LoC tests.

---

## Suggested execution order

| Order | Feature | Size | Why this slot |
|-------|---------|------|---------------|
| 1 | **F1** — live TUI refresh | M | Closes a known gap in #9; biggest single quality bump. |
| 2 | **F2 + F3** — replay + `--no-record` | M+S | Replay enables better test coverage of the renderer; `--no-record` is the obvious tag-along. |
| 3 | **F4** — `rerun --failed` | M | Best workflow improvement once replay exists. |
| 4 | **F6** — JSON output | M | Unlocks CI integrations; no UI risk. |
| 5 | **F5** — shell completion | S | Polish; bigger benefit once subcommands grow. |

F1 alone justifies the next pass — the TUI being inert is a real
papercut. F2 + F3 together makes a tight 1.5-day slice. After that,
F4 and F6 are independent and either order works.

---

## What's deliberately *not* on this list

- Multi-playbook orchestration. Out of scope (`ansible-pull` /
  `ansible-runner` already cover this).
- Web UI / HTTP server. Spec-out-of-scope.
- Editing playbooks from inside the TUI. Definitely not.
- Auto-detecting and grouping flapping hosts. Cute idea, no real
  signal that anyone wants it.
- Direct ansible-core integration (importing the library instead of
  shelling out). Would couple AOM to ansible's API and break the
  licensing pitch (MIT-safe-because-no-import). Stays out.
