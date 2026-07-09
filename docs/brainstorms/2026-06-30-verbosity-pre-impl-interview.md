# Verbosity-Plan Pre-Implementation Interview
Date: 2026-06-30 · Goal: Lock down the open questions in the verbosity-handling plan + QC triage before any code is written. Source docs: `docs/brainstorms/2026-06-29-verbosity-handling.md` (1180 lines, partial read) and `docs/brainstorms/2026-06-30-qc-review-triage.md` (404 lines, full read).

## Summary / key decisions

**v1 scope locked.** v1 = the next minor release (`v0.x+1`). All 17 design sections + 20 QC triage decisions ship together as one release. The multi-layer config refactor (`core/config_layer.py`, ~150-200 LOC) is in scope (hard prerequisite per Doc 1 §11). The `~/.cache/aom/` config cache is **deferred to v2** — the 50ms startup cost is not worth the wrong-config risk from a stale cache.

**4 open design questions resolved:**
- **Q21** — `--check`/`--diff` UI: show `"(no diff)"` placeholder when field is absent
- **Q22** — per-host truncation: no cap (consistent with Q10=B; README "Disk usage" is the user guidance)
- **Q23** — live streaming inspect: adopt 3-line spec note
- **Q32** — TUI render budget: < 100ms for 1MB stdout; lazy-render (`L` to load full) is the fallback

**Implementation order: phased by feature, not by discipline.** Each phase is end-to-end (test → impl → doc). 8 phases:
1. Schema version bump (QC-004): `_schema_version: 2` in `meta.json`
2. Redaction rewrite (QC-002): ansible-core seed + red-team fixture + Layer 0/1/2 reframe
3. Config refactor: new `core/config_layer.py` + multi-layer load + `aom_config.yaml` rename + auto-migration
4. Storage extension: `hosts.<host>.verbose` block + `aom_verbose_line` synthetic event + redaction wiring
5. CLI flags: `--capture-verbose`, `--capture-setup`, `--no-redact`, `--yes`, `--no-failed-hint`, `--hide-warnings`, `--hide-deprecations`, `--config`
6. Live indicators: `● REC+VC` status, failed-hint, warnings/deprecations, `--capture-setup` exclusion
7. Inspect TUI: `V` keybind, focus indicator, tabbed DetailBlock, lazy-render, `V` flash
8. Tests + verification: QC-009 (4 tests: fuzz, crash-recovery, schema-boundary, concurrency) + QC-012 (`scripts/verify_anchors.py`)

**Heuristic prefix list for `aom_verbose_line`** derived empirically from `ansible-core 2.20`'s `lib/ansible/utils/display.py`. Resolves the research task the triage flagged at line 113.

## Question Backlog (Pending)
(none — all 10 original items resolved; 3 design revisions resolved in next session — see "Locked design decisions" below)

## Locked design decisions (post-research revisions)

After Phase 0 research (5 parallel agents) on 2026-06-30, the following revisions to the brainstorm plan are locked in:

### Storage decision: synthetic events in `events.jsonl`, drop `stderr.log`

After user feedback: **drop the `stderr.log` file entirely.** Stop writing it. Every stderr line becomes a synthetic `aom_stderr_line` event in `events.jsonl` with classification fields. One canonical log file, one read path for inspect. No backward compatibility (per user: "still in active development, this is okay").

Synthetic event schema:
```json
{
  "_event": "aom_stderr_line",
  "_timestamp": "2026-06-30T12:34:56.789012Z",
  "source": "ssh_debug",
  "host": "web1",
  "level": 4,
  "line": "SSH: ANSIBLE_REMOTE_PORT/remote_port/ansible_port set: (-o)(Port=22)"
}
```

| Field | Type | Meaning |
|---|---|---|
| `_event` | str | Discriminator: `"aom_stderr_line"` |
| `_timestamp` | str (ISO 8601 UTC) | When AOM received the line |
| `source` | str (enum) | One of 12 values (see below) |
| `host` | str \| null | Extracted from `<hostname>` prefix if present, else null |
| `level` | int | Verbosity caplevel (0=always, 1-5) |
| `line` | str | Raw stderr line text |

