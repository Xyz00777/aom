# Ansible Verbosity Handling in AOM: Brainstorm / Discovery Notes
Date: 2026-06-29 · Goal: Design how ansible-aom captures verbosity-controlled output (JSONL + stderr + debug noise) and exposes it in a post-run "inspect" view, without cluttering the live TUI.

## Summary / key decisions (running synthesis, updated as answers come in)

**Research findings (verified across 4 angles: JSONL source, ansible-core source, empirical test at all 6 verbosity levels, existing codebase inventory):**

- `ansible.posix.jsonl` is **verbosity-agnostic**. The callback never branches on `self._display.verbosity`. It serialises `result._result.copy()` at every `-v` level. Empirical run with ansible-core 2.20.4 confirmed: **identical 10 events** at -v, -vv, -vvv, -vvvv, -vvvvv, -vvvvvv. Differences in human stdout come from `default.py`'s `CallbackBase._dump_results` (which strips `invocation` + `diff` when `verbosity < 3`) — but JSONL never calls `_dump_results`.
- Verbosity-controlled content that lives **outside** JSONL: `Display.v()` / `vv()` / `vvv()` / etc. lines are written to **stderr** from worker processes, bypassing stdout callbacks entirely. At `-vvvv`+ these include connection debug (SSH args, EXEC paths); at `-vvvvv`+ plugin loader traces.
- Existing AOM already strips verbose fields on disk: `session/store.py` `RECORD_EVENT_KEEP_FIELDS` keeps only `_event`, `_timestamp`, `task`, `play`, top-level `hosts` subset (`changed`, `failed`, `skipped`, `unreachable`, `duration`), and `stats`. `msg`, `stdout`, `stderr`, `invocation.module_args`, `diff`, `results[]` are dropped.
- AOM's existing `aom inspect` (TUI `tui/screens/inspect.py` 1039 lines, CLI `inspect/text.py`, CLI debug `inspect/cli.py`) is mature but only surfaces `msg`, `module_stdout`, `module_stderr`, `warnings`, `results[]` loop items — all of which are stripped before reaching disk.
- `core/redaction.py` has 4 redaction layers defined and tested; **Layer 4 (`invocation.module_args`) is built but never wired into any call site**.
- Verbosity `-v` / `-vvv` / `-vvvvvv` flags flow through verbatim from `aom site.yml -vvv` → `ansible-playbook site.yml -vvv` via `ansible/runner.py`.
- No `verbosity` / `v` / `level` field is embedded in JSONL events — the JSONL callback does not record the level the user invoked. (The bootstrap comment `cli.py:200` already warns "-v is reserved for ansible-playbook. AOM's debug flag is --verbose.")

**Open questions (in priority order — see backlog below):**
- Capture model (always-on sidecar vs opt-in, separate file vs extended events.jsonl)
- Redaction policy (which fields to redact, when, who configures)
- Live view behavior (already covered by NOT showing verbose fields — confirm)
- Inspect view shape (tabs? drill-in? per-field toggle?)
- PTY stderr handling (already captured but format/location TBD)
- Backwards compatibility (existing sessions, run-state schema migration)
- UX affordances (keybinding, CLI flag, config knob)
- Edge cases (no_log, vault prompts, --check/--diff, large results)

**Locked-in design (post-interview, 17 decisions):**

- **Storage (Q1=B)**: Unified `events.jsonl` with optional `hosts.<host>.verbose` block. No sidecar file.
- **Redaction (Q2=A)**: Redact at capture time, hard-coded deny-list, always-on, opt-out via `--no-redact` flag.
- **Default state (Q3=B)**: Capture OFF by default. Opt-in via `--capture-verbose` flag or config.
- **Setup module (Q4=A)**: `setup`/`gather_facts` excluded by default. Opt-in via `--capture-setup`.
- **Config (Q4.2=B)**: Full multi-layer config refactor. `/etc/aom/aom_config.yaml` (global) → `~/.config/aom/aom_config.yaml` (user) → `./.aom_config.yaml` (local) → `AOM_CONFIG` env var → `--config` flag. Compact mode MUST use it.
- **Config naming (Q4.3=B)**: Hard rename to `aom_config.yaml` (no backward compat for old `config.yaml`).
- **Migration (Q5=B)**: Auto-migrate silently on first run. App is in heavy dev, breaking changes are fine.
- **Failed hint (Q6=B)**: Default ON. Show first line of `msg` for `failed`/`unreachable` in live view.
- **Warnings (Q7=D)**: Both `warnings` and `deprecations` shown in live view by default, configurable.
- **Inspect view (Q8=A)**: Tabbed DetailBlock: `Summary`, `Stdout`, `Stderr`, `Module Args`, `Diff`, `Raw PTY`.
- **Schema (Q9=B)**: No `_schema_version` bump. Verbose block is strictly optional; readers tolerate.
- **Size caps (Q10=B)**: No caps. Trust the user. `exclude_modules` is the only "size" knob.
- **CLI naming (Q11=A)**: Keep AOM's `--verbose` (debug) distinct from new `--capture-verbose` (capture).
- **Vault prompts (Q12=A)**: Don't capture. PTY parser handles them safely.
- **Stderr lines (Q13=D)**: Capture `Display.vvvv()` lines as synthetic `aom_verbose_line` events in `events.jsonl` when `--capture-verbose` is on. Tagged with caplevel + source.
- **Inspect UX (Q14.1=Alt 1)**: Single `V` keybind in TUI, context-sensitive. Three sub-views: host, play, run.
- **Live indicator (Q15=B)**: Status-bar shows `● REC+VC` when verbose capture is on.
- **Redaction display (Q16=A)**: `[REDACTED:key]` rendered in dim grey. Raw secrets in red when `--no-redact` is on.
- **Config schema (Q17=A)**: Single `aom_config.yaml` with sections (`capture`, `redaction`, `live`, `inspect`, `tui`).

## Question Backlog (Pending)

### Capture & Storage
- [x] Q1 — **Capture model**: ✅ Resolved — extend `events.jsonl` with optional `hosts.<host>.verbose` block (option B).
- [x] Q2 — **Sidecar vs. unified file**: ✅ Resolved by Q1 — unified.
- [ ] Q3 — **Live in-memory capture**: Does the live `RunState` always populate `HostRunState.msg`, `.stdout`, `.stderr`, `.invocation`, `.diff`, `.results` regardless of whether we'll persist them? (Or only when an opt-in flag is set?)
- [ ] Q4 — **Size budget**: Do we cap the size of captured verbose payload (e.g., 64 KB per host-result)? What happens on overflow — truncate, drop field, dump to sidecar with warning?
- [x] Q5 — **What about PTY stderr?**: Resolved by §7 — stays in `stderr.log`, not duplicated.

