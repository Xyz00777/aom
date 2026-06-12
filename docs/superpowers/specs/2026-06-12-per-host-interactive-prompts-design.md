# Per-host interactive prompts — design

**Date:** 2026-06-12
**Status:** Design approved; pending spec review before planning.
**Related:** `.sisyphus/notepads/plans/interactive-prompts.md` (the IP1–IP5 work that
shipped single-prompt PTY handling), `src/ansible_aom/ansible/runner.py`,
`src/ansible_aom/core/prompts.py`, `src/ansible_aom/ansible/callback/aom_jsonl.py`
(the bundled-plugin precedent).

## Problem

A deployment playbook confirms per host:

```yaml
- name: Confirm deployment
  ansible.builtin.pause:
    prompt: |
      Deploy to {{ inventory_hostname }} ({{ env_domain }})?
      {{ deploy_preview_block | default('') }}
      Press Enter to continue or Ctrl+C to abort
  when: "'production' in group_names"
```

Through `aom` (and through plain `ansible-playbook`) this prompts **once** for the
whole batch: it shows the first host's templated text, and the single Enter releases
every host. The user wants a distinct, host-templated prompt **and** a distinct
answer per host — the prompt differs per host and so does the change being confirmed.

### Root cause (confirmed)

`ansible.plugins.action.pause.ActionModule` sets `BYPASS_HOST_LOOP = True` (verified
against ansible 2.20.5). In a non-`serial` multi-host play, ansible therefore runs the
pause action exactly once for the batch and templates its args against a single host.
AOM observes the child's PTY and forwards exactly what ansible emits; when ansible
emits one prompt, **no downstream cleverness can split it into per-host prompts.** The
fix has to live where the host loop lives — inside ansible — via either `serial: 1`
(re-runs the play per host) or a plugin that does *not* bypass the host loop.

### What already works (verified empirically)

AOM's existing PTY heuristic + runner loop already detect and route **sequential**
per-host prompts correctly. A fake child that emits `prompt(web1)` → host output →
`prompt(web2)`, reading a line after each, produced two `handle_interactive_prompt`
calls with the correct distinct host text and routed each answer to the right read.
So `serial: 1` + plain `ansible.builtin.pause` already yields correct per-host
prompting under AOM today — Phase 1 only locks this in and signposts it.

## Goals

- Per-host prompt **text** and per-host **answer**, regardless of play strategy.
- Keep today's single-prompt PTY handling untouched as the fallback for plain
  `pause` / `vars_prompt` (non-adopters lose nothing).
- The per-host plugin's playbook must also run under plain `ansible-playbook`
  (no `aom`) — CI, teammates, manual runs.

## Non-goals (v1)

- Capturing a typed **value** per host (vars_prompt-style registered variable). The
  control channel is designed to carry one later, but v1 is confirm-only.
- Overriding `ansible.builtin.pause` transparently. Adoption is explicit (a new task
  action) — clearer and opt-in.
- Bridging arbitrary ambient keystrokes outside detected prompt windows (already a
  documented limitation of the IP work; unchanged).

## Phase 1 — the `serial: 1` path (ship fast, no new runtime behavior)

AOM already does the right thing here; Phase 1 verifies, warns, and documents.

### 1.1 End-to-end integration test
A real fixture playbook against `ansible-playbook` (integration tier, needs
`ansible-core`):
- Static inventory with two local hosts (e.g. `web1`/`web2`, both
  `ansible_connection=local`).
- A play with `serial: 1` and an `ansible.builtin.pause` task whose `prompt`
  references `{{ inventory_hostname }}`, plus a trivial follow-up task.
- Driven through `run_playbook` with a `MagicMock` renderer that returns `""`.
- Assert `handle_interactive_prompt` is called **twice**, with each host's distinct
  templated text, and the run exits 0.

### 1.2 Preflight "bypassed prompt" warning
A **pure** core function, unit-testable, no I/O:

```
detect_bypass_host_loop_prompts(playbook_plays, resolved_host_counts) -> list[str]
```

For each play: if it resolves **>1 host**, has no `serial` (or `serial` not `1`/small),
and contains a `pause` (`ansible.builtin.pause`/`pause`) task whose `prompt` references
a host-varying var (`inventory_hostname`, `ansible_host`, …), produce a warning:

> Task 'Confirm deployment' uses a per-host prompt but the play isn't `serial: 1`;
> ansible will prompt once for all N hosts. Use `serial: 1`, or
> `aom.interactive.confirm` for true per-host prompts.

Wired into the runner's preflight stage (beside the existing `pre_result.errors`
loop) via `renderer.add_warning(msg, False)`. Best-effort: the playbook YAML scan is
wrapped so a parse failure never aborts the run. Lives in `core/` (e.g.
`core/prompts.py` or a new `core/preflight_lints.py`); the YAML read is done by the
infrastructure caller and the parsed structure handed to the pure detector.

### 1.3 Docs
- README + SPECIFICATION: a "Per-host prompts" subsection — `serial: 1` for the
  simple sequential case, `aom.interactive.confirm` for parallel / strategy-independent.
- Update `.sisyphus/notepads/plans/interactive-prompts.md` with the multi-host
  finding and the two supported paths.

## Phase 2 — `aom.interactive.confirm` per-host plugin

An action plugin (+ stub module) that **omits** `BYPASS_HOST_LOOP`, so ansible runs it
once per host and templates the prompt against each host's own vars.

