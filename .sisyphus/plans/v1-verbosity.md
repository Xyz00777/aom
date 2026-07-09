# Plan: v1 Verbosity Handling + Verbose Capture

## Goal
Implement the v1 feature set for `ansible-aom`: capture verbosity-controlled output (JSONL verbose blocks + stderr verbose lines), redact secrets, expose in inspect TUI via context-sensitive `V` keybind, and add a multi-layer config system. Ship as the next minor release (`v0.x+1`).

## Approach
Phased by feature (8 phases). Each phase is a discrete PR. TDD-first: failing test → implementation → verification. Source docs and research are in `docs/brainstorms/2026-06-29-verbosity-handling.md` and `docs/brainstorms/2026-06-30-qc-review-triage.md`. The pre-implementation interview (with all decisions and revisions) is at `docs/brainstorms/2026-06-30-verbosity-pre-impl-interview.md`. Research reports are at `.sisyphus/notepads/2026-06-30-verbosity-pre-impl-interview/`.

## TODOs
- [x] Task 1.1: **Schema version bump** — Add `_schema_version: 2` to `meta.json` writer; reader defaults missing field to 1; test the v1 → v2 promotion path. (Phase 1 of v1 work; reverses Q9=B per QC-004.) — **DONE 2026-06-30**. +10 LOC in `src/ansible_aom/session/store.py`; new `tests/unit/test_meta_schema_version.py` with 6 tests (all pass; 1797/1797 unit tests pass; mypy clean; ruff clean).
- [ ] Task 2.1: **Redaction rewrite** — Replace substring-match redaction with ansible-core seed (exact-match keys: `password`, `vault_password`, `api_key`, `private_key`, `token`, `secret`, `passwd`, `ssh_pass`) + user-config regex layer; add red-team fixture `tests/fixtures/redaction_bypass.jsonl` with ~30 cases (redact + don't-redact); reframe `core/redaction.py` Layers 0/1/2 (Layer 0 = upstream `no_log: true`; Layer 1 = hard-coded; Layer 2 = user-config).
- [ ] Task 2.2: **Wire `redact_event` into the event pipeline** — `src/ansible_aom/core/redaction.py:280-283` Layer 4 is built but unwired. Connect it to where JSONL events are persisted, before `events.jsonl` write.
- [ ] Task 3.1: **Config refactor** — Add `pydantic-settings[yaml]` to `pyproject.toml`. New `core/config_layer.py` (~50 LOC, not 150-200): `find_config_paths()`, `merge_configs()`, `load_config_with_layers()`. Use `YamlConfigSettingsSource(yaml_file=[...], deep_merge=True)` + `settings_customise_sources`. Set `nested_model_default_partial_update=True` (critical gotcha). Multi-layer precedence: built-in defaults < `/etc/aom/aom_config.yaml` < `~/.config/aom/aom_config.yaml` < `./.aom_config.yaml` < `AOM_CONFIG` env < `--config` CLI < value CLI flags.
- [ ] Task 3.2: **Config file rename + auto-migration** — Rename `~/.config/aom/config.yaml` → `~/.config/aom/aom_config.yaml` (hard rename, no backward compat). On first run with new AOM, detect old file, migrate to new schema, move old to `config.yaml.migrated`.
- [x] Task 4.1: **Drop `stderr.log`** — Stop writing the file. Update `session/store.py:record_stderr` to call the classifier instead of writing to disk. Update read paths (the load in `src/ansible_aom/session/store.py:759-763` is no longer needed). — **DONE 2026-07-01**.
- [x] Task 4.2: **Stderr classifier** — New `core/stderr_classifier.py` (~80 LOC). `StderrSource` enum (12 values). `CLASSIFIER_RULES` list (30 regexes from `stderr-classification-taxonomy.md` Section 4). `classify(line: str) -> StderrEvent` (first match wins, extract `host` from `<hostname>` prefix). — **DONE 2026-07-01**.
- [x] Task 4.3: **Custom JSONL callback plugin** — New `src/ansible_aom/callbacks/aom_connection.py` (~80-100 LOC). Emits `aom_connection_acquired` (with `connection_id` UUID) on `v2_runner_on_start`; `aom_connection_released` on `v2_runner_on_ok/failed/unreachable/skipped`. Auto-loaded via `ANSIBLE_CALLBACK_PLUGINS` when AOM runs ansible-playbook. — **DONE 2026-07-01**.
- [x] Task 4.4: **Emit `aom_stderr_line` events** — Update `core/parser.py:_handle_plaintext`. Reuse existing warning/deprecation logic (lines 256-281). Add new else branch: classify the line, look up the most-recent `aom_connection_acquired` for the host, attach `connection_id` and `attribution_confidence` ("unique" or "ambiguous"), emit synthetic event via session sink. — **DONE 2026-07-01**.
- [x] Task 4.5: **Test fixtures** — JSONL event samples for each of the 12 source values; `aom_connection_acquired`/`released` events; overlapping async task scenarios for the attribution-confidence flag. — **DONE 2026-07-01**.
- [x] Task 5.1: **Global `--yes` flag** — Add to `create_parser()` in `src/ansible_aom/cli.py`. (Verified doesn't exist as global; only on `rerun` subcommand at `src/ansible_aom/rerun/cli.py:301-304`.) — **DONE 2026-07-01**.
- [x] Task 5.2: **Verbose-capture flags** — Add `--capture-verbose`, `--capture-setup`, `--no-redact`, `--no-failed-hint`, `--hide-warnings`, `--hide-deprecations`, `--config` to global parser. `--no-redact` requires `--yes` in non-TTY mode (per QC-003); interactive prompt in TTY. — **DONE 2026-07-01**.
- [x] Task 5.3: **Auto-set `ANSIBLE_CALLBACK_PLUGINS`** — When AOM runs ansible-playbook, set the env var to point at `src/ansible_aom/callbacks/` (so the connection-tracking plugin loads automatically). No user-visible flag. — **DONE 2026-07-01**.
- [x] Task 6.1: **Status bar `● REC+VC`** — When verbose capture is on, show in the bottom status bar of the compact mode.
- [x] Task 6.2: **Failed-hint** — For `failed`/`unreachable` tasks, show first line of `msg` (after redaction) in the compact log. Toggleable via `[live] show_failed_hint: true` (default).
- [x] Task 6.3: **Warnings + deprecations in live view** — Show by default with color coding (yellow / orange). Configurable via `[live] show_warnings: true`, `[live] show_deprecations: true`. CLI flags `--hide-warnings` and `--hide-deprecations`.
- [x] Task 7.1: **`V` keybind in inspect TUI** — Context-sensitive. Press `V` at host/play/run focus. Opens the Verbose panel filtered to the focus level.
- [x] Task 7.2: **Verbose panel** — Reads `aom_stderr_line` events from `events.jsonl`. Filters by focus level: run = run-level sources only; play = run-level + task-level in play window; task = run-level + task-level for focused `connection_id`. Ambiguous lines (multiple active connections on same host) get a `?` indicator.
- [x] Task 7.3: **TUI footer focus indicator** — Show `focus: <level> (<context>)` in the footer (per QC-008). Transient `V` flash on keybind press.
- [x] Task 7.4: **Lazy-render budget** — Q32: < 100ms for 1MB stdout block. If exceeded, lazy-render (first 100 lines + "press L to load full"). "L" keybind loads full content.
- [x] Task 7.5: **CLI text mode** — Update `aom inspect --text` to read `aom_stderr_line` events. Remove 20-line cap and `status == "failed"` gate. Add `--task <name>` and `--play <name>` scoping flags.
- [x] Task 8.1: **Fuzz test** — `tests/unit/test_aom_verbose_line_fuzz.py`. 10k random stderr lines through the prefix classifier; assert no false positives for known non-verbose lines (`ERROR!`, `Traceback`, `FATAL`, etc.).
- [x] Task 8.2: **Crash-recovery test** — `tests/unit/test_event_store_crash_recovery.py`. SIGKILL AOM mid-write from a subprocess; restart; verify replay handles missing `meta.json` (warn, continue).
- [x] Task 8.3: **Schema-boundary test** — `tests/unit/test_replay_schema_boundary.py`. Record with AOM v1 (no `_schema_version`); replay with AOM v2 (has `_schema_version: 2`); verify replay branches correctly.
- [x] Task 8.4: **Concurrency test** — `tests/integration/test_concurrent_inspect.py`. Fake playbook emitting 1000 events/sec while another thread invokes `aom inspect` on partial `events.jsonl`. Assert no `IOError`, no truncated lines, no race.
- [x] Task 8.5: **`scripts/verify_anchors.py`** — Per QC-012. Parses design doc for `path:line-line` patterns, verifies each anchor against the actual file. Pre-commit hook entry.
- [x] Task 8.6: **README "Disk usage" section** — Per QC-005. Worked example: "200-host run with `--capture-verbose --capture-setup` produces ~50MB. 100 sessions ≈ 5GB." Point to `aom inspect prune --days N`.
- [x] Task 8.7: **Verification task: `aom inspect prune` exists** — Confirmed by `aom-codebase-verification.md` Task 1.
- [x] Task 8.8: **Verification task: pre-commit setup** — Confirmed by `aom-codebase-verification.md` Task 3. Add `verify_anchors.py` as a local hook.

## Final Verification Wave
- [x] F1: Run full test suite (`uv run pytest tests/ -q`) — all tests pass
- [x] F2: `lsp_diagnostics` clean across all changed files
- [x] F3: `uv run ruff format && uv run ruff check --fix` — clean
- [x] F4: `uv run mypy src/ansible_aom` — clean
- [x] F5: `scripts/verify_anchors.py` passes against the v1 design doc
- [x] F6: Manual smoke: `aom --help` shows all new flags; `aom inspect <sid>` (TUI) shows Verbose panel via `V` keybind; `aom site.yml --capture-verbose -vvvvv` produces a session with `aom_stderr_line` events tagged by source
- [x] F7: SPECIFICATION.md and ARCHITECTURE.md updated; README has "Disk usage" section

## Out of scope (deferred to v2)
- `~/.cache/aom/` config cache (50ms startup is acceptable; wrong-config risk outweighs benefit; per Q6)
- Encrypting `events.jsonl` at rest
- Per-field toggle UI in inspect TUI
- Auto-classification of `aom_verbose_line` source beyond the regex heuristic
- Live streaming of verbose data to a separate TUI window while run is in progress
- Multi-session comparison of verbose data (`aom inspect diff` for verbose events)
- Aggregated/structured redaction of nested values (v1 does surface-level match only)
