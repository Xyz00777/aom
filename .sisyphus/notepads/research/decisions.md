
## 2026-05-08: Licensing Research for ansible-aom

### Decision: License choice for ansible-aom
- **Conclusion**: ansible-aom can safely use MIT or Apache-2.0 because it communicates with ansible-core at arm's length via subprocess (pexpect/pipes), not via linking or importing.
- **Chosen approach**: Declare as MIT (or Apache-2.0) with `ansible-core` as an optional integration dependency, not a hard dependency.
- **Key precedent**: ansible-navigator (Apache-2.0) and ansible-runner (Apache-2.0) are both official Ansible project tools that wrap/shell-out to ansible-core and are licensed Apache-2.0, NOT GPL.
- **Caution**: If ansible-aom ever imports from ansible-core (e.g., `from ansible import ...`), those specific modules would be GPL-3.0-or-later and the importing code would need to be GPL-compatible. Avoid importing ansible-core at runtime.

### Key References
- ansible-core pyproject.toml: `license = "GPL-3.0-or-later"`
- ansible-navigator: `license = {text = "Apache"}` → Apache-2.0
- ansible-runner: `license = "Apache-2.0"`
- ara: GPL-3.0-or-later (but it uses a callback plugin that runs INSIDE ansible's process)
- FSF GPL FAQ on arm's-length communication: https://www.gnu.org/licenses/gpl-faq.en.html

## 2026-06-29: Verbosity handling in existing Ansible/TUI tools

### Sources reviewed
- ansible-navigator (interactive TUI + artifact replay): https://github.com/ansible/ansible-navigator and docs/faq.md
- AWX Job Detail (verbosity dropdown, Event filter, Host Details dialog): https://docs.ansible.com/projects/awx/en/24.6.1/userguide/jobs.html ; https://github.com/ansible/awx/blob/devel/docs/job_events.md ; issues #6680, #13613, #4221
- ARA Records Ansible (callback-captures-everything, web UI for drill-down): https://github.com/ansible-community/ara ; FOSDEM 2022 slides (archive.fosdem.org/2022/.../5093/export/events/attachments/...)
- ansible-runner OutputEventFilter: https://deepwiki.com/ansible/ansible-runner/8.4-output-processing ; ansible-runner docs (verbosity param, event_handler, suppress_ansible_output, json_mode)
- nix-output-monitor (nom): https://github.com/maralorn/nix-output-monitor
- Generic TUI log patterns: tui-tracing (https://docs.rs/tui-tracing/), tui-logger (https://github.com/gin66/tui-logger ; DeepWiki page on dual-filter)

### Cross-cutting patterns
1. **Capture everything, display selectively.** Dual-tier filtering is the dominant pattern in mature TUI log tools (tui-tracing, tui-logger): a capture filter gates what enters the store, a display filter hides/shows records already captured. Re-tightening the display filter brings verbose events back without loss.
2. **JSONL/event callback is the data backbone.** navigator, AWX, ARA all rely on Ansible's callback hooks (`v2_playbook_on_*`, `v2_runner_on_*`). JSONL is the authoritative structured stream. Human-readable stdout is a side-channel for tooling like ansible-runner's `OutputEventFilter` which embeds base64-encoded events into escape-sequenced stdout for **later decode**.
3. **Whole stdout captured to disk; UI is a lens over it.** ansible-runner writes the full process stdout to `artifact_dir/stdout` (`OutputEventFilter`), AWX persists every event to Postgres (`job_events` table, `MAX_UI_JOB_EVENTS = 4000` truncation hint only). Verbosity does not erase data; it controls what the *callback* emits.
4. **Verbosity is set on the run, not retroactively.** AWX exposes 0..5 in Job Template (verbosity integer). Setting it higher is the only way to get more event richness from the callback (especially `module_args`, debug, and SSH connection details). navigator runs the playbook once and replays from the artifact — you cannot invent more verbose events that weren't captured.
5. **`-vvvv` and above cause operational pain.** AWX docs warn verbosity 5 "will block heavily" and can lock the browser tab; AWX issue #6680 records that ~80% of `job_events` rows come from a handful of chatty tasks at high verbosity. Real tools throttle or filter, never flood.
6. **Drill-down UX: hierarchical tree with lazy detail.** All four tools converge on a play→task→host hierarchy (AWX JobDetail, navigator replay, ARA web UI, job_events.md ASCII diagram in AWX docs). Detail is only fetched/expanded on click. AWX has a separate Host Details dialog with JSON tab, Standard Out tab, Standard Error tab.
7. **Filter chips + event-type dropdown at the top of detail view.** AWX JobDetail has Stdout / Event / Advanced filter dropdowns; failed/unreachable counts badged in the header. ARA web UI offers per-task status filters. navigator has `:filter <regex>` on any content page.
8. **Capture-time vs display-time risk.** AWX issue #13613 demonstrates the danger: secret/env vars leak through `runner_on_failed` *regardless of requested verbosity* if they are stored in `result._result` by the module. Redaction is orthogonal to verbosity display.
9. **nom-style "trees + bottom panel + scrolling log above" is the established live-runner layout.** nom draws a fixed status panel over the streaming log; verbosity is implicit in the parsed log, not a user togglable. Error messages are deliberately re-printed into the status panel so they're findable after the run (issue #177 discussion).

### Implications for ansible-aom
- Keep JSONL as the canonical capture (we already do this).
- Persist *all* events regardless of user-selected verbosity — verbosity is a display-time filter, not a capture filter. Dropping events at capture time is what forces re-runs.
- Separately capture raw PTY stdout/stderr lines that JSONL does not encode (ansible banners, prompts, "PLAY RECAP" pre-text, "to exit, type CTRL-D" lines from `vars_prompt`) so the inspect view can show them verbatim. This mirrors `OutputEventFilter`'s "verbose" path: un-encoded stdout lines become a structured event with `event=verbose`.
- Do NOT default to `-vvv`. If the user wants to inspect module_args or connection details later, they need to know the run actually captured them — surface a visible "captured at -v / -v / -vvv" indicator in the meta line.
- Inspect view layout: play → task → host; each task has expandable sections for `module_args`, `result`, `stdout_lines`, `stderr_lines`, plus a raw PTY log panel. AWX dialog pattern, applied to Textual.
- One UX trap to avoid: AWX's #13613 leak shows verbosity display is not a redaction strategy. If aom ever expands `module_args` in inspect, fields like `password`, `no_log: true` results must be redacted in the renderer (or rely on ansible-core's `no_log` filtering having stripped them at callback time). The project should consider the redactor note in `.sisyphus/notepads/impl-gaps/learnings.md`.
- For "capture everything, filter live" UX inside the TUI: copy tui-tracing/tui-logger's EWIDT pattern — keys to toggle display of ok/changed/skipped/unreachable, with capture always at full granularity.


---

## 2026-06-29: Ansible Verbosity Levels × JSONL Callback Research

### Decision: How AOM should handle verbosity-driven data

**Sources reviewed (citations below)** confirm three layers of truth:

1. **Ansible core** (Display class) gates `<host>`-prefixed verbose lines via
   `_display.v()` / `vv()` / `vvv()` / `vvvv()` / `vvvvv()` / `vvvvvv()`.
   These are written **directly to the parent process's stdout by the
   worker**, bypassing any stdout callback. The JSONL callback **cannot
   see them**.
2. **Default callback** mutates the result dict in `_dump_results` based on
   `self._display.verbosity`:
   - `verbosity < 3` → strips `invocation` and `diff` from result.
   - `verbosity > 2` → forces indented pretty-print.
   - `verbosity > 1` → shows `PLAYBOOK:` banner + task paths.
   - `verbosity > 3` → dumps full CLI args table.
3. **ansible.posix.jsonl callback** is **verbosity-agnostic in its
   emit logic**. It serialises whatever result dict the task executor
   hands it — including `invocation.module_args`, `diff`, `action`,
   `stdout`, `stderr`, `msg`, etc. It does **not** check `self._display.verbosity`
   in any of its event-emit methods. It does add `_event`, `_timestamp`,
   `play.duration.start/end`, `task.duration.start/end` of its own.

### Recommended approach for AOM

- AOM runs ansible-playbook with the user-passed verbosity flag
  (`-v`, `-vv`, `-vvv`, `-vvvv`, `-vvvvv`, `-vvvvvv`).
- The `ansible.posix.jsonl` callback writes one JSON line per callback
  event to stdout; AOM parses those lines as the canonical event stream.
- For "verbose details not shown live, captured for post-run inspect":
  AOM should **always pass `-vvvvvv`** (or at minimum `-vvvv`) to
  ansible-playbook internally — but that conflicts with user-supplied
  verbosity flags.
- The cleanest solution: let user-supplied `-v` flags flow through
  unchanged. JSONL will emit the full result dict regardless. AOM's
  compact view ignores the verbose fields by default; `aom inspect`
  exposes them.
- For SSH connection debug (`-vvvv`+), users must enable that verbosity
  themselves; those messages are written to AOM's stderr stream
  (because `VERBOSE_TO_STDERR=True` default), not stdout. AOM's PTY
  parser already captures stderr, so they are stored in `stderr.log`
  if AOM records that.

### Gotchas / Surprises

- **Invocations (`module_args`) and `diff` are stripped from human output
  at `verbosity < 3`**, but **NOT stripped from JSONL events**. JSONL
  emits the full `result._result` dict minus `_ansible_*` internal keys.
- **`invocation.module_args` may contain secrets** if the task doesn't
  set `no_log: true`. AOM must apply redaction before persisting to
  `events.jsonl` (already on the TODO list per `.sisyphus/impl-gaps/`).
- **The verbose lines from `_display.v/vv/vvv/vvvv/vvvvv/vvvvvv` are NOT
  in JSONL.** They go to the worker process's stdout/stderr directly,
  bypassing all stdout callbacks. AOM can only capture them by reading
  the PTY's raw byte stream and parsing the `<host>` prefix.
- **Connection debug at `-vvvv`** prints to **stderr by default**
  (`VERBOSE_TO_STDERR=True`). At `-vvvvv`/`-vvvvvv` internal Ansible
  plugin debug goes to stdout (some goes to log only).
- **`action` field** in JSONL `hosts[host]` is added by jsonl itself
  (`result_copy['action'] = task.action`) — it's always present
  regardless of verbosity.
- **`_ansible_verbose_always` and `_ansible_verbose_override`** on a
  result can override verbosity-gated display in default callback
  (`_run_is_verbose`). These don't affect JSONL.
- **`-vvvvvv` is real** (max verbosity = 6 = -vvvvvv). Source:
  `lib/ansible/utils/display.py` lines defining `v`, `vv`, `vvv`,
  `vvvv`, `vvvvv`, `vvvvvv` (caplevel 0..5, gated by
  `verbosity > caplevel`).
- **`v2_runner_on_start` (per-host task start)** is only emitted by
  jsonl when strategy is **NOT** `linear`/`debug` (lockstep). For
  linear strategy (default), only `v2_playbook_on_task_start` fires.
  Verbosity does NOT change this.
- **`v2_playbook_on_handler_task_start`**: only emitted in lockstep.
- **`v2_playbook_on_notify`**: the default callback emits this only
  when `verbosity > 1`. JSONL callback **does not override
  `v2_playbook_on_notify`** at all (inherits no-op base).

### Per-verbosity mapping (final)

| Verbosity | Human stdout (default callback)                                                                                 | JSONL events (ansible.posix.jsonl)                                                                                              |
|-----------|----------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| `-v` (1)  | OK/CHANGED shown with full result dump (`_run_is_verbose` true when `verbosity > 0`). `invocation`/`diff` stripped | Same events as below. `_dump_results` not used. **Full `result._result` dict including `invocation` and `diff` is emitted.** |
| `-vv` (2) | Adds `PLAYBOOK:` banner, `task path: …`, NOTIFIED HANDLER messages, full CLI args on failure.                    | Same as `-v`. No verbosity gating in jsonl source.                                                                              |
| `-vvv` (3)| Pretty-printed results (indent=4). Result dump includes `invocation` and `diff`.                                  | Same. (No additional fields emitted — the fields were always in the result dict; only human display stripped them.)            |
| `-vvvv`(4)| Plugin load messages: "Loading callback plugin …".                                                              | Same.                                                                                                                          |
| `-vvvvv`(5)| Internal Ansible plugin debug (rarely used).                                                                    | Same.                                                                                                                          |
| `-vvvvvv`(6)| Maximum debug. Worker-level tracing.                                                                          | Same.                                                                                                                          |

**Key insight for AOM**: JSONL is identical regardless of `-v` level.
The user's `-v` choice affects:
- Human-readable stdout (default callback, not visible to AOM)
- `stderr` debug noise from `-vvvv`+ (captured by AOM's PTY stderr stream)

### Sources

1. ansible.posix jsonl callback source (commit main):
   https://github.com/ansible-collections/ansible.posix/blob/main/plugins/callback/jsonl.py
   - No `self._display.verbosity` checks anywhere. Uses
     `_dump_results` not at all — emits raw `result._result` +
     `on_info` + `action`.
   - Adds `_event`, `_timestamp`, `play.duration.start/end`,
     `task.duration.start/end`.

2. ansible-core default callback:
   https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/callback/default.py
   - `_run_is_verbose(result, verbosity=0)` →
     `(self._display.verbosity > verbosity or _ansible_verbose_always)
      and not _ansible_verbose_override`
   - `_dump_results`: strips `invocation` if `verbosity < 3`,
     strips `diff` if `verbosity < 3`.

3. ansible-core callback base (`__init__.py`):
   https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/callback/__init__.py
   - `_dump_results`: lines 252–254 show the verbosity-based stripping
     of `invocation` and `diff`.

4. ansible-core Display class:
   https://github.com/ansible/ansible/blob/devel/lib/ansible/utils/display.py
   - `v()` caplevel=0, `vv()` caplevel=1, … `vvvvvv()` caplevel=5.
   - `verbose(msg, caplevel)` → `self._verbose_display` only when
     `self.verbosity > caplevel`. Goes to **stderr** when
     `VERBOSE_TO_STDERR` (default True).

5. Official CLI verbosity doc:
   https://docs.ansible.com/projects/ansible/latest/cli/ansible-playbook.html
   "the builtin plugins currently evaluate up to -vvvvvv"

6. Debugging modules doc:
   https://docs.ansible.com/projects/ansible-core/devel/dev_guide/debugging.html
   Confirms `-vvv` shows connection-level details and
   `invocation.module_args` in result dump.

### Recommendation for AOM roadmap

- **No code change needed** to jsonl parser — it already sees the full
  result dict.
- **Reaffirm existing redaction strategy** for `invocation.module_args`
  on tasks lacking `no_log: true`. These appear at every verbosity
  level in JSONL.
- **Document to users**: pass `-vvvv` (or higher) to ansible-playbook
  to get verbose connection debug captured in AOM's stderr stream
  and recorded under `events.jsonl`'s sibling `stderr.log`.
- **Don't** try to suppress verbose lines via JSONL — they aren't
  in JSONL. The user already controls what reaches the terminal via
  `-v` flags.