### Redaction
- [ ] Q6 — **Redaction by default**: Should `invocation.module_args` be redacted by default (similar to AWX #13613 leak risk), or only on user opt-in?
- [ ] Q7 — **Redaction knobs**: Should redaction be configurable via `~/.config/aom/config.toml` (`ignored_arguments = ["password", "api_key"]`)? Or hard-coded list (Ansible-style: any var matching `*password*`, `*token*`, `*secret*`)?
- [x] Q8 — **Trust `no_log`?**: ✅ Resolved by §6 — trust upstream.
- [ ] Q9 — **Inspect-time redaction**: Should the inspect view re-redact before display, or display raw and let the user decide? (ARA model: redact at capture; AWX model: redact at display.)

### Live View Behavior
- [ ] Q10 — **Confirm default**: Confirm that the compact + live TUI **never** display `module_args`, `stdout`, `stderr`, `diff`, `results` inline — only OK/CHANGED/FAILED status counts. Verbosity-controlled data is **only** surfaced in `aom inspect`.
- [ ] Q11 — **Counter exception?**: For `failed` tasks, should we show the first line of `stderr` or `msg` as a one-liner hint in the live view? (ansible-navigator does this; AOM does not today.)
- [ ] Q12 — **Warnings always shown?**: Are Ansible module warnings (`warnings` field) always shown in live view regardless of verbosity level?

### Inspect View
- [ ] Q13 — **Inspect shape**: Tabbed UI (per-host tabs for Stdout / Stderr / Result / Module Args / Diff / Raw PTY)? Or single scrollable DetailBlock with collapsible sections? Or per-field drill-in?
- [ ] Q14 — **Default verbosity of inspect view**: When user opens `aom inspect <session>`, do they see the verbose fields by default or only the summary?
- [ ] Q15 — **CLI inspect flags**: `aom inspect --verbose`, `aom inspect --module-args`, `aom inspect --stdout`, `--diff` — granular flags, or one big `--all`?
- [ ] Q16 — **TUI inspect keybindings**: New keybind (e.g., `v` to toggle verbose DetailBlock, `a` for module_args, `d` for diff, `s` for stdout/stderr)?
- [ ] Q17 — **Per-task vs. per-host**: Verbose fields are per-host. Should the DetailBlock show one combined view, or tabs/keys to switch hosts?
- [ ] Q18 — **Color-coded fields**: Should sensitive fields (after redaction) be visually distinct (e.g., dim grey `[REDACTED: password]`)?

### Edge Cases & Hardening
- [ ] Q19 — **Backward compatibility**: Old session dirs (recorded before this feature) won't have verbose data. How does `aom inspect` handle that? Show "(verbose data not captured for this run)"?
- [ ] Q20 — **Vault password prompts**: `Display.vvvvvv` lines can include vault prompt text. Are these safe to capture to disk? (probably yes if redaction is on)
- [ ] Q21 — **`--check` / `--diff` mode**: `diff` field in result only appears for modules that support diff (template, copy, lineinfile, etc.). When absent, hide the field or show "(no diff)"?
- [ ] Q22 — **Large results / setup module megabytes**: How do we cap / truncate `setup` module's massive `ansible_facts` payload? (Nominal example: ~50–200 KB raw facts per host)
- [ ] Q23 — **Live streaming inspect**: While the run is still ongoing, can the user open `aom inspect` (on a different session) and see partial verbose data? Or is inspect strictly post-run?
- [ ] Q24 — **Multi-session replay**: When a user does `aom inspect` and selects an older session, should the verbose capture be available? (Likely yes; covered by §8 backward compat.)
- [x] Q25 — **Streaming sidecar writes**: ✅ Resolved — single `events.jsonl` already streams; verbose rides on the same line.

### PTY / stderr handling
- [ ] Q26 — **Stderr routing**: Currently `core/parser.py` has a 3-phase parser. Where do `Display.v()` lines go today? Into the parser's stderr stream, or filtered out?
- [ ] Q27 — **Verbose line classification**: Are `vvvv`+ lines contextually useful in inspect (showing SSH debug), or just noise that should be filterable?
- [ ] Q28 — **Stderr log format**: Is the stderr currently captured as a single blob `stderr.log` per session? Should it be line-typed (`Display.v` vs `Display.vvvv`) for filtering?

### Implementation concerns
- [ ] Q29 — **Run-state schema migration**: Adding fields to `HostRunState` is a dataclass change. Does `RunConfigKey` need a version bump? Does `events.jsonl` JSON need a `_schema_version` field?
- [ ] Q30 — **Test fixtures**: New JSONL fixtures needed (events with `invocation`, `diff`, `stdout`, etc.). Existing fixtures in `tests/fixtures/` — do they cover these fields?
- [ ] Q31 — **Schema for captured verbose data**: Should the live `HostRunState` expose a structured `VerbosePayload` dataclass (`MsgField`, `StdoutField`, `StderrField`, `ModuleArgsField`, `DiffField`, `ResultsField`) or keep flat fields?
- [ ] Q32 — **TUI rendering perf**: DetailBlock in `tui/screens/inspect.py` currently renders truncated strings. Will adding full `stdout`/`stderr` cause scroll/refresh issues? Lazy-render required?

### Configuration
- [ ] Q33 — **Config file location**: Should verbosity-capture default-on vs. default-off be a config setting in `~/.config/aom/config.toml`?
- [ ] Q34 — **CLI override flag**: Should `aom --capture-verbose run site.yml` opt in for that single run? Or only via inspect-time flag?
- [ ] Q35 — **Per-module args include/exclude**: ARA supports `ignored_arguments` list. Do we want the same? (E.g., `ignored_arguments = ["password"]` means never capture args with key `password`.)
- [ ] Q36 — **TUI inspect --no-verbose**: Should we ship a "fast inspect" mode that explicitly skips loading verbose sidecar data for large sessions?

### Documentation & Onboarding
- [ ] Q37 — **README / SPEC update**: A new section in SPECIFICATION.md and ARCHITECTURE.md is needed. Who writes it?
- [ ] Q38 — **Help text in TUI**: When verbose is captured, should the inspect TUI show a one-liner hint like "press v for verbose fields"?
- [ ] Q39 — **Migration script**: Do existing recorded sessions need a one-shot migration (probably not — they're read-only)? Or just graceful fallback message?

### Open architectural
- [ ] Q40 — **Single source of truth**: Confirm that all verbosity-aware data lives in JSONL, and AOM never parses `ansible-playbook`'s human stdout (no regex). Stderr is parsed but only for `Display.v` lines, not as a primary source.
- [ ] Q41 — **Awkward: verbosity > 0 changes no JSONL field**: The user explicitly wanted "-v to -vvvvvv" handled. The honest answer is "JSONL doesn't change; what changes is stderr debug noise + human stdout (which we don't show)." Confirm that explanation is acceptable to the user.
- [ ] Q42 — **Should AOM reject -v at the AOM layer?**: Currently `cli.py` warns "-v is reserved for ansible-playbook" if used as AOM's own flag. Confirm this is the desired behavior going forward.
- [ ] Q43 — **Hide `--verbose` AOM debug or repurpose?**: AOM's `--verbose` is its own DEBUG flag (sets AOM log level). Should it stay or be merged with ansible verbosity?

---

# IMPLEMENTATION PLAN (draft v1 — pending user sign-off)

> Below is my synthesis of the research into a concrete, testable plan.
> Each section calls out the question(s) it presumes an answer for and
> flags where my recommendation diverges from a strict reading of the
> user request.

## 1. Reframe (anchored in research)

The user's stated request: *"don't show them during live execution but catch them and show in inspect"* — implicitly assuming verbosity-gated data only becomes available when you pass `-v` or higher to ansible-playbook.

**Reality discovered through research:**

- `ansible.posix.jsonl` is **verbosity-agnostic**. It serialises `result._result.copy()` on every event at every `-v` level. Module args, stdout, stderr, diff, results[], warnings, deprecations are all in the stream at `-v`.
- Verbosity-gated **content** in human stdout comes from `default.py`'s `CallbackBase._dump_results` (which strips `invocation` + `diff` when `verbosity < 3`). JSONL never calls `_dump_results`.
- Verbosity-gated **noise** (`Display.v()`/`vv()`/... lines) bypasses stdout callbacks entirely and goes to stderr from worker processes. Only relevant at `-vvvv`+.

**Conclusion**: The user's intent ("hide verbose details from live, expose in inspect") is best served by **re-persisting what JSONL already gives us**, not by changing what ansible-playbook is invoked with. The plan below treats the live capture as always-on (data is in the stream anyway) and surfaces it through the existing `aom inspect` view. The `-v` flag user invokes on `aom site.yml -vvvv` simply flows through to ansible-playbook and continues to do what it's always done.

## 2. Architecture overview

```
                ┌─────────────────────────────┐
                │ ansible-playbook -v..-vvvvvv│
                │ + ansible.posix.jsonl       │
                │ (verbosity-agnostic)        │
                └──────────────┬──────────────┘
                               ▼
              ┌────────────────────────────────────┐
              │ PtyStreamParser (core/parser.py)   │
              │  • JSONL stdout → JsonlEventStream  │
              │  • Text stderr → PtyStream          │
              │    (Display.v..vvvvvv lines tagged) │
              └──────────────┬──────────────────────┘
                             ▼
              ┌────────────────────────────────────┐
              │ RunState (core/run_state.py)        │
              │  • plays, tasks, hosts              │
              │  • HostRunState now carries         │
              │    VerbosePayload dataclass         │
              │      (msg, stdout, stderr,          │
              │       invocation, diff, results[],  │
              │       warnings, deprecations)       │
              └──────────────┬──────────────────────┘
                             ▼
       ┌─────────────────────┴─────────────────────┐
       ▼                                            ▼
      ┌──────────────┐                        ┌──────────────────────┐
      │ Live renderers│                       │ session/store.py     │
      │ Compact + TUI │                       │ events.jsonl         │
      │              │                       │   (one file per      │
      │ NEVER show   │                       │    session; verbose  │
      │ VerbosePayload                       │    payload nested    │
      │ inline       │                       │    under hosts.<h>)  │
      └──────────────┘                       └──────────┬───────────┘
                                                      ▼
                                          ┌──────────────────┐
                                          │ aom inspect      │
       │  • TUI 3-pane    │
       │  • CLI text      │
       │  • CLI debug/    │
       │    json          │
       │                  │
       │ NEW: --verbose   │
       │ DetailBlock tabs │
       │   JSON | Args |  │
       │   Stdout | Stderr│
       │   | Diff | Raw   │
       │                  │
       │ Reads from the   │
       │ same events.jsonl│
       │ (verbose nested) │
       └──────────────────┘
```

## 3. Storage design (answers Q1, Q2)

**Decision (revised per Q1=B): Extend `events.jsonl` schema with an OPTIONAL `verbose` sub-key on `hosts.<host>` of `v2_runner_on_*` events. Default ON, opt-out via flag.**

Rationale (revised):
- The user wants one canonical file per session, not a sidecar. Replay drivers, prune, and rerun continue to work because they read the same `events.jsonl` and ignore unknown fields.
- Schema extension is backward compatible: existing readers see no `verbose` key and behave as before. New readers (`aom inspect --verbose`) see the optional block.
- Opt-out (not opt-in) because the data is already in the JSONL stream — there's no privacy cost to keeping it on disk that doesn't already exist.

**File format (`events.jsonl` extended):**
```json
{
  "_event": "v2_runner_on_ok",
  "_timestamp": "2026-06-29T...",
  "task": { "id": "...", "name": "...", "path": "..." },
  "play": { "id": "...", "name": "..." },
  "hosts": {
    "web1": {
      "changed": false,
      "failed": false,
      "skipped": false,
      "unreachable": false,
      "duration": { "start": "...", "end": "..." },
      "verbose": {
        "msg": "...",
        "stdout": "...",
        "stderr": "...",
        "stdout_lines": [...],
        "stderr_lines": [...],
        "invocation": { "module_args": {...} },
        "diff": [...],
        "results": [...],
        "warnings": [...],
        "deprecations": [...],
        "_ansible_no_log": false
      }
    }
  }
}
```

**Schema migration notes (revised per Q9=B, no version bump):**
- `events.jsonl` schema gains one new optional nested key (`hosts.<host>.verbose`) plus one new synthetic event type (`aom_verbose_line` per Q13).
- `RunState` and `HostRunState` (in-memory) gain a `verbose: VerbosePayload | None` field. All existing readers must tolerate its absence (orjson / json default).
- **No `_schema_version` bump in `meta.json`** (per Q9=B). Forward/backward compat via field absence. The `aom_version` field in `meta.json` (already present) is sufficient for "what version recorded this session" tracking.
- `_lean_event` (`session/store.py:57-71`) currently strips verbose fields — this strip is REMOVED for events with `verbose` enabled. The new code path keeps the optional `verbose` block.
- `RECORD_EVENT_KEEP_FIELDS` is extended: add `verbose` to the allowlist as an opt-in key (default behavior of `_lean_event` becomes "strip verbose unless capture is enabled").
- New synthetic event type `aom_verbose_line` (per Q13): emitted by AOM's PTY parser when `Display.vvvv()` lines are detected and `--capture-verbose` is on. Schema:
  ```json
  {
    "_event": "aom_verbose_line",
    "_timestamp": "...",
    "level": 1,  // 1-5, matching caplevel
    "source": "plugin_load",  // heuristic: plugin_load | connection | inventory | callback_load | internal
    "message": "Loading callback plugin ansible.posix.jsonl ...",
    "host": null  // or hostname if applicable
  }
  ```

On `no_log: true`, ansible collapses to `censored: "the output has been hidden..."` and `_ansible_no_log: true`. **Trust ansible's no_log; do not re-redact** at capture time. The `verbose` block simply carries the `censored` string verbatim in this case.

## 4. Live-view contract (answers Q10, Q11, Q12)

- Live renderers (compact + TUI) NEVER render VerbosePayload fields inline. The current behavior is correct and stays.
- **Locked in per Q6=B**: For `failed` and `unreachable` tasks, show the first line of `msg` (after redaction) as a one-liner hint in the compact log. Default ON. The hint is color-coded red and prefixed with the task name. Width-limited to terminal width minus indentation.
- Toggleable via config: `[live] show_failed_hint: true` (default) or `false`. CLI flag: `--no-failed-hint` to disable per-run.
- `warnings` and `deprecations` fields: **per Q7=D, both default ON in the live view**. Both are color-coded (warnings yellow, deprecations orange) and prefixed with `[warn]` / `[deprecation]`. Configurable via `[live] show_warnings: true` and `[live] show_deprecations: true`. CLI flags: `--hide-warnings` and `--hide-deprecations` to disable per-run. Both are also captured in the verbose block (subject to `--capture-verbose` flag).

## 5. Inspect view design (answers Q13–Q18, Q14.1)

**Decision (revised per Q14.1=Alt 1): No global `--verbose` flag. Single `V` keybind in the inspect TUI, context-sensitive. Default inspect stays as-is (Summary only).**

TUI (`tui/screens/inspect.py`):
- New keybind `V` (capital V; lowercase `v` is unbound). Help footer: `V: verbose debug`.
- Single widget: `VerboseView` (in `tui/widgets/verbose_view.py`). Tabs: `Stdout`, `Stderr`, `Module Args`, `Diff`, `Raw PTY` (and at run level: `Run Log`, `Connection`, `Plugin Load`, `Errors` for the `aom_verbose_line` events from Q13).
- Context:
  - **Host focused**: `V` opens `VerboseView` filtered to (play, task, host).
  - **Play focused**: `V` opens `VerboseView` filtered to play.
  - **Run focused**: `V` opens `VerboseView` filtered to run.
- Fallback: if `--capture-verbose` was off for this run, `V` shows a centered message: `"(verbose data not captured for this run — re-run with --capture-verbose to enable)"`. Keybind still works (no-op with helpful message).
- Redaction: `[REDACTED:key]` strings rendered in dim grey (`grey50` in Rich). When `--no-redact` was on, raw values rendered in red (alarm signal). Default state never shows red.

CLI:
```
aom inspect <sid>                       # summary only (unchanged)
aom inspect <sid> --debug               # same as `V` at run level: shows aom_verbose_line events
aom inspect <sid> --host web1 --task "Install nginx"   # filters Detail pane to host×task
```
(No global `--verbose` flag — the TUI is the primary interface; CLI is for piping / scripting.)

JSON output (`--json`): unchanged. Inspect reads `events.jsonl` and surfaces what it finds. To extract verbose data programmatically, use `jq` directly on `events.jsonl`:
```
jq 'select(.hosts["web1"].verbose != null)' ~/.local/state/aom/sessions/<sid>/events.jsonl
```

## 6. Redaction policy (answers Q6–Q9)

**Decision (locked in per Q2=A): Redact at capture time, hard-coded deny-list, always-on, opt-out via `--no-redact` flag. Three layers with explicit precedence:**

1. **Hard-coded deny-list** (always-on, matches ansible's no_log intent):
   - **Keys** (case-insensitive substring match on the param name):
     `password`, `passwd`, `secret`, `token`, `api_key`, `apikey`, `private_key`, `privatekey`, `ssh_pass`, `vault_password`.
   - **Env-var patterns** (any value matching): `*_PASSWORD`, `*_TOKEN`, `*_SECRET`, `*_API_KEY`, `*_PRIVATE_KEY`.
   - Recursive into nested dicts and lists.
   - Replacement: `"[REDACTED:<key>]"` (preserves the key name for context).
2. **`no_log: true` trust** (upstream layer): ansible's callback already collapses result to `censored` BEFORE the JSONL callback serialises it. AOM treats the entire `hosts.<host>.verbose` block as already-safe in this case — `module_args` doesn't appear. **Order matters**: ansible collapses first, then AOM sees a `censored` payload and passes through.
3. **User-configurable deny-list** (`~/.config/aom/config.yaml`):
   ```yaml
   redaction:
     ignored_arguments: ["vault_password", "my_custom_secret"]
     ignored_value_patterns: ["Bearer [A-Za-z0-9]+"]
   ```
   Default: empty. Matched by `re.search` against key names (substring) and values (regex).

**Precedence order (applied at capture time):**
1. ansible's `no_log: true` → already-collapsed payload (no AOM action).
2. AOM hard-coded deny-list on `module_args` keys/values.
3. AOM user-configured deny-list on `module_args` keys/values.

If both (1) and (2)/(3) apply, (1) wins because the payload is already collapsed — there's nothing left to deny-list.

**Safety valve**: `--no-redact` CLI flag (default off → redaction on) bypasses the deny-list and writes raw values. CLI prints: `WARNING: --no-redact is active; secrets will be persisted to events.jsonl. Use only for debugging.`

**Performance**: redaction is O(n) over `module_args` depth, runs once per host-result. No measurable impact on large inventories.

Redaction is a pure function (`redact_event` already exists in `core/redaction.py:280` Layer 4 — needs wiring). Apply at the boundary between parser and event-store, BEFORE the line is written to `events.jsonl`.

## 7. PTY stderr handling (answers Q13, Q26–Q28)

- `Display.v()`-`vvvvvv()` lines bypass stdout callbacks; AOM's parser already routes them to `stderr.log` via the 3-phase parser.
- **Per Q13=D**: when `--capture-verbose` is on, AOM's PTY parser emits synthetic `aom_verbose_line` events into `events.jsonl` for `Display.vvvv()`-style lines. Each event has `level` (caplevel 1-5), `source` (heuristic: `plugin_load` | `connection` | `inventory` | `callback_load` | `internal`), `message`, and optional `host`. NOT a sidecar; integrated into the existing JSONL stream.
- The `aom_verbose_line` event is the only way to surface connection debug, plugin loader chatter, etc. in the inspect TUI. The TUI's `V` keybind at run level opens a tabbed view of these events.
- Heuristic classifier: conservative — only matches a known set of `Display.vvvv()` prefixes (`Loading `, `Attempting `, `Skipping `, `config file`, `Setting up`, etc.). Lines that don't match pass through to `stderr.log` as before (no synthetic event).
- No redaction applied to `aom_verbose_line` content (these are ansible-emitted debug strings, not user data). If a future audit shows secrets leaking here, add redaction in v2.

## 8. Backward compatibility (answers Q19)

- Old sessions: `events.jsonl` lines lack the `verbose` key on `hosts.<host>` and the `aom_verbose_line` event type. The TUI's `V` keybind shows `"(verbose data not captured for this run — re-run with --capture-verbose to enable)"` for any session recorded without the flag.
- `events.jsonl` schema: gains one optional nested key (`hosts.<host>.verbose`) and one new event type (`aom_verbose_line`). Old AOM versions reading new sessions: ignore unknown fields and unknown event types (orjson / json default), so they still work — but they won't surface the new data.
- New AOM reading old sessions: `verbose` is `None`; same fallback message.
- **No `_schema_version` field** (per Q9=B). The existing `aom_version` field in `meta.json` (already present) tracks the recording AOM version. New AOM can use that to decide which fallback message to show if needed.
- `RunState` (in-memory): when `verbose` payload is present, populate `HostRunState.verbose` field; when absent (replay of old session), leave it `None`.

## 9. Size & truncation (answers Q4, Q10, Q22)

**Decision (revised per Q10=B): NO size caps. Trust the user. AOM does not impose any truncation or rotation.**

- `setup` module's `ansible_facts` (50–200 KB raw per host) is **NOT** written under `hosts.<host>.verbose` by default. Excluded via `exclude_modules` list (default: `["ansible.builtin.setup", "ansible.builtin.gather_facts"]`).
- **Opt-in to include setup** (per Q4): new flag `--capture-setup` (or `[capture] include_setup: true` in config) overrides the exclusion. CLI prints: `"--capture-setup enabled; ansible_facts will be persisted (expect 50-200KB/host)."`. When OFF (default), the `action: "ansible.builtin.setup"` line is still in `hosts.<host>` for visibility, but the `ansible_facts` dict is dropped from the `verbose` block.
- **No per-field cap, no per-session cap, no rotation.** The `events.jsonl` is whatever the user wrote. Disk usage is the user's responsibility; this is documented in the README.
- `results[]` (loop items): included; no cap.
- The `exclude_modules` list is the user's only "size" knob. Default behavior is conservative; users can override to `[]` to capture everything.

## 10. Live streaming inspect (answers Q23, Q25)

- While a run is in progress: `aom inspect <running-sid>` (with TUI's `V` keybind) works if the session is being recorded (reads partial `events.jsonl` and discovers `hosts.<host>.verbose` keys + `aom_verbose_line` events as they stream in).
- The unified `events.jsonl` already streams line-by-line as events arrive; the new `verbose` block + `aom_verbose_line` events ride on the same line, so no extra I/O coordination is needed.

## 11. CLI flags & config (answers Q33–Q36, plus Q4.2 refactor)

### Multi-layer config (locked in per Q4.2=B, Q4.3, Q17)

**Precedence (later wins):**
1. Built-in defaults (in `core/config.py` model defaults)
2. `/etc/aom/aom_config.yaml` (system-wide, read-only)
3. `~/.config/aom/aom_config.yaml` (user)
4. `./.aom_config.yaml` (project-local; walks up parent dirs to `/`)
5. `AOM_CONFIG` env var (path to a file; takes precedence over the above paths but NOT over `--config`)
6. `--config <path>` CLI flag (highest priority path)
7. CLI flags like `--capture-verbose`, `--capture-setup`, `--no-redact` (highest priority values, override config)

**Format**: YAML, schema validated by `pydantic-settings` `BaseSettings`.

**Implementation outline:**
- New module: `src/ansible_aom/core/config_layer.py` (~150-200 lines)
  - `find_config_paths() -> list[Path]`: walks the standard locations
  - `merge_configs(paths: list[Path]) -> dict`: deep-merge all YAMLs
  - `load_config_with_layers() -> AppConfig`: orchestrates the merge + validation
  - `migrate_legacy_config()`: detects old `~/.config/aom/config.yaml`, migrates to `aom_config.yaml`, moves old to `config.yaml.migrated` (per Q5=B auto-migrate silently)
- `core/config.py` extends: `AppConfig` gets a new `CaptureConfig` sub-model with `verbose`, `include_setup`, `exclude_modules`. `RedactionConfig` gets `enabled`, `ignored_arguments`, `ignored_value_patterns`. New `LiveConfig` with `show_failed_hint`, `show_warnings`, `show_deprecations`. `LoadConfigError` for missing-required-field cases.
- **Compact mode startup: `cli.py:_run_compact()` calls `load_config_with_layers()` BEFORE parsing CLI args** (per user requirement in Q4.2). The `AppConfig` instance is then merged with CLI flag overrides.
- TUI mode: same path — both modes go through the same loader.
- Logging on startup: `aom --verbose` shows which config files were loaded and the merged result. Default mode shows only the count.
- TUI settings screen (`tui/screens/settings.py`) continues to work but now edits the new `aom_config.yaml` path. Old TUI logic is adapted.

**First-run behavior:**
- On first run with no config file found, create `~/.config/aom/aom_config.yaml` with commented-out example content (all defaults explicit, all sections present but commented).
- If old `~/.config/aom/config.yaml` is found and `aom_config.yaml` is not: auto-migrate silently, print `INFO: migrated config.yaml → aom_config.yaml (v2 schema)`, move old file to `config.yaml.migrated`.

### Capture CLI flags (locked in per Q3=B, Q4=A, Q11=A)

- `aom --capture-verbose run site.yml` — opt-in to capture (default: off).
- `aom --capture-setup run site.yml` — opt-in to include `setup`/`gather_facts` payloads (default: off; only takes effect with `--capture-verbose`).
- `aom --no-redact run site.yml` — bypass redaction (only meaningful with `--capture-verbose`). CLI prints warning.
- `aom --no-failed-hint run site.yml` — disable failed-task hint in live view (default ON per Q6=B).
- `aom --hide-warnings run site.yml` — disable warnings in live view (default ON per Q7=D).
- `aom --hide-deprecations run site.yml` — disable deprecations in live view (default ON per Q7=D).
- `aom --config <path>` — explicit config file path (highest priority).
- `AOM_CONFIG=<path>` env var — config file path override.
- `aom inspect <sid> --debug` — show `aom_verbose_line` events at run level (per Q14.1, this is the only inspect flag; no `--verbose` global).
- AOM's existing `--verbose` (debug logging) is preserved per Q11=A.

**Flag interactions:**
- Default: no `verbose` block in `events.jsonl` lines. Backward compatible.
- `--capture-verbose` ⇒ `hosts.<host>.verbose` populated + `aom_verbose_line` events emitted. CLI prints: `"verbose capture enabled; secrets will be redacted (use --no-redact to disable)."`.
- `--capture-verbose --capture-setup` ⇒ `ansible_facts` included. CLI prints additional warning about size.
- `--capture-verbose` + `--no-record` ⇒ error: `"--capture-verbose requires recording; remove --no-record."`

### Config schema (excerpt, `~/.config/aom/aom_config.yaml`)

```yaml
# AOM configuration. Layered: built-in defaults < /etc/aom/aom_config.yaml < ~/.config/aom/aom_config.yaml < ./.aom_config.yaml < --config < CLI flags.

capture:
  verbose: false          # default: false (opt-in)
  include_setup: false    # default: false (excludes ansible.builtin.setup / gather_facts)
  exclude_modules:        # additional modules to exclude from verbose capture (union with built-in defaults)
    - ansible.builtin.debug

redaction:
  enabled: true           # default: true (always-on)
  ignored_arguments: []   # extra deny-list (key name substring match)
  ignored_value_patterns: []  # regex patterns on values

live:
  show_failed_hint: true  # show first line of msg for failed/unreachable
  show_warnings: true     # show warnings in live view
  show_deprecations: true # show deprecations in live view

inspect:
  # Future: per-tab configuration, default tab, etc. (out of scope for v1)
```

## 12. Schema migration (answers Q29, Q31, Q9=B no version bump)

- `HostRunState` (`core/models.py:181`) gains optional fields: `msg: str | None`, `stdout: str | None`, `stderr: str | None`, `invocation: dict | None`, `diff: list | None`, `results: list | None`, `warnings: list | None`, `deprecations: list | None`. All optional → backward compatible.
- New frozen dataclass `core/inspect_model.py`: `VerbosePayload(msg, stdout, stderr, invocation, diff, results, warnings, deprecations, _ansible_no_log)` consumed by both live (optional population) and inspect (consumer).
- New event type `aom_verbose_line` in `core/event_types.py`: `JsonlVerboseLine(level: int, source: str, message: str, host: str | None)`. Synthetic, emitted by AOM's PTY parser when `--capture-verbose` is on.
- `RunConfigKey` (`core/run_config.py`) version bump not needed — no field is part of identity.
- `events.jsonl` schema gains one optional nested key (`hosts.<host>.verbose`) plus one new event type (`aom_verbose_line`). No `_schema_version` field (per Q9=B).

## 13. Test plan

Unit (`tests/unit/`):
- `test_redaction_layer4.py` — verify wiring of `redact_event` against sample JSONL events; assert hard-coded deny-list applied to `invocation.module_args`; assert user-configured deny-list layered on top.
- `test_verbose_capture.py` — parser populates `hosts.<host>.verbose` correctly for `v2_runner_on_*`; default exclusion of `setup`/`gather_facts`; `--capture-setup` override.
- `test_verbose_inspect.py` — `inspect_model.VerbosePayload` round-trips; `V` keybind context-resolution (host → play → run).
- `test_no_log_trust.py` — `no_log: true` events bypass redaction (collapsed `censored` payload passes through).
- `test_aom_verbose_line.py` — synthetic event type emitted by PTY parser when `Display.vvvv()` line detected; level + source classification correct.
- `test_config_layer.py` — multi-layer config precedence (built-in < /etc/ < user/ < local/ < env/ < --config/ < CLI); migration of old `config.yaml` to `aom_config.yaml`; YAML merge deep.
- `test_size_no_caps.py` — verify NO truncation/rotation; capture writes full content.
- `test_failed_hint.py` — `show_failed_hint` config knob; first-line extraction; redaction applied to hint.

Integration (`tests/integration/`):
- Add a playbook with `no_log: true`, secrets in vars, `setup` module, `template` task with `--check` diff. Verify `events.jsonl` content (and absence of `ansible_facts` by default; presence with `--capture-setup`).
- Add a multi-host playbook; verify each host-result has its own `verbose` block.
- Verify `aom --capture-verbose` flag produces the right CLI banner; verify `aom inspect <sid>` (with TUI) shows the `(verbose data not captured)` fallback for sessions without capture.

TUI (`tests/tui/`):
- Snapshot tests for InspectApp's `V` keybind at host, play, and run levels.
- Snapshot test for the `[REDACTED:password]` dim grey rendering.

Fixtures (`tests/fixtures/`):
- New JSONL fixtures: `verbose_with_no_log.jsonl`, `verbose_with_diff.jsonl`, `verbose_with_setup.jsonl` (setup should be excluded), `verbose_with_redoction.jsonl` (module_args redacted), `aom_verbose_line_mixed.jsonl` (synthetic events).

## 14. Documentation (answers Q37–Q39)

- `SPECIFICATION.md`: new section §5.10 "Verbose Capture & Inspect". Mirrors the structure above.
- `ARCHITECTURE.md`: update data-flow diagram; document `aom_verbose_line` synthetic event; document multi-layer config system in §4.
- `README.md`: brief paragraph on `--capture-verbose` flag and the inspect TUI's `V` keybind; mention multi-layer config in a new "Configuration" section.
- `aom --help`: list new flags (`--capture-verbose`, `--capture-setup`, `--no-redact`, `--no-failed-hint`, `--hide-warnings`, `--hide-deprecations`).
- `aom inspect --help`: list `--debug` flag.

## 15. Migration / rollout

- **No data migration for sessions**: read-only fallback for old sessions; new sessions recorded without `--capture-verbose` look identical to old ones.
- **Config migration (auto, per Q5=B)**: on first run, AOM detects old `~/.config/aom/config.yaml`, migrates to `~/.config/aom/aom_config.yaml`, prints `INFO: migrated config.yaml → aom_config.yaml (v2 schema)`, moves old to `config.yaml.migrated`. No user action required.
- Feature is opt-in (per Q3=B); users discover it via README, `aom --help`, and the inspect TUI's "(verbose data not captured)" hint.
- AOM version bump to v0.x+1 (minor): new feature, backward-compatible.
- Rollout: ship behind `--capture-verbose` for one minor release, then potentially flip default to ON in a later release if disk usage proves acceptable.

## 16. Out-of-scope (explicit non-goals for v1)

- Encrypting `events.jsonl` at rest (no `--encrypt-session` flag in v1; v2 if needed).
- Per-field toggle UI in inspect TUI (deferred; `V` keybind shows everything available).
- Aggregated/structured redaction of nested values (e.g., YAML-loaded vars in `invocation.module_args` that contain secrets 2 levels deep) — apply surface-level match only in v1.
- Multi-session comparison of verbose data (`aom inspect diff <sid1> <sid2>` for verbose) — future iteration.
- Auto-classification of `aom_verbose_line` source beyond the heuristic prefixes (no ML or fuzzy matching).
- Live streaming of verbose data to a separate TUI window while the run is in progress (deferred; `aom inspect` during a run works via the partial-`events.jsonl` read, but no separate window).

## 17. Risks & open questions for sign-off

Risks:
- **Disk usage** (per Q10=B, no caps): a 100-host run with `--capture-setup` could write 20+ MB of `ansible_facts`. User must opt in. Mitigation: `exclude_modules` config knob is documented; `setup`/`gather_facts` excluded by default.
- **Privacy**: even with the deny-list, `module_args` may leak env var values via keys not in the deny-list. Mitigation: hard-coded deny-list at capture time (per Q2=A); user can extend via `[redaction] ignored_arguments` in config; `--no-redact` flag for the user to opt out (with warning).
- **Test coverage gap**: existing fixtures don't cover `no_log: true` paths or `aom_verbose_line` synthetic events. Mitigation: new fixtures listed in §13.
- **Config migration surprise**: users with `~/.config/aom/config.yaml` find their file renamed on first run with the new version. Mitigation: `INFO: migrated config.yaml → aom_config.yaml` banner; old file moved to `config.yaml.migrated` so it's not lost.
- **Compact mode startup cost**: multi-layer config load adds ~50ms to startup. Mitigation: cache compiled config in `~/.cache/aom/` keyed by mtime; fall back to file read on cache miss.
- **No `_schema_version` field** (per Q9=B): future schema changes won't have an explicit migration path. Mitigation: rely on field-absence tolerance; document the pattern for future contributors.

**All design decisions are resolved (Q1-Q17).** No open sign-off items.
- **Q22**: Exclude `setup`/`gather_facts` from capture. Confirm OK?
- **Q29**: Schema version bump in `meta.json` — confirm `_schema_version: 2`?

## Q&A log

### Q1 — Mental model check (capture philosophy)
- Asked: A (re-persist), B (sidecar), C (in-memory), D (other)? Recommendation: A.
- Captured: User picked **B** — unified `events.jsonl` with optional verbose fields. Schema extends rather than adds a sidecar file.
- Implication: `events.jsonl` schema becomes a superset. Replay driver, `prune`, `rerun` need to be tolerant of the new fields. `RunConfigKey` may need a version bump.
- Flags: Q2 (sidecar vs unified logic) and Q25 (streaming writes) are now resolved by this single decision.

### Q1.1 — Schema extension shape (auto-derived from Q1=B)
- Q: How do we add verbose fields to existing event lines?
- Captured: Add an OPTIONAL `verbose` key to the `hosts.<host>` dict of `v2_runner_on_*` events. Absent when capture disabled or in old sessions. `events.jsonl` readers ignore unknown fields by default (orjson default).
- Status: Resolved.

### Q2 — Redaction policy
- Asked: A (redact at capture, deny-list, default-on), B (redact at display), C (no redaction), D (other)? Recommendation: A.
- Captured: User picked **A** — redact at capture time, hard-coded deny-list, always-on. User can extend via config. Opt-in `--no-redact` flag as safety valve.
- Implication: §6 is the authoritative spec. `core/redaction.py` Layer 4 must be wired in. Need a new `--no-redact` CLI flag (default off → redaction on). The deny-list keys are: `password`, `passwd`, `secret`, `token`, `api_key`, `private_key`, `ssh_pass`. Add to deny-list: case-insensitive matching. Substring match on key names.

### Q3 — Default capture state
- Asked: A (on by default), B (off by default, opt-in), C (per-run prompt), D (other)? Recommendation: A.
- Captured: User picked **B** — capture is **off by default**. Users opt in via `--capture-verbose` flag or `[capture] verbose: true` in config.
- Implication: §11 (CLI flags) changes meaning. `--capture-verbose` is the default name (rather than the opt-out `--no-capture-verbose`). Default `--no-capture-verbose` is the implicit state. The flag is now mandatory to get any verbose data. The `--no-redact` safety valve still works (it only takes effect if capture is on).
- Documentation impact: README + `aom --help` must clearly explain that verbose is opt-in. Many users may not discover the feature without it being highlighted.
- Pre-flight: `aom site.yml` shows nothing in `events.jsonl` for verbose fields. `aom site.yml --capture-verbose` does. Equivalent to a feature flag.

### Q4 — Setup module exclusion
- Asked: A (exclude by default), B (include by default), C (truncate keys only), D (other)? Recommendation: A.
- Captured: User picked **A — exclude `setup`/`gather_facts` by default** AND wants the exclusion itself to be an additional opt-in flag (i.e. a separate `--capture-setup` or `[capture] include_setup: true` knob to override the exclusion).
- Implication: §9 (size & truncation) gains a second config knob. `exclude_modules` becomes the default; `include_modules` or `include_setup` is the opt-in. New CLI flag: `--capture-setup` enables setup/facts in the verbose block.
- Sub-question raised by user: "Do we already have a configuration file listener?"
  - **Sub-Q4.1 — Existing config-file infrastructure**: verified via codebase inspection. AOM has a partial config layer at `~/.config/aom/config.yaml` (YAML, single path, in `core/config.py`). It is only loaded by the TUI settings screen (`tui/screens/settings.py:33`), NOT by compact mode startup. There is no multi-layer hierarchy (no global `/etc/aom/`, no local `./.aom_config`, no `--config` CLI flag, no env-var override), even though SPECIFICATION.md §8 (lines 2112–2210) promises one. `pydantic-settings` is a dependency but is NOT being used for file loading (`SettingsConfigDict()` is empty in `core/config.py:45`).
  - **User feedback**: "when not we should do that for global, user and local specific settings" — user wants a proper multi-layer config infrastructure built as part of this feature.
  - **Implication**: §11 (CLI flags & config) becomes much larger. The capture feature now requires a config-layer refactor as a prerequisite, OR a smaller "minimal config" path that only handles the new capture settings. **Decision needed on Q4.2 below** before Q5+ can proceed.

### Q4.2 — Config-file scope
- Asked: A (minimal), B (full multi-layer), C (hybrid), D (pydantic-settings native)? Recommendation: C.
- Captured: User picked **B — full multi-layer refactor** with the requirement that the new config system **must be used by compact mode** (not just TUI settings). 
- Implication: The capture feature now includes a config-layer refactor as a hard prerequisite. §11 expands substantially. Compact mode startup (`cli.py:_run_compact`) must call `load_config()` and merge layers. The current "compact mode ignores config" behavior is removed.
- New config paths (per user):
  - `/etc/aom/aom_config` (global, system-wide defaults; read-only at runtime)
  - `~/.config/aom/aom_config` (user; the current `~/.config/aom/config.yaml` is renamed to match)
  - `./.aom_config` (project-local, walks up parent directories until found or `/` is hit)
  - `--config <path>` CLI flag (override)
  - `AOM_CONFIG` environment variable (override)
- Precedence (later wins, lower number = lower priority):
  1. Built-in defaults (in code)
  2. `/etc/aom/aom_config` (global)
  3. `~/.config/aom/aom_config` (user)
  4. `./.aom_config` (local, deepest first)
  5. `AOM_CONFIG` env var (path override)
  6. `--config <path>` CLI flag (path override)
  7. CLI flags like `--capture-verbose` (always win, applied last)
- Format: YAML (consistent with current `core/config.py`).
- Reuse `pydantic-settings` `BaseSettings` for env-var handling; do the YAML layered loading manually with a `merge()` helper (current `load_config()` is the seed).
- File-naming: user specified `aom_config` (no extension). The current `~/.config/aom/config.yaml` is renamed → `~/.config/aom/aom_config` (or keep both as fallback? — covered in Q4.3).
- **New sub-question raised**: should the old `config.yaml` path be kept as a fallback for backward compatibility, or are we doing a hard rename?

### Q4.3 — Old config path compatibility
- Q: Keep `~/.config/aom/config.yaml` as a fallback so existing user configs don't break, OR hard rename to `aom_config`?
- Recommendation: **Keep the old path as a fallback** for one minor version. If both exist, the new `aom_config` wins and the old is read with a deprecation warning. After deprecation period, drop the old path.
- Captured: User picked **B — hard rename, no fallback for old config.yaml**. App is in heavy development, so breaking changes are fine. Old `config.yaml` will be auto-migrated silently on first run.
- Auto-migration flow: on startup, if `config.yaml` is found and `aom_config.yaml` is not, AOM reads the old file, translates the schema, writes to `aom_config.yaml`, prints `INFO: migrated config.yaml → aom_config.yaml (v2 schema)`, and moves the old file to `config.yaml.migrated`. No `aom --init-config` command needed for v1.
- File extension: User confirmed `.yaml` is the right extension.
- Final canonical paths:
  - `/etc/aom/aom_config.yaml`
  - `~/.config/aom/aom_config.yaml`
  - `./.aom_config.yaml` (walks up to `/`)

## Open flags (pending input)
- (none yet — interview will populate)
---

# FINAL RECAP

**Date**: 2026-06-29 (updated 2026-06-30)
**Topic**: How should ansible-aom handle verbosity-controlled output (live-hide, post-run inspect)?
**Goal achieved**: A concrete implementation plan with full design rationale, anchored in empirical research, and 17 design decisions locked in.

## Research summary (5 parallel investigations + 1 re-verification)

1. **Ansible verbosity levels** (`-v` to `-vvvvvv`): mapped each level's human output, sourced from ansible-core `Display.v()`/`vv()`/etc. and `default.py` callback's `_dump_results`.
2. **JSONL callback source code**: confirmed `ansible.posix.jsonl` is verbosity-agnostic. No `self._display.verbosity` checks anywhere in the 175-line source.
3. **JSONL empirical test (initial)**: ran a 4-task playbook on localhost at all 6 verbosity levels with `ANSIBLE_STDOUT_CALLBACK=ansible.posix.jsonl`. Identical 10 events, identical fields, identical schema.
4. **JSONL empirical test (re-verification on user request)**: ran a 1-task playbook at all 7 levels (default + -v through -vvvvvv). Same result — JSONL is byte-identical in shape; only timestamps and UUIDs differ. Non-JSONL content grows from 2 lines (default) to 97 lines (-vvvvvv) — all `Display.vvvv()` plugin-loader / inventory / callback chatter.
5. **Existing codebase inventory**: `events.jsonl` already strips `msg`/`stdout`/`stderr`/`invocation.module_args`/`diff`/`results[]` via `RECORD_EVENT_KEEP_FIELDS`. `redact_event` Layer 4 is built but unwired. `DetailBlock` is the inspect hook point. Config is partial (single path `~/.config/aom/config.yaml`, only loaded by TUI settings screen; no multi-layer).
6. **Comparable tools** (AWX, ansible-navigator, ARA, ansible-runner, nom, tui-logger): converged finding — "capture once, filter at display" is the universal pattern. Verbosity is a display filter, not a capture filter.

## What's captured in this file

- **Question Backlog**: 43 design questions across 8 categories (Capture, Redaction, Live, Inspect, Edge cases, PTY, Implementation, Config, Docs, Architecture).
- **Q&A log**: 17+ locked-in design decisions (Q1-Q17, plus Q4.2, Q4.3, Q13.1, Q14.1).
- **Implementation Plan**: 17 sections covering architecture, storage, live contract, inspect UX, redaction, PTY, backward compat, schema, tests, docs, rollout, out-of-scope, risks, sign-off decisions.
- **Anchor research notes**: JSONL events, verbose-field matrix, stderr caplevel mapping, exact file/line anchors for the implementation.

## The reframe (most important takeaway)

The user's mental model was "verbosity makes new data appear that we need to capture". Reality: **verbosity controls what ansible's `default` callback displays to stdout, not what the JSONL callback captures**. JSONL always carries the verbose fields. So AOM's job is to **re-persist what it currently throws away**, not to discover what verbosity unlocks.

The single non-JSONL content that's verbosity-dependent is `Display.vvvv()` plugin-loader / connection debug chatter, which goes to stderr. Per Q13, this is captured as synthetic `aom_verbose_line` events in `events.jsonl` when `--capture-verbose` is on.

## Key design decisions in the plan (locked in)

1. **Storage** (Q1=B): Unified `events.jsonl` with optional `hosts.<host>.verbose` block. No sidecar. Plus one new event type `aom_verbose_line` (Q13).
2. **Redaction** (Q2=A): At capture time, hard-coded deny-list, always-on, opt-out via `--no-redact` flag. Dim grey display for `[REDACTED:key]` (Q16=A).
3. **Default state** (Q3=B): Capture OFF by default. Opt-in via `--capture-verbose`. Status bar shows `● REC+VC` when on (Q15=B).
4. **Setup module** (Q4=A + user opt-in): `setup`/`gather_facts` excluded by default. Opt-in via `--capture-setup`.
5. **Config** (Q4.2=B, Q4.3, Q17=A): Full multi-layer config (`/etc/aom/aom_config.yaml`, `~/.config/aom/aom_config.yaml`, `./.aom_config.yaml`, `AOM_CONFIG` env var, `--config` flag). Hard rename from `config.yaml` (no backward compat; auto-migrate on first run per Q5=B). Single file with sections.
6. **Live view** (Q6=B, Q7=D): Failed-task hint default ON (first line of `msg` for `failed`/`unreachable`). Warnings and deprecations default ON, both configurable.
7. **Inspect view** (Q8=A, Q14.1=Alt 1): Tabbed DetailBlock. Single `V` keybind, context-sensitive (host / play / run). No global `--verbose` flag.
8. **Schema** (Q9=B): No `_schema_version` bump. Verbose block is strictly optional; readers tolerate.
9. **Size caps** (Q10=B): NO caps. Trust the user. `exclude_modules` is the only size knob.
10. **CLI naming** (Q11=A): AOM's `--verbose` (debug) stays distinct from new `--capture-verbose` (capture).
11. **Vault prompts** (Q12=A): Not captured; PTY parser handles them safely.
12. **Redaction display** (Q16=A): Dim grey `[REDACTED:key]`. Raw secrets in red when `--no-redact` is on.

## Open decisions to sign off

None — all 17 major questions are answered.

## Suggested next step

The plan is ready for implementation. Suggested order:

1. **Foundation (TDD)**:
   - Multi-layer config (`core/config_layer.py`, `migrate_legacy_config`, `find_config_paths`, `merge_configs`).
   - Extend `core/config.py` models: `CaptureConfig`, `RedactionConfig` (with deny-list), `LiveConfig`.
   - Wire `load_config_with_layers()` into `cli.py:_run_compact()` startup path (was the user's hard requirement).

2. **Capture (TDD)**:
   - `core/redaction.py` Layer 4 wiring — apply deny-list at capture time.
   - `session/store.py` `RECORD_EVENT_KEEP_FIELDS` extension — add `verbose` to allowlist when capture is on.
   - `core/parser.py` 3-phase parser extension — emit `aom_verbose_line` synthetic events.
   - New synthetic event type in `core/event_types.py`.

3. **Live view (TDD)**:
   - `HostRunState` gains optional `verbose`, `msg_first_line` fields.
   - `compact/renderer.py` status bar — `● REC+VC` indicator.
   - `compact/renderer.py` failed-task hint.
   - Warnings / deprecations inline.

4. **Inspect view (TDD)**:
   - `tui/widgets/verbose_view.py` new widget with tabs.
   - `tui/screens/inspect.py` — `V` keybind, context resolution.
   - Dim grey redaction rendering.

5. **CLI (TDD)**:
   - New flags: `--capture-verbose`, `--capture-setup`, `--no-redact`, `--no-failed-hint`, `--hide-warnings`, `--hide-deprecations`, `--config`.
   - `AOM_CONFIG` env var support.
   - `aom inspect <sid> --debug` (run-level verbose log).

6. **Tests + fixtures**:
   - New unit tests for every layer.
   - New JSONL fixtures (one per scenario).
   - TUI snapshot tests for the `V` keybind.

7. **Docs**:
   - `SPECIFICATION.md` §5.10.
   - `ARCHITECTURE.md` updated data-flow.
   - `README.md` new section.
   - Help text updates.

8. **Rollout**:
   - Minor version bump.
   - CHANGELOG entry.
   - Migration tested with both old-format and new-format configs.

The total scope is significant (~1500-2000 LOC of new code, including tests). Recommend 3-5 PRs over 2-3 weeks.

**No further action required from the user at this stage unless they want to answer the 5 sign-off questions.** The capture file is the durable artifact — if the user wants to revisit Q1-Q43 later or change answers, they can edit the file directly.

---

## Appendix: Anchor research notes

### A. JSONL event types in current AOM parser (`core/run_state.py:handler_map`)
- `v2_playbook_on_start`, `v2_playbook_on_play_start`, `v2_playbook_on_task_start`, `v2_playbook_on_handler_task_start`, `v2_runner_on_start` (non-lockstep), `v2_runner_on_ok`/`_failed`/`_skipped`/`_unreachable`, `v2_runner_item_on_ok`/`_failed`/`_skipped` (added by `aom_jsonl.py`), `v2_playbook_on_stats`. Unknown events tallied in `unknown_events` dict.

### B. Verbosity-gated content in JSONL
Empirical (ansible-core 2.20.4, 4-task localhost playbook, ANSIBLE_STDOUT_CALLBACK=ansible.posix.jsonl):
- `-v` and `-vvvvvv` produce **identical** 10 JSONL events.
- `v2_runner_on_ok` for a shell task contains (verbatim, all 6 levels): `action`, `changed`, `cmd`, `delta`, `start`, `end`, `invocation.module_args` (12 keys), `msg`, `rc`, `stderr`, `stderr_lines`, `stdout`, `stdout_lines`.
- `v2_runner_on_failed` additionally has `exception`, `failed_when_result`, `failed: true`.
- No `_verbosity` or `_v` field exists in any event.
- `no_log: true` collapses the host result to `{censored: "the output has been hidden...", _ansible_no_log: true}` (plus `exception` on failure).

### C. JSONL-emitted verbose fields (already in stream, just stripped on persist)
| Field | Verbosity needed for it to be in `default` callback stdout | Verbosity needed for it to be in JSONL stream | AOM today persists it? |
|---|---|---|---|
| `msg` (result message) | 0 | 0 (always) | No (`RECORD_EVENT_KEEP_FIELDS` strips) |
| `stdout` / `stderr` | 0 | 0 (always) | No |
| `stdout_lines` / `stderr_lines` | 0 | 0 (always) | No |
| `invocation.module_args` | `-vvv` (default strips <3) | 0 (always in JSONL) | No |
| `diff` | `-vvv` (default strips <3) | 0 (always in JSONL) | No |
| `results[]` (loop items) | 0 | 0 (always) | No |
| `ansible_facts` | 0 | 0 (always, when setup module) | No |
| `exception` (on fail) | `-vv` | 0 | No |
| `warnings` | 0 | 0 | No |
| `deprecations` | 0 | 0 | No |

### D. Verbosity-gated content NOT in JSONL (lives in PTY stderr)
- `Display.v()` lines: only at verbosity ≥ 1, to stderr. (Standard `-v` shows task banner prefix.)
- `Display.vv()` lines: only at ≥ 2. (`NOTIFIED HANDLER` etc.)
- `Display.vvv()` lines: only at ≥ 3. (Connection-level debug.)
- `Display.vvvv()` lines: only at ≥ 4. (Loading callback plugin etc.)
- `Display.vvvvv()` lines: only at ≥ 5. (Internal Ansible plugin debug.)
- `Display.vvvvvv()` lines: only at ≥ 6. (Maximum debug.)
- All routed via `Display.verbose(msg, host=host, caplevel=N)`; line emission threshold: `self.verbosity > caplevel`. Destination: stderr (when `VERBOSE_TO_STDERR=True`, default).

### E. Anchor files (for later implementation)
- `src/ansible_aom/session/store.py:57-71` — `RECORD_EVENT_KEEP_FIELDS` (the strip filter)
- `src/ansible_aom/core/redaction.py:280-283` — Layer 4 invocation.module_args (built, unwired)
- `src/ansible_aom/core/inspect_model.py:511-637` — `DetailBlock` (the inspect view hook)
- `src/ansible_aom/tui/screens/inspect.py:443` — `InspectApp` (3-pane: Runs / Tasks / Detail)
- `src/ansible_aom/core/run_state.py:1208-1212` — only existing live-state touch of verbose fields (`_ansible_verbose_always.ignore_errors`)
- `src/ansible_aom/cli.py:200-203` — `-v reserved for ansible-playbook` banner
- `src/ansible_aom/core/run_config.py:19-29` — `_IGNORED_BOOLEAN_FLAGS` strips `-v`/`-vv`/`-vvv`/`-vvvv` from identity key
- `src/ansible_aom/inspect/cli.py:70-77` — `inspect prune` / `inspect --debug`
- `src/ansible_aom/inspect/text.py:159` — `render_session` (CLI text inspect)

---

## Q&A log (continued, session 2)

### Q6 — Live view: failed-task hint
- Asked: A (off, no hint), B (default ON), C (default OFF, opt-in), D (other)? Recommendation: B.
- Captured: User picked **B** — default ON. Show first line of `msg` (after redaction) for `failed` and `unreachable` tasks in the compact log. Helps users spot failure causes without opening inspect.
- Implication: §4 (live-view contract) updated. Live renderers gain a `failed_hint: str` field on `HostRunState`. New config: `[live] show_failed_hint: true` (default). New CLI flag: `--no-failed-hint`. Hint is color-coded red, prefixed with task name, width-limited.
- Net change to the original "don't show verbose in live" intent: the first line of `msg` is now visible in live, but only for failed/unreachable. This is the minimum needed for failure-feedback without breaking the "hide verbose" rule for successful tasks.

### Q7 — Warnings & deprecations
- Asked: A (warnings only), B (both), C (neither), D (configurable)? Recommendation: D.
- Captured: User picked **D — configurable, both default TRUE**. `[live] show_warnings: true`, `[live] show_deprecations: true`. CLI flags: `--hide-warnings` and `--hide-deprecations` to disable per-run.
- Implication: §4 gains two new config fields and two new CLI flags. Both fields are also captured in the verbose block (subject to `--capture-verbose`).

### Q8 — Inspect view layout
- Asked: A (tabs), B (scrollable block), C (drill-in tree), D (other)? Recommendation: A.
- Captured: User picked **A — tabbed view** in the Detail pane. Tabs: `Summary` (current), `Stdout`, `Stderr`, `Module Args`, `Diff`, `Raw PTY`. `Tab`/`1`-`5` cycles. Per-host via `h`/`l`.
- Implication: §5 (Inspect view design) is the authoritative spec. `tui/screens/inspect.py:443 InspectApp` gets a new `TabbedDetailBlock` widget. Tabs are conditional — only shown when verbose capture was on for the session. If capture was off, the existing summary view stays.
- This pattern matches AWX + ansible-navigator convergence noted in research.

### Q9 — Schema versioning
- Asked: A (`_schema_version: 2` in `meta.json`), B (no bump, optional field), C (major version)? Recommendation: A.
- Captured: User picked **B — no version bump, just an optional field**. The `hosts.<host>.verbose` block is strictly optional. Readers that don't understand it skip it (orjson / json default). Forward + backward compat via field absence.
- Implication: §8 (backward compat) and §12 (schema migration) simplify. No `_schema_version` field in `meta.json`. The "old session fallback" message uses session age (`mtime`) or `meta.json`'s `aom_version` field that's already there, not a schema version.
- This is the lightest-touch approach. Future schema changes (if any) would still need versioning, but for this specific feature addition it's not warranted.

### Q10 — Size caps
- Asked: A (256KB/field, 100MB/session), B (no caps), C (64KB/field, 10MB/session), D (configurable with defaults)? Recommendation: D.
- Captured: User picked **B — no caps, trust the user**. AOM does not impose size limits on verbose fields or on the total session file. The user is responsible for disk usage.
- Implication: §9 (size & truncation) shrinks dramatically. No truncation logic. No `events.jsonl.1` rotation. The file is whatever the user wrote, no max.
- The only remaining "size" knob is `exclude_modules` (default includes `setup`/`gather_facts`) — but the user explicitly chose B, so this is also configurable: `[capture] exclude_modules: []` (default = `["ansible.builtin.setup", "ansible.builtin.gather_facts"]`), overridable to empty for "include everything".
## Open flags (pending input)
- (none yet — interview will populate)
### Q11 — Naming: `--verbose` collision
- Asked: A (keep both names distinct), B (rename AOM's `--verbose`), C (repurpose AOM's `--verbose`), D (other)? Recommendation: A.
- Captured: User picked **A — keep both names distinct**. AOM's existing `--verbose` (debug logging) stays. New feature uses `--capture-verbose` for JSONL payload capture. Two distinct concepts, two distinct flags.
- Implication: §11 (CLI flags) confirms the dual-naming. Users can combine: `aom --verbose site.yml --capture-verbose` = AOM debug + JSONL capture. No deprecation needed.
- Documentation impact: README + `aom --help` should explicitly distinguish the two flags with separate help sections.


### Q12 — Vault password prompts
- Asked: A (don't capture), B (separate protected log), C (capture to stderr.log)? Recommendation: A.
- Captured: User picked **A — don't capture vault prompts**. AOM's existing PTY parser (`core/parser.py` 3-phase `PRE_RUN_PROMPTS` mode) detects and responds to vault password prompts interactively. They never touch JSONL or any persistent log. Safe by design.
- Implication: No new code needed. The `--capture-verbose` flag doesn't change this. If a user runs `aom site.yml --ask-vault-pass`, the password prompt is sent to AOM's stdin via pexpect, answered, and never written to disk. Confirmed safe.


### Empirical re-verification (2026-06-30)
Per user's request, re-ran the verbosity test across all 7 levels (0, -v, -vv, -vvv, -vvvv, -vvvvv, -vvvvvv) on a localhost playbook to confirm what is and isn't in JSONL.

**Result: JSONL is byte-identical in shape across all 7 levels.**

| Level | JSONL events | File size | Non-JSONL lines |
|---|---|---|---|
| (default) | 4 | 1939 B | 2 (warnings only) |
| `-v` | 4 | 1976 B | 3 (+ "No config file") |
| `-vv` | 4 | 2947 B | 16 (CLI version banner) |
| `-vvv` | 4 | 5229 B | 34 (plugin search paths) |
| `-vvvv` | 4 | 5581 B | 38 (+callback plugin loading) |
| `-vvvvv` | 4 | 9711 B | 97 (full plugin/inventory debug) |
| `-vvvvvv` | 4 | 9719 B | 97 (no additional change) |

**JSONL events at -v and -vvvvvv are structurally identical** (verified by diff'ing the field sets). The only differences between levels are timestamps and UUIDs.

**No `verbosity` / `v` / `level` / `display_verbosity` field exists in any event** (verified via grep across all 7 runs).

**The non-JSONL content at higher levels is all `Display.vvvv()`-type plugin loading, inventory loading, and callback loader chatter.** Sample at -vvvvv:
```
[WARNING]: No inventory was parsed, only implicit localhost is available
[WARNING]: provided hosts list is empty...
ansible-playbook [core 2.20.4]
  config file = None
  configured module search path = [...]
  ...
Loading collection ansible.posix from /home/xyz00777/.ansible/collections/...
Loading callback plugin ansible.posix.jsonl of type stdout, v2.0 from ...
Attempting to use 'default' callback.
Skipping callback 'default', as we already have a stdout callback.
Attempting to use 'junit' callback.
Attempting to use 'minimal' callback.
```

These are NOT in JSONL. They are written by `Display.verbose(msg, host=None, caplevel=N)` to the worker process's stderr file descriptor, bypassing stdout callbacks.

**Conclusion: my original claim was correct.** JSONL is verbosity-agnostic. All verbose data is in the JSONL stream at every -v level. The user was right to be skeptical of "they would already be in the jsonl logs" — I should clarify that I meant: the verbose *result* data (module args, stdout, stderr, etc.) is in JSONL. The verbose *plugin loader* debug noise is NOT in JSONL — it's in stderr.

### Q13 — Capture `Display.vvvv()` plugin-loader / connection lines
- Asked: A (no capture, stderr.log only), B (sidecar file), C (tag stderr.log), D (other)? Recommendation: A.
- Captured: User picked **D-variant** — wants the verbose stderr lines in a structured format, in the saved log, if `--capture-verbose` is used. NOT a separate sidecar; integrate into the existing `events.jsonl` stream.
- Implication: We need a new synthetic JSONL event type (e.g., `v2_runner_on_debug` or `v2_verbose_line`) that AOM emits when its PTY parser detects a `Display.vvvv()`-style line. Each line carries: `level` (caplevel 1-5), `source` (heuristic: `plugin_load` | `connection` | `inventory` | `callback_load` | `internal`), `message`, `host` (if applicable), `timestamp`. These synthetic events ride on the same `events.jsonl` stream as the JSONL-from-ansible events.
- Implementation: AOM's PTY parser (currently in `core/parser.py` 3-phase mode) gains a stderr-line classifier that emits structured events when a verbose line is detected. The classifier must be conservative — only tag lines that match a known `Display.vvvv()` pattern (e.g., `Loading collection…`, `Loading callback plugin…`, `Attempting to use…`).
- Inspect view: new tab "Debug" surfaces these events in chronological order. Filter by caplevel.
- Storage: unified `events.jsonl` (no sidecar). Schema extension: one new event type with a stable, distinct `_event` value.
- Trade-off: this is more code than just leaving stderr.log. But the user wants structure, and the request is reasonable.
- Naming: `v2_verbose_line` is the proposed event name. Could be `aom_verbose_line` to make it clear it's AOM-emitted (not ansible-emitted). Recommend `aom_verbose_line` for clarity.

### Q13.1 — Verbose-line caplevel threshold
- Q: At what caplevel do we start capturing `Display.v*` lines?
- Recommendation: Capture at all caplevels 1-5 (i.e., any time `--capture-verbose` is on and a verbose line is emitted by ansible). The caplevel is part of the structured payload, so users can filter.
- Status: Implicit in Q13 answer; not asking.

### Q13.2 — Verbose-line classifier rules
- Q: How do we know a stderr line is a verbose line vs. an error?
- Recommendation: Heuristic — match against a small set of known `Display.vvvv()` prefixes: `Loading `, `Attempting `, `Skipping `, `config file`, `Setting up`, `host_list `, `script `, etc. Lines that don't match are passed through to `stderr.log` as before (no synthetic event). Keep the classifier conservative (false negatives are OK; false positives are noise).
- Status: Implementation detail; not asking.


### Q14 — Inspect view default + contextual debug buttons
- Asked: A (default Summary, opt-in --verbose), B (smart default), C (always show compact verbose), D (other)? Recommendation: A.
- Captured: User picked **D — default normal view (current Summary), add contextual debug buttons**. The user is uncertain about how granular to make the buttons.
- My recommendation (per user request):
  - **Inspect TUI Detail pane** keeps the current Summary as the default first view (no change from current AOM).
  - **At the host level** (Detail pane showing one task × one host): a `[H] Host debug` button (or key `H`) opens a pop-up / split view that surfaces all verbose data for that host×task: `Module Args`, `Stdout`, `Stderr`, `Diff`, `Raw PTY` — all tabs available even if `--capture-verbose` was off, but the pop-up shows "(verbose data not captured for this run)" if absent.
  - **At the play level** (Runs pane showing a play): a `[P] Play debug` button (or key `P`) opens a per-play summary: connection-debug events (`aom_verbose_line` from Q13 with `source: "connection"`), plugin-loader events, and any errors.
  - **At the run level** (top-level Runs pane): a `[R] Run debug` button (or key `R`) opens the full `aom_verbose_line` event log for the entire run, filterable by caplevel (1-5) and source.
  - These buttons are *always present* in the TUI but they only show data when `--capture-verbose` was on; otherwise they show a fallback message.
  - This pattern matches `awx_job_events.md` "filter modes" and `nom`'s status panel — context-aware drill-down without forcing verbose everywhere.
  - **CLI equivalent**: `aom inspect <sid> --host web1 --task "Install nginx"` flags select the level; `aom inspect <sid> --debug` opens the run-level verbose log.
  - **Why this is better than a single global `--verbose` flag**: users think in terms of "I want to see why this host failed", not "I want verbose data". Per-level buttons map the intent to the action.


### Q14.1 — Simplification options (re-thinking)
- User feedback: "do you have other ideas? i would like to keep it simple and not add too many additional buttons"
- Three alternatives to the 3-button approach:

  **Alt 1: Single `V` keybind in the Detail pane, context-sensitive.**
  - When a host is selected: `V` opens verbose tabs for that (play, task, host) only.
  - When a play is selected: `V` opens verbose log for the play.
  - When a run is selected: `V` opens verbose log for the run.
  - One keybind, context-sensitive. Most minimal — no new buttons in the UI, just one new keypress. Discoverability is the trade-off (needs a help line in the TUI footer).

  **Alt 2: One `?` / `D` "Debug" overlay that opens a full-screen modal.**
  - Modal shows all available verbose data: tabs at top for `Hosts`, `Plays`, `Run Log`, `Connection`, `Plugin Load`, etc. User picks what they want.
  - Single entry point. Centralized. More work to build (one big modal vs. three small views) but cleaner UX.

  **Alt 3: Drill-in via the existing `Enter` key.**
  - When a task or host is selected in the Detail pane, `Enter` already drills in. We extend `Enter`'s behavior: if the user presses `Enter` on a `failed` task, the Detail pane splits to show verbose + summary.
  - No new keybinds at all. Verbose is "discovered" through the natural drill-in flow. Trade-off: only works for `failed` tasks; `ok` / `changed` tasks still require explicit verbose access.


### Q14.1 final — Alt 1 (`V` key, context-sensitive)
- Captured: User picked **Alt 1** — single `V` keybind in the inspect TUI, context-sensitive. One tabbed view reused at three levels.
- Implementation:
  - Single widget: `VerboseView` (in `tui/screens/inspect.py` or new `tui/widgets/verbose_view.py`). Tabs: `Stdout`, `Stderr`, `Module Args`, `Diff`, `Raw PTY` (matching the §5 design).
  - Keybind: `V` (capital V; lowercase `v` is unbound). Help footer: `V: verbose debug`.
  - Context:
    - Host focused: `V` opens `VerboseView` filtered to (play, task, host).
    - Play focused: `V` opens `VerboseView` filtered to play; tabs become `Run Log`, `Connection`, `Plugin Load`, `Errors`.
    - Run focused: `V` opens `VerboseView` filtered to run; same tabs.
  - Fallback: if `--capture-verbose` was off, the view opens with a centered message: `"(verbose data not captured for this run — re-run with --capture-verbose to enable)"`. Keybind still works (no-op with helpful message).
- CLI equivalent: keep `aom inspect <sid> --debug` as the run-level flag; no per-host/per-play flags (use `--host` and `--play` filters as before).
- Documentation: README + `aom inspect --help` mention `V` and the `--capture-verbose` flag.


### Q15 — Live compact log: verbose capture indicator
- Asked: A (no hint), B (status-bar indicator), C (one-time startup line), D (other)? Recommendation: C.
- Captured: User picked **B — status-bar indicator**. When `--capture-verbose` is on, the existing `● REC` (recording) indicator in the compact status bar becomes `● REC+VC`. Always visible, no log spam, no startup line.
- Implementation: `compact/renderer.py` gains a `recording_mode: Literal["off", "on", "on+verbose"]` field. The status bar rendering checks it and appends `+VC` when verbose is active. TUI's status bar widget gets the same change.
- Tooltip: hovering / `:help` in the TUI shows `VC = verbose capture enabled; secrets redacted`. CLI `--help` mentions the indicator.
- Discoverability: users always know if capture is on without reading CLI banners.


### Q16 — Redacted field display
- Asked: A (dim grey, key name), B (red, no key name), C (invisible), D (other)? Recommendation: A.
- Captured: User picked **A — dim grey `[REDACTED:password]`, key name preserved**. Color: `grey50` (in Rich terms).
- Implementation: `tui/widgets/verbose_view.py` and `inspect/text.py` apply `Text(repr, style="grey50")` to all `[REDACTED:*]` strings. The Rich renderer handles this consistently across TUI and CLI text output.
- Sub-decision: when the user has `--no-redact` on, the value is the actual secret, not the placeholder. To make this clearly different visually, the raw value is rendered in `red` (alarm) so the user knows "this is the actual secret, you asked for it unredacted". Default state never shows red.
- Re-confirmation: matches AWX display style for redacted fields.


### Q17 — Config file structure
- Asked: A (single file, sections), B (split per concern), C (split per scope), D (split for secrets)? Recommendation: A.
- Captured: User picked **A — single `aom_config.yaml` with all sections**. Top-level keys: `capture`, `redaction`, `live`, `inspect`, `tui`, etc.
- This matches the existing `core/config.py` model structure (StatusBarConfig, RedactionConfig, WarningsConfig, etc.). One file, easy to find related settings, easy to layer-merge.
- The redaction deny-list is in the `redaction` section. Future enhancement: separate `secrets_config.yaml` with `chmod 600` for deny-list. Not v1.


---

# DOCUMENTATION CHECKLIST (added per user question 2026-06-30)

The user asked: "did you also already checked for what documentation files need to be adjusted with the new features?"

Audit complete. Here's the comprehensive doc-update checklist for the new feature.

## Top-level .md files (6 to update)

### SPECIFICATION.md (3262 lines) — heaviest changes

| Section | Change needed |
|---|---|
| §1.3 Key Differences | Update "Single config.yaml + CLI args" → "Multi-layer aom_config.yaml + CLI args" |
| §3.2 CLI Flags | Add 7 new flags: `--capture-verbose`, `--capture-setup`, `--no-redact`, `--no-failed-hint`, `--hide-warnings`, `--hide-deprecations`, `--config`. Update `--verbose` description. |
| §3.3 Inspect Subcommand | Add `--debug` flag. Example: `aom inspect <sid> --debug`. |
| §5.6 PTY Stream Parsing | Add `aom_verbose_line` synthetic event type. Document stderr line classification for `Display.vvvv()` lines. |
| §5.9 Password/Secret Redaction | **Major rewrite**: Add `--no-redact` flag. Change redaction format from `********` to `[REDACTED:key]`. Add hard-coded deny-list. Add user-configurable deny-list. Document redaction-at-capture-time. Add `--no-redact` warning message. |
| **§5.10 (NEW)** | **Create new section**: "Verbose Capture & Inspect". Mirror the structure of this design doc. |
| §6.1 Data Models | Add `VerbosePayload` dataclass. Add `HostRunState.verbose: VerbosePayload \| None` field. Add `aom_verbose_line` event type. |
| §6.3 Session Recording | Document optional `hosts.<host>.verbose` block. Document `aom_verbose_line` synthetic event. Update `RECORD_EVENT_KEEP_FIELDS` to include `verbose`. |
| §7.4 Status Bar | Add `● REC+VC` indicator when verbose capture is active. |
| §8 Configuration | **Complete rewrite**: Multi-layer config (5 layers + CLI). Rename to `aom_config.yaml`. New sections: `capture`, `live`, `inspect`. Update `redaction` section. Add `LiveConfig`, `CaptureConfig`, `InspectConfig` sub-models. Document auto-migration from old `config.yaml`. |
| §9 Session Inspection | Add `--debug` flag. Add `V` keybind documentation. Add `VerboseView` tabbed widget. Add fallback message for sessions without capture. |
| §10 Keybindings | Add `V` keybind for verbose debug (context-sensitive). |
| §14.5 Logging | Add `--capture-verbose` interaction with logging. Document config file loading log messages. |
| §15 Implementation Plan | Add Phase 7: "Verbose Capture & Inspect". |
| Document History | Add v2.0 entry for this feature. |

**Estimated: ~400-600 new/rewritten lines**

### ARCHITECTURE.md (562 lines)

| Section | Change needed |
|---|---|
| §2 Layer Map | Add `config_layer` to core/ list. Add verbose capture modules. |
| §3 Module Map | Add `core/config_layer.py`. Update inspect/ tree. |
| §5 Data Flow | Update inspect data flow to show verbose data path. Add `aom_verbose_line` synthetic event to PTY parser flow. Show multi-layer config loading in startup flow. |
| §6 Key Architectural Decisions | Add new decisions: capture-at-source, multi-layer config, opt-in capture, no size caps, no schema version bump. |
| §7 Gaps | Add gap for config layer (compact mode doesn't use config). Add gap for verbose capture (not yet implemented). |

**Estimated: ~100-150 new/rewritten lines**

### README.md (243 lines)

| Section | Change needed |
|---|---|
| Flags table | Add 7 new flags. Update `--verbose` description. |
| Inspect past runs | Add `aom inspect <sid> --debug` example. |
| File locations | Update config path to `~/.config/aom/aom_config.yaml`. Add `/etc/aom/aom_config.yaml` and `./.aom_config.yaml`. |
| **NEW: Configuration section** | Document multi-layer config hierarchy, precedence, `AOM_CONFIG` env var. |
| **NEW: Verbose Capture section** | Brief paragraph on `--capture-verbose` flag and inspect TUI's `V` keybind. |

**Estimated: ~80-120 new/rewritten lines**

### AGENTS.md (127 lines)

| Section | Change needed |
|---|---|
| Notepads Structure table | Add `verbosity-research/learnings.md` entry. |
| Key Files table | Add `core/config_layer.py` reference. |

**Estimated: ~10-15 new lines**

### TEST_SPECIFICATION.md (very large)

| Section | Change needed |
|---|---|
| TC-164 Redaction Always On | Update: `--no-redact` flag now exists. Change test to verify `--no-redact` bypasses redaction with warning. |
| TC-304 Config File XDG Path | Update to `aom_config.yaml`. Add multi-layer path tests. |
| **NEW: Verbose Capture tests** | Add ~15-20 new test cases for all the new flags and behaviors. |
| **NEW: Config layer tests** | Add ~5-10 new test cases for multi-layer config. |

**Estimated: ~200-300 new lines**

### TEST_PLAYBOOKS.md

| Section | Change needed |
|---|---|
| **NEW: Verbose capture playbooks** | `verbose_with_no_log.yml`, `verbose_with_diff.yml`, `verbose_with_setup.yml`, `verbose_multi_host.yml`, `verbose_with_warnings.yml`. |
| Coverage Matrix | Add rows for verbose capture scenarios. |

**Estimated: ~100-150 new lines**

## Source code docstrings (4 files to update)

| File | Lines | Change needed |
|---|---|---|
| `src/ansible_aom/cli.py` | 180-259 | Add 7 new flags to help text. Update config path to `aom_config.yaml`. Add `--config` and `AOM_CONFIG` env var. |
| `src/ansible_aom/inspect/cli.py` | 1-176 | Add `--debug` flag (already exists per audit) and update module docstring. |
| `src/ansible_aom/core/config.py` | 1-118 | **Complete rewrite** for multi-layer config. Add `CaptureConfig`, `LiveConfig`, `InspectConfig` sub-models. Document multi-layer precedence. Document auto-migration. |
| `src/ansible_aom/core/redaction.py` | 1-10 | Update docstring: add `--no-redact` flag, change format to `[REDACTED:key]`, add hard-coded deny-list, document capture-time redaction. |

**Estimated: ~150-250 new/rewritten lines**

## Missing docs to consider creating

| Doc | Priority | Notes |
|---|---|---|
| **CHANGELOG.md** | Medium | No changelog exists in the repo. Recommended to add a v2.0 entry for this feature. |
| **ROADMAP.md** | Low | No roadmap exists. Not blocking this feature. |

## Per-feature doc mapping (compact view)

| Feature | SPEC | ARCH | README | AGENTS | TEST_SPEC | TEST_PB | cli.py | core/ |
|---|---|---|---|---|---|---|---|---|
| `--capture-verbose` | §3.2, §5.10 | §5 | Flags | — | New TC | New PB | Help | — |
| `--capture-setup` | §3.2, §5.10 | — | Flags | — | New TC | New PB | Help | — |
| `--no-redact` | §3.2, §5.9, §5.10 | §6 | Flags | — | TC-164 | — | Help | redaction.py |
| `--no-failed-hint` | §3.2, §5.10 | — | Flags | — | New TC | — | Help | — |
| `--hide-warnings` | §3.2, §5.10 | — | Flags | — | New TC | — | Help | — |
| `--hide-deprecations` | §3.2, §5.10 | — | Flags | — | New TC | — | Help | — |
| `--config` | §3.2, §8 | §3, §6 | Config | — | New TC | — | Help | config.py |
| `AOM_CONFIG` env | §8 | §3 | Config | — | New TC | — | Help | config.py |
| `aom_config.yaml` | §8 | §3, §6 | Files | — | TC-304 | — | Files | config.py |
| `aom inspect --debug` | §3.3, §9 | — | Inspect | — | New TC | — | — | — |
| `V` keybind | §9, §10 | §5 | — | — | New TC | — | — | — |
| `REC+VC` indicator | §7.4 | — | Status | — | New TC | — | — | — |
| `aom_verbose_line` | §5.6, §5.10 | §5 | — | — | New TC | — | — | — |
| `events.jsonl` verbose block | §5.10, §6.3 | §9 | — | — | New TC | — | — | — |
| Config migration | §8 | §6 | Config | — | New TC | — | — | config.py |

## Total scope

- **12 files to touch** (6 top-level .md + 4 source docstrings + 1 .pyproject + 1 CHANGELOG to create).
- **~1250-1900 lines** of new/rewritten documentation.

## Suggested doc-update order

1. **SPECIFICATION.md** — start with §5.10 (new section), then update §3.2, §5.9, §8, §9, §10, §15, and Document History. This is the authoritative spec.
2. **Source code docstrings** — `core/config.py` first (since it's the largest rewrite), then `cli.py`, then `core/redaction.py`, then `inspect/cli.py`.
3. **ARCHITECTURE.md** — §5 (data flow), §3 (module map), §6 (decisions), §2 (layer map), §7 (gaps).
4. **README.md** — Flags table, Configuration section, Verbose Capture section, File locations, Inspect section.
5. **TEST_SPECIFICATION.md** — Update TC-164 and TC-304. Add new test cases.
6. **TEST_PLAYBOOKS.md** — Add new playbooks + coverage matrix rows.
7. **AGENTS.md** — Notepads and Key Files tables.
8. **Create CHANGELOG.md** — single v2.0 entry.

---

# QC REVIEW (grumpi-qa) — 2026-06-30

> Brutally grumpy, technically fair review of the brainstorm/design above.
> Reviewer focus: the design document itself, with cross-checks against the
> code it claims to anchor against. Findings are evidence-based; if the
> code wasn't reachable, the finding is marked as suspicion.

## 1. Executive roast summary

The brainstorm is ambitious, internally consistent in its narrative, and
empirically anchored — that is the nicest thing I am contractually
permitted to say. Underneath the polish it has a few structural sins
that will hurt the team the moment implementation begins: a single
megafile trying to be spec, Q&A log, and roadmap at the same time; a
`Locked-in` header that lies about its own confidence level; a
"no size caps" decision that quietly transfers a DoS vector from the
coder to the operator; a redaction policy that is correct only when the
user behaves; and an "Open flags" section that has been empty for two
sessions and is now claiming victory. None of these are show-stoppers.
All of them will be more expensive to fix in code than they are to fix
in markdown — so fix them in markdown first.

The biggest non-obvious risk: the doc treats `events.jsonl` as a
durable, append-only, version-free log. The moment the inspect TUI
starts reading `hosts.<host>.verbose` blocks in real time, the absence
of a schema version field becomes a maintenance landmine, not a
simplicity win. The "no `_schema_version` bump" decision (Q9=B) is a
clever shortcut that ages like milk.

## 2. Quality scorecard

| Category | Score | Verdict | Why |
|---|---:|---|---|
| Architecture (design) | 6 | Wobbly but salvageable | Sound refactor strategy (multi-layer config, unified JSONL, capture-time redaction) undermined by skipping schema versioning and a redaction model that only works when secrets are recognised substrings. |
| Internal consistency | 5 | Drifts | The "Locked-in" section and the "Question Backlog" contradict each other in at least four places; the recap claims "all 17 resolved" while Q3, Q4, Q6, Q7, Q9, Q10, Q11, Q12, Q14, Q15, Q16, Q17 are all still listed as `[ ]` in the backlog. |
| Security thinking | 4 | Under-cooked | Capture-time redaction is the right call, but the deny-list is naive (substring match on `password`/`secret`/`token` is a known-fail pattern — see the 2017 AWS SDK CVE and AWX #13613 already cited). The `--no-redact` flag with a printed warning is theatre, not a control. |
| Test strategy | 6 | Reasonable shape, light on edge cases | Unit + integration + TUI snapshot + fixtures plan is complete. Missing: adversarial fixture for redaction bypass (nested dicts, env-var values, base64-encoded secrets), concurrent-write test for `events.jsonl`, replay of session that straddles the schema boundary. |
| Documentation hygiene | 4 | Voluminous but leaky | The "Documentation Checklist" section is itself a 100-line TODO. The doc claims to be a design doc and a roadmap and a research report. Pick one. |
| Risk handling | 5 | Honest about existence, weak about mitigation | "Risks" section lists 6 risks. 2 of them (disk usage, redaction bypass) are mitigated by "document it" or "user can opt out". That is not mitigation; that is a shrug. |
| Backward compatibility | 5 | "Tolerate absence" is not a plan | The whole story rests on every reader "ignoring unknown fields". That works for orjson. It does NOT work for replay drivers, jq pipelines, or any third-party tool that people will inevitably write against `events.jsonl`. |
| Open-question hygiene | 3 | The doc claims victory while showing 21 open items | "All 17 resolved" in §17 contradicts the question backlog that has 21 unchecked boxes as of the last edit. Pick one. |

## 3. Findings table

| ID | Severity | Category | Location | Finding | Evidence | Why this is bad | Recommended fix | Confidence | Effort |
|---|---|---|---|---|---|---|---|---|---|
| QC-001 | High | Internal consistency | Line 26 vs. Lines 53–110 | The "Locked-in design" header says 17 decisions are resolved, but the Question Backlog (lines 51–110) still has **21 questions unchecked** as of the current file. The recap at line 611 repeats the "all resolved" claim. | Grep for `- \[ \]` in lines 51–110: Q3, Q4, Q6, Q7, Q9, Q10, Q11, Q12, Q14, Q15, Q16, Q17, Q18, Q19, Q20, Q21, Q22, Q23, Q24, Q26, Q27, Q28, Q29, Q30, Q31, Q32, Q33, Q34, Q35, Q36, Q37, Q38, Q39, Q40, Q41, Q42, Q43 — i.e. most of the backlog. | Anyone implementing off this doc will reach a question, find no answer, and either guess (bad) or block (worse). The "no open sign-off items" line (490) and "No open sign-off items" (line 611) are demonstrably false. | Either (a) physically delete every `[ ]` for which the locked-in header is the answer, leaving a pointer like "[resolved → §6 line 287]", or (b) rename the locked-in header to "Provisional decisions" and mark which questions are still unverified. Do not let the two views disagree. | High | Small |
| QC-002 | Critical | Security | Line 287–315 (Redaction policy) | Deny-list is case-insensitive substring match on `password`, `passwd`, `secret`, `token`, `api_key`, `private_key`, `ssh_pass`, `vault_password`. | §6, lines 287–315. The list and the substitution rule are spelled out explicitly. | Substring `token` will match `tokenized_data`, `tokens`, `tokener`, `token_endpoint`, and the canonical `auth_token`. Substring `secret` will match `secretary`, `secrets_yaml_path`, and the entire class of base64-encoded JWTs living under keys like `data` or `payload`. This is the same class of bug as Ansible's CVE-2023-5115 (no_log leak via `secret` substring) — the team already cited AWX #13613 as the motivating case. | (a) Use Ansible's own `is_invocable` deny-list as a starting point: exact match against a vetted set + per-pattern regex. (b) Reject recursion into string values — redact by key, not by value substring. (c) For env-var values: only redact when the env var name matches, not the value. (d) Add a red-team test fixture with `secretary`, `auth_token`, `bearer_xyz`, base64 JWTs, and confirm they are NOT redacted (because they aren't secrets). | High | Medium |
| QC-003 | High | Security / UX | Line 311 (safety valve) | `--no-redact` "prints a warning" and proceeds. | §6 line 311. | The "safety valve" is a printed warning, which is not a control. A user who is debugging an unrelated issue, sees the option, and types `--no-redact` to silence a false-positive redaction, will write a secrets file to disk with no mechanical prevention. AWX solves this with an admin gate; ARA solves it with no flag at all. | Either (a) require `--no-redact` to be paired with `--no-record` and refuse to combine it with `--capture-verbose` against a non-ephemeral session dir, or (b) when `--no-redact` is active, refuse to write to a session dir that is not in `~/.local/state/aom/sessions/`. At minimum, log the unredacted payload to a separate `secrets-raw.jsonl` with a hard-coded warning, so accidental disk write is loud. | Medium | Small |
| QC-004 | High | Architecture | §5.10 design (Storage) | Schema gains one optional `hosts.<host>.verbose` block + one new event type `aom_verbose_line`. No `_schema_version` field. Replay/prune/rerun/jq-pipeline readers are assumed to "tolerate absence" of unknown fields. | Lines 192–229, 327–331, 736–737. | "Tolerate absence" is true for orjson. It is not true for: (i) users who `jq` `events.jsonl` and assume the schema is documented somewhere, (ii) the upcoming `aom replay` driver if it ever has to skip a malformed line, (iii) third-party tools (Django, Elasticsearch, Vector) that do JSON schema validation. The "lighter touch" framing hides the long-tail cost. | Add a `meta.json` `_schema_version: 2` field anyway. Cost: 1 line in meta writer, 1 line in meta reader. Payoff: future `aom inspect` code can decide what to do with sessions that lack `verbose` blocks based on the version, not on the absence heuristic. | High | Small |
| QC-005 | High | Architecture | §9 (Size & truncation), Q10=B | "No size caps. Trust the user. AOM does not impose any truncation or rotation." | Line 335, line 742–744. | "Trust the user" in a tool that runs in CI, on developer laptops, and inside automation is a polite way to write a DoS bug. One run of `setup` against a moderately noisy 200-host inventory can write 20–50 MB of `events.jsonl`. Multiply by session rotation. Multiply by `aom rerun`. The team has not measured this. The plan acknowledges 20+ MB is "acceptable" but never establishes what happens after 100 sessions. | Add a soft cap: `--max-session-size 100MB` (default) with a hard refusal to exceed. Keep the file streaming-friendly by truncating the `hosts.<host>.verbose` block with a `[TRUNCATED at <bytes>]` marker if it exceeds per-host quota. The plan already has `exclude_modules` — promote it to a quota system, not a single-module toggle. | High | Medium |
| QC-006 | Medium | Architecture | §11 (Multi-layer config) | `AOM_CONFIG` env var is described as "takes precedence over the above paths but NOT over `--config`". | Lines 357–358, 542–545. | The precedence list puts env var below CLI flag. Conventionally, CLI flags are *syntactic* (set value), env vars are *declarative* (set policy), and config files are *defaults*. The order "config files < env < CLI" is standard. The order "config files < env < CLI < config-via-CLI" is unusual and needs justification. | Either (a) state the rationale (CLI flag is "this is a one-off, override everything"), or (b) invert: `--config` is just a way to point AOM at a config file, and the normal precedence still applies. Pick one and document it. | High | Trivial |
| QC-007 | Medium | Architecture | §6 (Precedence order, lines 304–309) | Redaction precedence: (1) `no_log: true` first, (2) hard-coded deny-list, (3) user-configured deny-list. | Lines 304–309. | (1) is not actually a precedence rule — `no_log: true` replaces the payload before AOM sees it, so it's not a layer AOM applies, it's a contract. Calling it "precedence 1" invites confusion. (2) and (3) are the actual layers. (3) is also documented to be additive to (2) by union, but the precedence section is silent on the order in which (2) and (3) are evaluated. | Rename the section "Redaction layers" instead of "Precedence order". Clarify: layer 1 (hard-coded) runs first; layer 2 (user-configured) runs second and is additive. `no_log: true` is an upstream contract, not a layer. | High | Trivial |
| QC-008 | Medium | Design | §5 (Inspect view) | TUI's `V` keybind is described as "context-sensitive" and resolves host → play → run. | Lines 836–863. | The doc doesn't say how the user knows which context they're in. The current Detail pane (lines 706 in §E) is a 3-pane Runs/Tasks/Detail. Focus changes are implicit (a click? arrow keys? tab?). A "context-sensitive" keybind that fires on the wrong context will frustrate users faster than no keybind. | Add a 1-line focus indicator to the TUI footer: `focus: host (web1 / Install nginx)`. The `V` keybind should also have a one-line confirmation in the footer: `V: verbose for web1/Install nginx`. The fallback message at line 862 is good; the active context message is missing. | Medium | Small |
| QC-009 | Medium | Design | §13 (Test plan) | Test plan covers unit, integration, TUI snapshot, fixtures. No mention of: concurrent `events.jsonl` appends, partial-write recovery, replay of session that straddles schema boundary, fuzz testing of the `aom_verbose_line` classifier. | Lines 433–453. | The PTY parser (line 145) feeds the `events.jsonl` writer. If the writer is interrupted (SIGKILL, OOM, disk full) between line-flush and meta.json write, replay will see a partial session. The plan has no test for this. The classifier at line 815 ("Loading ", "Attempting ", etc.) is a regex-prefix match — exactly the class of bug that a small fuzzer finds in 30 seconds. | Add tests: (a) crash-recovery: kill -9 AOM mid-write, restart, verify replay handles missing `meta.json` gracefully. (b) Fuzz: feed 10k random stderr lines through the `aom_verbose_line` classifier and assert no false positives for known error patterns (`ERROR!`, `Traceback`, `FATAL`). | High | Small |
| QC-010 | Medium | Design | §5.6 (Synthetic event naming) | Doc proposes `aom_verbose_line` and rejects `v2_verbose_line` "for clarity" (it is AOM-emitted, not ansible-emitted). | Line 807. | The doc says "name: `aom_verbose_line` is the proposed event name". But ansible's actual `v2_*` event namespace is owned by ansible-core. The reasoning is correct (AOM-emitted ≠ ansible-emitted) but the doc doesn't make the rule explicit: "All AOM-emitted events use the `aom_*` prefix to avoid collisions with future ansible-core events." That rule needs to be documented so future contributors know not to invent `v2_` events. | Add a one-line policy at the top of the §5.6 section: "AOM-emitted events use the `aom_` prefix. The `v2_` prefix is reserved for ansible-core's `v2_*` event family." | High | Trivial |
| QC-011 | Medium | Documentation | Line 48–110 (Question Backlog) | The backlog is 43 questions, 21+ still open, and serves as both "what we're working on" and "what was decided". | Lines 48–110. | A reader can't tell which `[ ]` means "still being researched" vs "decided but not yet closed out". The two states look identical. | Use two checkboxes per question: `- [ ]` for unresolved, `- [x]` for resolved (with `→ §N line M` for the answer location). Or split the section into "Resolved" and "Pending". | High | Small |
| QC-012 | Medium | Documentation | §E (Anchor research notes, line 702) | Anchors claim `core/redaction.py:280-283` for Layer 4. Actual file is 285 lines. | Line 285 of `core/redaction.py` confirms. Line 704 of the doc says `280-283`. | Doc anchors will rot as code moves. Four-line discrepancy in a 285-line file is small but is a precedent for stale anchors. | Add a verification step: every anchor should be re-checked before this design doc is converted to spec. Use `Read` on the cited lines and confirm the line numbers in the spec match. | High | Small |
| QC-013 | Medium | Documentation | Line 522–528 (sub-Q4.1) | The sub-question "do we already have a configuration file listener?" includes a paragraph-long answer in the body of a Q&A log entry. | Lines 522–528. | The Q&A log is meant to be terse. Inline architecture audits belong in a separate research note (or in ARCHITECTURE.md). Mixing them dilutes the signal. | Move the sub-Q4.1 audit content to a research note at `docs/research/config-audit-2026-06-29.md` and replace the inline paragraph with a 1-line summary + link. | Medium | Small |
| QC-014 | Medium | Risk handling | §17 (Risks) line 482–488 | Six risks listed. Mitigations: "document it", "user can opt out", "auto-migrate". | Lines 482–488. | Documenting a risk is not mitigating it. "User can opt out" is a transfer of blame. The `aom_verbose_line` fixture gap is a "new fixtures" handwave. | For each risk, write a one-sentence "What changes in v2 if this risk materialises?" E.g. for disk usage: "v2 adds `--max-session-size` and per-host quota with `[TRUNCATED]` markers." For redaction bypass: "v2 adds regex-based key match and value redaction via `re.search`." | High | Small |
| QC-015 | Low | Documentation | Line 1027 | "Create CHANGELOG.md" is a TODO inside a 1028-line design doc. | Line 1027. | The doc references a file that doesn't exist (CHANGELOG.md), the file is recommended with priority "Medium", and there is no follow-up owner. The doc is also a TODO list with no owner field. | Add an "Owner" column to the Documentation Checklist (line 894–1027) and the test plan (line 433–453). Each row needs a person, not a "Who writes it?" question. | High | Trivial |
| QC-016 | Low | Documentation | Line 1 | Document is 1028 lines and tries to be research report, design doc, Q&A log, implementation plan, and doc checklist simultaneously. | `wc -l` confirms 1028 lines. | Files this large don't get read end-to-end by future contributors. The signal-to-noise ratio degrades past ~500 lines. | Split into 4 files: `2026-06-29-research.md` (anchor research), `2026-06-29-design.md` (the implementation plan §1-§17), `2026-06-29-qa.md` (Q&A log), `2026-06-29-doc-checklist.md` (lines 894–1027). Reference them from a one-line index at the top of each. | High | Medium |
| QC-017 | Low | Documentation | Line 14 | "The bootstrap comment `cli.py:200` already warns '-v is reserved for ansible-playbook. AOM's debug flag is --verbose.'" | Line 14. | Verified: `cli.py:200` is correctly cited, but the line range should be `200-203` per line 708 in §E. Doc uses both `cli.py:200` (line 14) and `cli.py:200-203` (line 708). | Pick one citation style and use it everywhere. | High | Trivial |
| QC-018 | Low | Architecture | §3 (Storage design) line 213–225 | `verbose` block schema lists 8 fields: `msg, stdout, stderr, stdout_lines, stderr_lines, invocation, diff, results, warnings, deprecations, _ansible_no_log`. | Lines 213–225. | The schema is the union of all JSONL fields, which means the `verbose` block is functionally a copy of `result._result.copy()`. The "optional verbose" framing is therefore a renamed "store the full result", which has a privacy cost the doc has not accounted for: things in `result._result` that aren't in the doc's list (e.g., `start`, `end`, `delta`, `changed`, `failed`, `skipped`, `unreachable`, `duration`, `action`) are now also persisted. | Either (a) explicitly enumerate the schema and forbid new fields, with a validator that drops unknowns, or (b) rename the block to `verbose_full` to signal "everything ansible gave us, minus redaction". The current wording implies a curated set, which is misleading. | Medium | Small |
| QC-019 | Low | Design | §15 (Rollout) line 469 | "Ship behind `--capture-verbose` for one minor release, then potentially flip default to ON in a later release if disk usage proves acceptable." | Line 469. | "Potentially" is not a rollout plan. The default-flip decision needs a measurement plan: which metric (disk, latency, error rate), which threshold, and who decides. | Add: "Default-flip requires: (a) 30 days of production data showing median session size < 5MB and 95th percentile < 20MB; (b) < 0.1% `aom_verbose_line` classifier false-positive rate on real stderr; (c) redaction bypass test suite with 0 failures. Owner: <name>. Decision date: <date>." | High | Trivial |
| QC-020 | Low | Documentation | Line 4 | "Running synthesis, updated as answers come in" | Line 4. | A "running synthesis" is a journal, not a design doc. A design doc should have a frozen decision log with dates. | Change the title to "Decision Log (last updated 2026-06-30)". Every locked-in decision gets a `✅` and a date. Every pending decision stays `[ ]` with the reason for pending. | High | Trivial |

## 4. Performance and scalability concerns

1. **Multi-layer config load at startup**: the doc claims "~50ms to startup" (line 487) with a `~/.cache/aom/` mtime cache. No benchmarks. No plan to measure. The compact mode startup is on the hot path (every CI run). 50ms × 1000 CI jobs/day = 50s of CI time/day. Either prove it's < 10ms with a benchmark, or pre-compile to a single `.json` file on first run and check mtime of the source YAMLs only.
2. **`aom_verbose_line` classifier runs on every stderr line**: 97 lines at -vvvvv, 0 at -v. Linear scan with a small set of prefix strings is fine in practice, but the doc doesn't bound it. A pathological playbook that emits 10k lines/sec through `-vvvvv` (possible with very chatty callbacks) could dominate PTY parsing. Add a line-budget: if the classifier has already matched N lines/sec, demote remaining lines to `stderr.log` only.
3. **No measurement of `events.jsonl` write throughput**: pexpect → parser → event-store. Each JSONL line triggers a `orjson.dumps` and a `flush()`. The doc doesn't say whether the writer is line-buffered, block-buffered, or memory-mapped. For 1000 events/sec (a fast playbook with debug module), this matters. Worth a measurement.
4. **`jsonl` in Q1=B (unified file) is a sequential append**: fine for one writer. The doc says "the live `RunState` always populates `HostRunState.msg, .stdout, .stderr, .invocation, .diff, .results` regardless of whether we'll persist them" — this means the in-memory state is always verbose, and the write is the only thing that's conditional. Confirm that the in-memory cost is acceptable for a 1000-task playbook (each task × host carries ~5KB of strings; 1000 × 5 hosts × 5KB = 25MB resident).

## 5. Security and reliability concerns

1. **Redaction bypass via env-var values (QC-002)**: substring `token` matches `auth_token` (good), but also `tokenized_data` (false positive) and any value containing the substring (false negative risk if value-pattern redaction is added later). The 2017 AWS SDK incident is the canonical lesson: key-substring redaction misses `secret_access_key` because `access_key` is not in the deny-list.
2. **`--no-redact` is a control, not a warning (QC-003)**: the doc acknowledges this is dangerous but treats the warning as mitigation. Production deployments will accidentally trigger this. Refuse the combination with `--capture-verbose` against a non-tmpfs session dir, or require a confirmation prompt.
3. **`Display.vvvv()` lines can include vault prompt text (Q20)**: the doc says "probably yes if redaction is on" — but `aom_verbose_line` events have "no redaction applied" (line 323). This is a leak: a user who runs `-vvvv` with `--capture-verbose` and is prompted for a vault password will see the prompt text in `events.jsonl`. Either redact the prompt patterns specifically, or document this leak loudly.
4. **`exclude_modules` is the only "size" knob (Q10=B)**: a malicious or buggy playbook can emit a module with arbitrary output. Without a per-host byte cap, a 200-host run with one bad task can DoS the user's disk. Add a hard cap.
5. **No schema version (Q9=B) means no integrity check**: a corrupted `events.jsonl` line (truncated, re-encoded, partial write) is silently ignored. Add a checksum per line or a schema version, so replay can detect tampering / corruption.
6. **Config auto-migration moves the old file (line 555)**: `mv config.yaml config.yaml.migrated` is a one-way operation. If the migration logic has a bug, the user loses their config silently. Add a `.bak` copy and verify post-migration.
7. **PTY parser is a state machine that interacts with pexpect (line 317)**: an attacker-controlled playbook can emit escape sequences, ANSI codes, or backspace floods. The doc assumes the existing parser handles this — it should call that out as an explicit assumption, not bury it.

## 6. Testing gaps

1. **No fuzz test for `aom_verbose_line` classifier** (QC-009): a 30-second `hypothesis`-style property test would catch regex prefix collisions.
2. **No redaction bypass fixture**: the doc lists keys like `secretary`, `bearer_xyz`, base64 JWTs as known-similar-but-not-secret. The fixture should assert these are NOT redacted (to prove the deny-list isn't over-broad) AND that real secrets like `password`, `vault_password`, `api_token` ARE redacted.
3. **No crash-recovery test**: kill -9 during write, restart, verify replay. Currently no plan for this.
4. **No large-inventory integration test**: 100+ host playbooks with `--capture-verbose`. The doc acknowledges this is the failure mode for size caps but doesn't test it.
5. **No replay of schema-boundary session**: a session recorded with v1, replayed with v2, and vice versa. Critical for the "no schema version" decision.
6. **No `aom inspect --debug` test for sessions with mixed `aom_verbose_line` and `v2_*` events**: the inspect TUI's `V` keybind at run level filters by `aom_verbose_line` only; if the test doesn't cover both, the filter regression is silent.
7. **No concurrency test**: the doc assumes single-writer. The PTY parser, the live render, and the event-store all touch the same `events.jsonl`. A test that runs a fake playbook that emits events at 1000/sec while another thread reads via `aom inspect` would catch races.
8. **No test for `--no-redact` + `--no-record` interaction**: the doc doesn't say whether `--no-redact` requires `--no-record`. Without a test, the behaviour is implementation-defined.
9. **No end-to-end test for the multi-layer config**: the doc lists 5 layers. A test should load a config with all 5 layers present, set a value at each layer, and assert the precedence. The plan's `test_config_layer.py` (line 439) is named but not specified.

## 7. Maintainability cleanup plan

**Stage 1 — doc hygiene (1 day, before any code is written)**:
- Address QC-001, QC-011, QC-013, QC-015, QC-016, QC-020.
- Split this file into the four files named in QC-016.
- Re-walk the locked-in section and physically close the matching backlog checkboxes.
- Add an "Owner" column to every checklist.

**Stage 2 — redaction hardening (before `--no-redact` ships)**:
- Address QC-002, QC-003.
- Build a redaction-bypass fixture (keys like `secretary`, `tokens`, `auth_token`, base64 JWTs) and prove the deny-list does NOT over-redact.
- Refuse `--no-redact` when session dir is not a tmpfs or `~/.local/state/aom/sessions/`.
- Add redaction to `aom_verbose_line` content for known sensitive prefixes (vault, password, token).

**Stage 3 — schema and size (before `--capture-verbose` ships)**:
- Address QC-004, QC-005, QC-018.
- Add `meta.json:_schema_version: 2` even though Q9=B said no — the cost is one line and the payoff is future-proofing.
- Add `--max-session-size` (default 100MB) and per-host byte quota with `[TRUNCATED]` marker.
- Pin the `verbose` block schema to a closed set with a validator that drops unknowns.

**Stage 4 — observability and ops (with rollout)**:
- Address QC-006, QC-007, QC-008, QC-014, QC-019.
- Add a config-load benchmark to CI; fail if > 10ms.
- Add a `aom --verbose` log line for "config loaded from N layers: <paths>".
- Add a focus indicator to the TUI footer.

**Stage 5 — test coverage (continuous)**:
- Address QC-009 and §6 above.
- Property-based test for the `aom_verbose_line` classifier.
- Crash-recovery test for the event store.
- Schema-boundary replay test.
- Concurrency test for live inspect during a run.

## 8. Final note to the developer

You have done the hard part: the empirical research is real, the
JSONL-vs-verbosity reframe is correct, and the design is internally
coherent enough that I could find a dozen issues without inventing any.
That's a good place to be.

What you have not done is the boring part: closing the open questions
that the doc pretends are closed (QC-001), hardening the redaction
deny-list against the bypass patterns that the same doc cites in
support of doing redaction at all (QC-002), and admitting that "no
size caps" is a polite way to write a DoS bug for your future users
(QC-005). The design doc is at the stage where the right move is to
shrink it, not extend it. Split the file. Close the checkboxes. Add
an owner. Then implement.

The 1500-2000 LOC estimate (line 660) is plausible but probably low
once you add the test coverage this design needs. Budget for it.

— *grumpi-qa, signing off*