### Classifier: 12 source values, 30 regex rules

Source enum (`StderrSource`):
- `warning`, `deprecation`, `error` — always-emitted
- `ssh_debug` (caplevel 4+), `ssh_info` (caplevel 2-3) — SSH connection
- `connection` (caplevel 2-3), `connection_lifecycle` (caplevel 3) — generic connection
- `plugin_loading` (caplevel 3), `inventory` (caplevel 2) — startup
- `vault`, `prompt` — interactive
- `run_level` — fallback (config, retry file, play count, etc.)

Run-level vs task-level (for `V` keybind filtering):
- **Run-level** (visible at run focus): `warning`, `deprecation`, `error`, `plugin_loading`, `inventory`, `vault`, `prompt`, `run_level`
- **Task-level** (only visible at task/play focus when host matches): `ssh_debug`, `ssh_info`, `connection`, `connection_lifecycle`

Full regex table in `.sisyphus/notepads/2026-06-30-verbosity-pre-impl-interview/stderr-classification-taxonomy.md` Section 4. First match wins.

### Reuse existing classification

AOM's `core/parser.py:_handle_plaintext` already classifies `[WARNING]:` / `[DEPRECATION WARNING]:` patterns (lines 167-281). The existing `WarningEntry` dataclass (lines 72-79 of `core/models.py`) is a good model. The new classifier slots into the `else` branch at line 283, before `_plaintext_lines.append(line)`. The warning/deprecation logic is reused; new logic adds the other 10 source values.

### What `V` shows at each focus level

| Focus level | Show synthetic events where... |
|---|---|
| **Run** | `source IN (run-level sources)` — warnings, deprecations, errors, plugin loading, inventory, vault, prompts, run_level fallback. **Excludes** `ssh_debug`, `ssh_info`, `connection`, `connection_lifecycle` (task-level noise). |
| **Play** | All run-level + task-level events where the JSONL event time window falls within the play |
| **Task** | All run-level + task-level events for the specific task×host (filtered by `host` field) |

This correctly handles `strategy: free` because **the `host` field on each event is what scopes it**, not timestamps. A `ssh_debug` event with `host: "web1"` is part of web1's task, not web2's, even if they interleave on stderr.

### Implementation outline

**`core/stderr_classifier.py` (new, ~80 LOC)**:
- `StderrSource` enum (12 values)
- `CLASSIFIER_RULES` list (30 tuples: source, regex, has_host)
- `classify(line: str) -> StderrEvent` — try each regex, return first match with extracted host
- `StderrEvent` dataclass: `source`, `host`, `level`, `line`

**`core/parser.py:_handle_plaintext` (modified, +5 LOC)**:
- Reuse warning/deprecation handling (existing code at lines 256-281)
- Add new else branch: emit `aom_stderr_line` event via session sink
- Drop the `_plaintext_lines.append(line)` fallback (or keep it for backward compat with replays that look at _plaintext_lines)

**`session/store.py:record_stderr` (modified, -3 LOC)**:
- Remove the file write entirely
- Replace with: pass the line to the classifier and emit a synthetic event to `events.jsonl`

**`inspect/text.py` and `inspect/text.py:_render_stderr_tail` (modified)**:
- Read from `events.jsonl` (filter for `_event == "aom_stderr_line"`)
- Apply focus-level filter (run-level only, or scoped to play/task)
- Remove the `status == "failed"` gate and the 20-line cap

**`tui/screens/inspect.py` (Phase 7)**:
- Add "Verbose" panel that reads `aom_stderr_line` events
- Filter by focus level using the table above
- Use the existing `V` keybind (already in the plan) to toggle the panel

### Open architectural questions