### Packaging
Shipped as an **installable ansible collection** (`aom.interactive`; exact FQCN a
release detail) so the action resolves on the ansible path independently of AOM —
satisfying the "must work bare" requirement. The same collection tree also lives in
the AOM repo; when AOM spawns `ansible-playbook` it injects the bundled path
(`ANSIBLE_COLLECTIONS_PATH`) so it resolves under AOM even if the user hasn't
separately installed it. Bare runs require the user to add it to their
`requirements.yml`.

### Control channel (FIFO + control dir, polled)
Mirrors the env-injection pattern of `_callback_env` and reuses the runner's existing
0.5 s poll loop — no sockets, no threads.

1. Before spawn, AOM creates a control dir `…/aom-prompt-<pid>/` and exports
   `AOM_PROMPT_CONTROL_DIR=<dir>`.
2. Per host invocation, the action plugin:
   - reads `AOM_PROMPT_CONTROL_DIR`; if unset → **fallback** (see below);
   - generates a uuid `id`; `os.mkfifo(<dir>/<id>.fifo)`;
   - writes the request atomically: `<id>.json.tmp` → rename → `<dir>/<id>.req`,
     payload `{id, host, prompt, created}` (rename = AOM never reads a partial);
   - opens the FIFO for reading and **blocks** until AOM writes the answer;
   - cleans up its files; returns `{failed: true, msg}` on abort, else
     `{changed: false}` continue.
3. AOM's `_drive` loop, on each TIMEOUT tick (and after newlines), scans the control
   dir for unhandled `*.req` (arrival/mtime order). For each: read JSON, suspend the
   Live panel, call `renderer.handle_interactive_prompt(prompt)` (host-aware — the
   prompt text already names the host), open the FIFO for writing, send the answer +
   newline, mark handled, resume the panel.
4. **Parallel forks:** N hosts drop N `.req` files; AOM presents them one at a time so
   the user answers per host sequentially.
5. **Teardown safety:** in the runner's `finally`, AOM writes an empty answer to any
   outstanding `.req`/FIFO so no worker blocks forever if the run is torn down
   (Ctrl+C, crash). The plugin treats an empty answer as "continue".

### Fallback (bare run, `AOM_PROMPT_CONTROL_DIR` absent)
The plugin reads the controller's stdin like `pause` does (prints the prompt, reads a
line). Clean under `serial: 1`; interleaved under parallel forks — documented as a
known bare-run limitation, the same constraint that motivates running under AOM.

### Semantics
- Empty / Enter / `yes` → continue this host.
- `no` / `abort` / EOF → **fail this host only** (`failed=True`); other hosts proceed.
  This is strictly better than `pause`, where Ctrl+C aborts the whole run.
- v1 returns no value; the request/answer schema reserves room for a future
  `value` field.

### Renderer surface
Reuses the existing `Renderer.handle_interactive_prompt(prompt_text)` (compact:
`display.stop` + `input()` + restart; TUI: `suspend()` + `input()`), so both modes
work with no new renderer protocol method. The host identity travels inside
`prompt_text` (already host-templated). A dedicated host-aware method is a possible
later refinement, not required for v1.

## Architecture fit (ARCHITECTURE.md §7.5)

- **`core/` (pure, unit-tested):** the preflight bypass-prompt detector; the
  request/answer (de)serialization helpers. No I/O.
- **Infrastructure:** control-dir creation + polling + FIFO writes in
  `ansible/runner.py`; env injection beside `_callback_env`; the action plugin in the
  collection tree (it runs inside ansible's process, not AOM's, so it isn't bound by
  the core/infra split — but its pure payload schema is shared with `core/`).
- `core/` must not import from `compact/`/`tui/`/`renderer/` — unchanged; the detector
  and schema take plain data in and return plain data out.

## Testing strategy

- **Unit:** `detect_bypass_host_loop_prompts` across positive/negative cases (serial
  present, single host, non-host-varying prompt, non-pause task, multiple plays);
  request/answer schema round-trip.
- **Integration (Phase 1):** the real `serial: 1` two-host pause playbook (1.1).
- **Integration (Phase 2):** a fake "playbook" that speaks the control protocol —
  writes two `.req` files (two hosts), blocks on its FIFOs, and records the answers it
  received; assert AOM presents both prompts and routes each answer to the right FIFO,
  plus the teardown-empty-answer path. A real-ansible test that loads the bundled
  collection and runs the action plugin per host across two local hosts (no `serial`)
  to prove it fires per host.
- **TDD by spec:** add TC entries to `TEST_SPECIFICATION.md`; failing test first per
  the project's hard rules.

## Open risks

1. **Preflight YAML scan depth.** v1 scans top-level plays in the named playbook only;
   `import_playbook` / included task files are out of scope for the warning (best-effort
   — a missed warning is harmless; a wrong abort is not, so the scan never raises).
2. **FIFO portability.** POSIX-only; acceptable (ansible control nodes are POSIX). The
   fallback path is what runs anywhere.
3. **Collection release/versioning** is new surface for this repo (galaxy.yml, build).
   Bundling the same tree for under-AOM resolution keeps the happy path working before
   a Galaxy release exists.
4. **Stale control dir** from a crashed prior run: AOM uses a per-pid dir and cleans it
   in `finally`; the poller ignores `.req` files it has already handled by id.