From the taxonomy report Section 5:
- **`VERBOSE_TO_STDERR=False`** would route verbose to stdout. Out of scope; document the assumption.
- **`display.debug()`** goes to stdout, not stderr. Out of scope for v1; debug messages are captured by JSONL if relevant.
- **`banner()`** writes to stdout (PLAY/TASK headers). Already captured by JSONL via `v2_playbook_on_play_start` and `_task_start` events. No action needed.
- **Deduplication**: ansible deduplicates warnings, so the classifier sees fewer lines than expected. Fine; the event count matches what's on disk.

### Implication for the 8-phase plan

| Phase | Change |
|---|---|
| **Phase 4** (storage) | Drop `stderr.log`. Add `aom_stderr_line` synthetic event emission. Add `core/stderr_classifier.py` (~80 LOC). Update `store.py:record_stderr` to emit event instead of writing file. Update read side: `session["stderr"]` no longer exists; consumers read from `events.jsonl` filtered for `aom_stderr_line`. |
| **Phase 4** (sub-task) | Add test fixtures: JSONL event samples with `aom_stderr_line` events at each source. |
| **Phase 7** (TUI) | Add "Verbose" panel to inspect TUI. Filter by focus level (run-level vs task-level×host). |
| **Phase 7** (CLI) | Update `aom inspect --text` to read from `events.jsonl`, apply focus-level filter, remove 20-line cap and `status == "failed"` gate. |
| **Phase 7** (sub-task) | Add `--task` / `--play` scoping flags to `aom inspect --text` so the user can filter from the CLI too. |

### Connection tracking: custom JSONL callback plugin

After the `strategy: free` + `async` discussion, the v1 design needs a way to track which task owns a stderr line on a given host. The research (`connection-id-feasibility.md`) found that ansible-core's `connection_lock()`/`connection_unlock()` are never called, so there's no per-connection signal in stderr. Solution: ship a custom JSONL callback plugin that emits connection-tracking events on AOM's behalf.

**Decision: ship `src/ansible_aom/callbacks/aom_connection.py` as a JSONL callback plugin.** AOM auto-loads it via `ANSIBLE_CALLBACK_PLUGINS` when wrapping `ansible-playbook`. No user action required.

The callback plugin (extends `CallbackBase`):
- `v2_runner_on_start(task, host)` → emit `aom_connection_acquired` with `connection_id: <UUID>`, `task_uuid`, `host`, `ts`
- `v2_runner_on_ok/failed/unreachable/skipped(result)` → emit `aom_connection_released` with the same `connection_id`, status
- All other callback methods pass through (no override)

AOM's PTY parser sees these events interleaved with `v2_runner_on_*` JSONL events. When a stderr line arrives with `host: "web1"`, AOM looks at the most recent `aom_connection_acquired` for `web1` and tags the line with that `connection_id`. The line is then scoped to the correct task.

**Irreducible limit** (the only failure case): when two `aom_connection_acquired` events for the **same host** truly overlap in time (true concurrent execution on the same host, only possible with `async: poll: 0` + `strategy: free`). AOM attributes the stderr line to the **most recent** acquired connection for the host. The synthetic event gets a `attribution_confidence: "ambiguous" | "unique"` flag. The inspect TUI shows a small `?` indicator next to ambiguous lines; the user can drill in via the JSONL event timeline to disambiguate manually.

**Updated synthetic event schema** (adds `connection_id` and `attribution_confidence`):
```json
{
  "_event": "aom_stderr_line",
  "_timestamp": "2026-06-30T12:34:56.789012Z",
  "source": "ssh_debug",
  "host": "web1",
  "level": 4,
  "connection_id": "C-a3f9b2e1",
  "attribution_confidence": "unique",
  "line": "SSH: ANSIBLE_REMOTE_PORT set: (-o)(Port=22)"
}
```

For **run-level events** (no host, e.g., warnings, plugin loading), `connection_id` is `null` and `attribution_confidence` is `"unique"` (the line is unambiguously run-level).

### Updated `V` keybind behavior

| Focus | Filter |
|---|---|
| **Run** | `host IS NULL` (run-level events only, regardless of `connection_id`) |
| **Play** | `host IS NULL` OR (`host IN (hosts in this play)` AND line's `_timestamp` falls in play window) |
| **Task** | `host IS NULL` OR (`host == focused host` AND `connection_id == focused task's connection_id`); show ambiguous lines (different `connection_id` but same host) with `?` indicator |

This correctly handles:
- `strategy: free` alone (lines tagged by host, multiple hosts see their own)
- `async` alone (lines tagged by host; same host may have multiple connections, but the most-recent-acquired heuristic handles it)
- `strategy: free` + `async` (most-recent-acquired is the best we can do; ambiguous flag surfaces the limit honestly)
- The `host` field already works because the callback's `v2_runner_on_start` carries the host
- The `connection_id` works because the callback generates a unique UUID per acquisition

### Updated phase plan (additions)

| Phase | Change |
|---|---|
| **Phase 4** (storage) | New: `src/ansible_aom/callbacks/aom_connection.py` (~80-100 LOC). New event types: `aom_connection_acquired`, `aom_connection_released`. New fields on `aom_stderr_line`: `connection_id`, `attribution_confidence`. Parser maintains a `(host, connection_id, acquired_at)` map. |
| **Phase 4** (sub-task) | Test fixtures: callback plugin unit tests + integration test with overlapping async tasks. |
| **Phase 5** (CLI) | Auto-set `ANSIBLE_CALLBACK_PLUGINS=~/.local/share/aom/callbacks` when AOM runs ansible-playbook. No user-visible flag. |
| **Phase 7** (TUI) | "Verbose" panel groups by `connection_id` when present. Ambiguous lines get a `?` indicator. `--task` / `--play` filters use `connection_id` matching. |



### Q1 — What does "v1" mean in this context?
- Asked: A (this minor release), B (feature branch), C (smallest subset), D (post-QC-pass doc baseline)?
- Captured: **A — v1 = this minor release (`v0.x+1`).** Doc 1 line 468 is the only "v1" reference with a concrete version number; the triage doc's "v1" is shorthand for "this pass" and shouldn't override the version-bump statement.
- Implication: the 17 design sections + 20 triage decisions + 5 new files + 12 doc edits ship as one release. Sequencing = release-train sequencing. No "ship the branch, observe, cut later" intermediate state.
- Flags: none.

### Q2 — Implementation order
- Asked: A (triage's verify → doc → code), B (code first), C (parallel tracks), D (phased by feature)?
- Captured: **D — phased by feature.** Each phase is end-to-end (test → impl → doc edits interleaved). 8 phases listed in the Summary.
- Rationale (rejected A): the triage's "verify → doc → code" works for a small change but produces a 6-week "doc edit" PR and a 6-week "code" PR. Phased-by-feature keeps each unit reviewable.
- Rationale (rejected B): "code first" violates AGENTS.md's TDD-first rule for `core/` (the bulk of the work).
- Rationale (rejected C): parallel doc + code risks spec/code drift.
- 8-phase order:
  1. **Schema version (QC-004)**: small, isolated, sets the pattern for additive `meta.json` changes.
  2. **Redaction rewrite (QC-002)**: pure function in `core/redaction.py`; high test surface; red-team fixture is the deliverable proof.
  3. **Config refactor**: largest single code change (~150-200 LOC of new code + ~50 LOC of changes). Lands before storage because storage reads `[capture]` config values.
  4. **Storage extension**: `hosts.<host>.verbose` block + `aom_verbose_line` event + redaction wiring. The heart of the feature.
  5. **CLI flags**: surfaces the config + storage work to users. Includes `--yes` global (QC-003).
  6. **Live indicators**: `● REC+VC`, failed-hint, warnings/deprecations. Reads the storage + config to decide what to render.
  7. **Inspect TUI**: `V` keybind, focus indicator, tabbed DetailBlock, lazy-render with budget. Consumes the storage work.
  8. **Tests + verification**: QC-009 (4 tests) + QC-012 (verify_anchors.py) + final 3 verification tasks (`aom inspect prune` exists, `--yes` doesn't already exist, pre-commit setup).
- Flags: each phase is a discrete PR. The 8-PR shape is the source of truth; combine adjacent phases if a phase is < 100 LOC.

### Q3 — How are the 4 open questions (Q21, Q22, Q23, Q32) being resolved?
- Asked: A (resolve all now), B (resolve Q23/Q32, defer Q21/Q22), C (defer all 4), D (resolve only Q32)?
- Captured: **A — resolve all 4 now.** Walking through each below (Q3.1–Q3.4).
- Rationale (rejected B): the 4 questions are similar in scope; partial resolution leaves "we'll think about it" markers in the design doc, which the QC-001 sweep is supposed to clean up.
- Rationale (rejected C): defers 4 known unknowns into v1. The triage doc's "honest trade-offs" framing is a stylistic position, not a scope decision; the user picked A here.
- Rationale (rejected D): Q21 and Q22 are policy/UX choices, not architectural. Resolving them takes 5 minutes each.
- Flags: each resolution is one design-doc line edit + a one-line test. ~30 min total.

### Q3.1 — Q21 (`--check`/`--diff` UI)
- Asked: A ((no diff) placeholder), B (hide field), C (empty string), D (two distinct messages)?
- Captured: **A — show "(no diff)" placeholder when field is absent.** Consistent cell shape in the inspect TUI; no empty rows; self-documenting.
- Rationale (rejected B): empty tabs in a tabbed DetailBlock are fine in principle but add a "is this an empty tab or a hidden tab?" rendering concern.
- Rationale (rejected C): empty string looks like a bug.
- Rationale (rejected D): most informative, but the underlying distinction (module doesn't support diff vs. `--check` not set) is not actionable for the user — both look the same in the inspect TUI. Save the distinction for `aom inspect --show-diff-meta` in v2.
- Flags: none.

### Q3.2 — Q22 (per-host truncation policy)
- Asked: A (no cap), B (soft cap with marker), C (hard silent cap), D (per-field cap)?
- Captured: **A — no per-host cap.** Consistent with Q10=B (the user explicitly chose no caps in Q10). README's "Disk usage" section is the user-facing guidance. `aom inspect prune --days N` is the remediation path.
- Rationale (rejected B): introducing a cap just for `hosts.<host>.verbose` while leaving other writes uncapped is incoherent. The "Disk usage" section in the README (QC-005 mitigation) is the right home for this guidance.
- Rationale (rejected C): silent data loss is a non-starter.
- Rationale (rejected D): most granular, most code, most user confusion.
- Flags: depends on the README "Disk usage" section landing. Cross-reference to QC-005 doc work in §17.

### Q3.3 — Q23 (live streaming inspect spec note)
- Asked: A (adopt the 3 lines), B (adopt with edits), C (drop, trust §10 prose)?
- Captured: **A — adopt the 3-line note** as proposed in Q4.3 of the interview:
  ```
  Live streaming inspect (additions to §10):
  - `aom inspect <running-sid>` reads `events.jsonl` line-by-line via the
    existing streaming reader in `session/store.py` (no new code path).
  - Incomplete trailing line (no terminating newline) is treated as truncated
    and skipped with a `WARN` (per QC-009 crash-recovery semantics).
  - `--debug` flag is honoured mid-run: `aom_verbose_line` events emitted
    after the inspect TUI is opened appear on next refresh (≤ 1s polling).
  ```
- Rationale (rejected B): no edits suggested; the 3 lines cover the implementation guidance gap.
- Rationale (rejected C): §10's 4 lines are correct but the "implementation guidance" gap is the whole point of Q23.
- Flags: **verify** the inspect TUI's refresh rate is ≤ 1s during phase 7 (TUI work). If it's slower, the spec line needs revision.

### Q3.4 — Q32 (TUI render budget for full stdout/stderr)
- Asked: A (100ms budget + lazy-render fallback), B (always lazy-render), C (eager, no budget), D (256KB hard cap, eager)?
- Captured: **A — render budget < 100ms for 1 MB stdout block. Lazy-render (first 100 lines + "press L to load full") is the fallback if the budget is exceeded.**
- Rationale (rejected B): always-lazy loses the "fast path" for the 90% case (typical stdout is < 10KB).
- Rationale (rejected C): "trust Textual" is how we got here. A measured budget is the rigor play.
- Rationale (rejected D): a hard cap is a different design choice from a render budget. A cap is consistent with Q10=B if the cap is "0 = unlimited" and the default is 0; A keeps the no-cap default and adds a perf safety net.
- Flags: the 100ms number is a conservative guess. If phase 7 (TUI work) shows it's too tight, loosen to 250ms and document the change. If it's too loose, tighten to 50ms.

### Q4 — Is the multi-layer config refactor part of v1?
- Asked: A (in scope, hard prerequisite), B (split to v0.x+2), C (hybrid minimal)?
- Captured: **A — yes, part of v1.** Hard prerequisite per Doc 1 §11 ("Compact mode startup ... must call `load_config()` and merge layers"). The QC triage's "5 new code/test files" count is imprecise; the config refactor is a real ~150-200 LOC of new code in `core/config_layer.py`.
- Rationale (rejected B): splits the feature across two releases. Captures the "compact mode ignores config" behavior problem in v0.x+1, then in v0.x+2 changes it. Awkward.
- Rationale (rejected C): Doc 1 §11 explicitly considered and rejected hybrid as Q4.2=C. The user's TUI/compact parity is the point.
- Flags: config refactor is the largest single code change. Estimate ~2-3 days of focused work; budget accordingly in phase 3.

### Q5 — `aom_verbose_line` heuristic prefix list
- Asked: A (derive from ansible-core source), B (small starter list, iterate), C (drop synthetic event), D (let implementer build)?
- Captured: **A — derive empirically from `ansible-core 2.20`'s `lib/ansible/utils/display.py`.** Read every `Display.v*()` call site, build the prefix set.
- Rationale (rejected B): "land with a known-short list" is exactly the spec's "et cetera" problem. We'd ship with a list the implementer guesses at, then iterate based on user reports. Empirical derivation is more rigorous for the same cost.
- Rationale (rejected C): drops a feature the design spec calls out. Out of scope for "lock down the open questions."
- Rationale (rejected D): shifts the work without specifying the result. The triage's open-flag at line 113 explicitly flagged this as a research task; doing the research is the right answer.
- Flags: ~30 min of reading ansible-core source. Run in parallel with phase 2 (redaction) since both are pure research. Output is a `core/verbose_heuristic.py` constant (or similar) consumed in phase 4.

### Q6 — `~/.cache/aom/` config cache
- Asked: A (defer), B (land in v1), C (with feature flag), D (measure first)?
- Captured: **A (with explicit rationale) — defer to v2.** The 50ms startup cost is not worth the wrong-config risk from a stale cache.
- Rationale (rejected B): introduces a cache with no measurement. If the cache invalidates wrong (mtime drift, fs races), users get wrong config silently.
- Rationale (rejected C): feature flag is overhead for a mitigation that's already optional.
- Rationale (rejected D): "measure first" is the rigor play but the 50ms is the user's own claim, and "do we cache?" doesn't depend on whether the claim is 50ms or 5ms. The risk calculus (wrong config vs. faster startup) is the same.
- Flags: revisit in v2 if a user reports startup latency. Add a note to v1 README's "Performance" section (if one exists) or skip.

### Q7 — Sufficient context from triage doc?
- Asked: A (read Doc 1 lines 577-1180 first), B (trust the triage), C (read selectively)?
- Captured: **B — trust the triage doc as faithful and proceed.** Triage is dated 2026-06-30, one day after Doc 1, and the user signed off on each of the 20 decisions.
- Implication: I do not need to read Doc 1's QC REVIEW section, §13 test plan, §14 docs, §15 migration, §16 out-of-scope, or §17 risks in full. The triage's summary is the working source of truth.
- Flags: none.

## Open flags (pending input)
- **Verify `aom inspect prune` exists and is tested.** ~~Doc 2 line 380.~~ **RESOLVED 2026-06-30**: PASS. `src/ansible_aom/inspect/cli.py:70-74`, `--days` default 30, integration test at `tests/integration/test_inspect_cli.py:58`, unit test at `tests/unit/test_cli.py:551`. See `aom-codebase-verification.md` Task 1.
- **Verify `--yes` doesn't already exist as a global flag.** ~~Doc 2 line 381.~~ **RESOLVED 2026-06-30**: PASS. Only exists on `rerun` subcommand (`src/ansible_aom/rerun/cli.py:301-304`). Top-level `cli.py` parser has no global `--yes`. Phase 0 (pre-flight) needs the flag added. See `aom-codebase-verification.md` Task 2.
- **Verify pre-commit / CI hook setup before adding `scripts/verify_anchors.py`.** ~~Doc 2 line 382.~~ **RESOLVED 2026-06-30**: PASS. 5 hooks: ruff-format, ruff-check, mypy (all pre-commit), pytest (pre-push only), graphify-refresh. New script slots in as a local hook entry. See `aom-codebase-verification.md` Task 3.
- **Confirm inspect TUI's existing refresh rate is ≤ 1s.** ~~Per Q3.3 flag.~~ **RESOLVED 2026-06-30 (with revision)**: The inspect TUI is a **static browser** — no polling. Only the live TUI (`src/ansible_aom/tui/app.py:468`) has a 200ms tick. The Q3.3 spec note assumed the inspect TUI polls, which is wrong. See "Design revisions" below.
- **Confirm `src/ansible_aom/core/redaction.py:280-283` is the real Layer 4 location.** ~~Doc 2 line 113.~~ **RESOLVED 2026-06-30**: PASS. Lines 279-283 (comment on 279, code on 280-283). The `redact_event` function spans 216-285 and is unwired. See `aom-codebase-verification.md` Task 5.

## Phase 0 (research) — Findings 2026-06-30

Three research agents ran in parallel against actual source. Reports at `.sisyphus/notepads/2026-06-30-verbosity-pre-impl-interview/`:

### Finding 1 — `aom_verbose_line` prefix list is one prefix, not many

**The brainstorm's heuristic ("Loading, Attempting, Skipping, config file, Setting up, etc.") was hallucinated.** Actual ansible-core 2.20.4 source shows:

- At caplevel ≥ 4 (`-vvvvv`+), the only `Display.v*()` call sites in ansible-core are in `lib/ansible/plugins/connection/ssh.py:Connection._add_args()`. All produce lines matching the prefix `SSH: ` (e.g., `SSH: ANSIBLE_REMOTE_PORT/remote_port/ansible_port set: (-o)(Port=22)`).
- The brainstorm's "Loading callback plugin", "setting up inventory plugins", "CONNECTION: pid X acquired lock" are all at caplevel 3 (`-vvvv`), not caplevel 4. Below the conservative boundary.
- No `Attempting `, `Skipping `, `config file`, `Setting up` prefixes exist in ansible-core 2.20.4's `Display.v*()` calls at any caplevel.

**Implication for the v1 plan:**
- The `aom_verbose_line` synthetic event is a **one-prefix classifier** (`SSH: `), not a multi-prefix heuristic. Code is ~10 LOC, not ~50.
- The event type may be over-scoped. Consider: drop the synthetic event entirely; just log `Display.vvvv+` stderr lines to `stderr.log` and surface them via the existing "Raw PTY" inspect tab (Q8=A in the brainstorm). The user can still see the SSH args in inspect; they just don't get the structured event in `events.jsonl`.
- The research report's Open Question #1 ("caplevel boundary ambiguity") recommends caplevel ≥ 3 (vvvv) instead of ≥ 4 (vvvvv) to include `CONNECTION:` lock messages, callback loading, and inventory setup. The user should pick one boundary.

**Open decision for user**: keep `aom_verbose_line` as a one-prefix classifier (and decide which caplevel), or drop it entirely.

### Finding 2 — Inspect TUI is a static browser

**The Q3.3 spec note ("≤ 1s polling") is wrong about the inspect TUI.** The inspect TUI (`tui/screens/inspect.py`, 1039 lines) is a read-only browser that:
- Loads session data on mount (`on_mount` → `_reload_runs`)
- Re-loads on `r` keypress (`action_reload_runs`)
- Does NOT have `set_interval` or `set_timer` calls

The **live TUI** (`src/ansible_aom/tui/app.py:468`) does poll at 200ms — but that's the playbook-monitoring TUI, not the inspect TUI.

**Implication for the v1 plan:**
- "Live streaming inspect" (Q23) doesn't need a polling loop. The inspect TUI already reloads on `r`. For a true streaming experience, add a `<C-r>` (auto-refresh) mode that calls `_reload_runs()` on a 1s timer when active.
- The Q3.3 spec note needs revision: change "≤ 1s polling" to "user-initiated reload on `r`; optional auto-refresh on `<C-r>` toggle at 1s."

### Finding 3 — Config refactor is ~50 LOC, not 150-200

**`pydantic-settings` v2.x supports layered YAML natively** via `YamlConfigSettingsSource(yaml_file=[...], deep_merge=True)`. The library's composition engine does `deep_update` across all sources for free.

**Critical gotchas** (none in the brainstorm):
1. **Must set `deep_merge=True`** on `YamlConfigSettingsSource` or nested dicts in earlier files get wiped by empty later files.
2. **Must set `nested_model_default_partial_update=True`** in `SettingsConfigDict` or user-level YAMLs that touch one sub-model field wipe the rest of the sub-model from system-level YAMLs.
3. **Missing files are silently skipped** — desired for XDG layering, footgun for typo'd `--config` paths. AOM's CLI should `assert Path(p).is_file()` before invoking `Settings()`.
4. **`pyyaml` must be installed explicitly** — `pydantic-settings[yaml]` extra. Verify `pyproject.toml` pins it.

**Implication for the v1 plan:**
- `core/config_layer.py` is **~50 LOC, not 150-200**. Phase 3 (config refactor) effort drops from ~2-3 days to ~1 day.
- The plan's full multi-layer system is reachable in ~10 LOC of file-list resolution + the standard `settings_customise_sources` pattern (15 LOC). The rest is model definitions in separate sub-modules.

### Finding 4 — All 5 verification tasks PASS

The 5 open-flags from the brainstorm are all correct. The AOM codebase matches the docs. The only delta:
- `src/ansible_aom/core/redaction.py:279-283` (off-by-1 from cited 280-283; comment on 279, code on 280-283).
- `--yes` needs adding to global parser (Phase 0 work).
- Pre-commit setup is well-defined; `scripts/verify_anchors.py` slots in as a new local hook.

### Design revisions needed

Based on the research, the v1 plan should be revised:

1. **Phase 4 (storage extension)** — drop the `aom_verbose_line` synthetic event entirely, OR keep it as a one-prefix classifier (`SSH: `). The brainstorm's multi-prefix design is hallucinated. Decision needed.
2. **Q3.3 spec note (live streaming inspect)** — rewrite to match reality: "Inspect TUI is static; reload on `r`; optional auto-refresh on `<C-r>` toggle at 1s."
3. **Phase 3 (config refactor) LOC estimate** — revise from "150-200 LOC" to "~50 LOC" (plus model definitions in separate sub-modules). Add the 2 critical gotchas (`deep_merge=True`, `nested_model_default_partial_update=True`) to the spec.
