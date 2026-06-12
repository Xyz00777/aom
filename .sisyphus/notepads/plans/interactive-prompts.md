# Interactive prompts — diagnosis and plan

The user hit this with:

```yaml
- name: Confirm deployment
  ansible.builtin.pause:
    prompt: "Deploy to {{ inventory_hostname }} ({{ env_domain }})? Press Enter to continue or Ctrl+C to abort"
  when: "'production' in group_names"
```

Through `aom`, nothing displays and Enter doesn't get through.

## Diagnosis (precise)

`runner._drive()` watches the PTY with this pattern list:

```python
patterns = [r"\r?\n", pexpect.EOF, pexpect.TIMEOUT, *_PASSWORD_PATTERNS]
```

`_PASSWORD_PATTERNS` is a fixed list of 7 vault/ssh/become regexes.
`ansible.builtin.pause` emits:

```
[pause]
Deploy to web1.prod (example.com)? Press Enter to continue or Ctrl+C to abort:
```

— a `[pause]` marker, then the prompt text, ending with `:` and **no
trailing newline** (the module is reading from stdin). Three failures
cascade:

1. **The prompt never flushes to the renderer.** pexpect's
   newline-terminated read sits in TIMEOUT forever. The prompt text
   accumulates in `child.before` and is only inspected on the next
   matched pattern — which never comes.
2. **The Rich Live panel may overdraw the prompt** even if it did
   flush, because the panel keeps repainting the bottom rows.
3. **stdin is never bridged.** The user typing into AOM's terminal
   sends bytes to AOM's stdin, which the runner ignores. The child
   reads its own PTY's stdin, which has nobody on the other end.

So: prompt invisible + input goes nowhere.

## Affected interactive surfaces

In rough order of how often they bite users:

| # | Feature | Trigger | Today | Should be |
|---|---------|---------|-------|-----------|
| 1 | `ansible.builtin.pause` with `prompt:` | At task time | Hangs silently | Show prompt, accept Enter (or any text), forward |
| 2 | `vars_prompt:` plain text | At play start | Hangs silently | Show prompt, accept line, forward |
| 3 | `vars_prompt:` with `private: yes` | At play start | Often hangs (depends on prompt text matching a password regex) | Routed through `handle_password_prompt` like vault |
| 4 | `ansible.builtin.pause` with `seconds:` | At task time | Hidden — task disappears off the panel until it returns | Show "pausing 30s…" countdown |
| 5 | `--ask-pass` / `--ask-become-pass` / `--ask-vault-pass` | Before play | Already works (password patterns) | Unchanged |
| 6 | `ansible.builtin.expect` module | Inside playbook | Works (it's the playbook talking to its own subprocess; AOM doesn't see it) | Unchanged |
| 7 | Custom modules with stdin prompts | Anywhere | Hangs silently | Should "just work" via stall detection |

(5) and (6) are already fine. (1)–(4) and (7) are the real targets.

## Architectural options

### A. Pattern-matched suspend (extend the password model)

Add more regexes to `_PASSWORD_PATTERNS` (renamed `_PROMPT_PATTERNS`):

- `^\[pause\]` — the pause module's marker line
- `[Pp]ress [Ee]nter` — common phrasing
- `: $` — generic "field name: " trailing
- `\(yes/no\)\??\s*$` — confirmation prompts

When matched: `_display.stop()` (or `app.suspend()`), `input()` for one
line, `child.sendline(answer)`, resume.

**Pros:** Surgical, mirrors password handling exactly, no new threads.
**Cons:** Arms race — every new module-author prompt phrasing is a
miss. `: $` in particular has false-positive risk (e.g. a `debug:`
task that prints `something:` at end of line).

### B. Stall-detection + passthrough

Augment the runner loop with a `_stall_counter`. On every TIMEOUT
branch, if the child is alive AND `child.before` is non-empty AND no
JSONL event has fired in T seconds (track `_last_event_at`), increment
the counter. After N consecutive stalls (e.g. N=5 → ~2.5s with the
0.5s timeout), call `renderer.handle_interactive_prompt(child.before)`:

1. Suspend the panel.
2. Print the pending pre-match content (the prompt the user can't see).
3. `input()` one line.
4. `child.sendline(answer)`.
5. Resume the panel.

**Pros:** Catches *any* prompt, including custom-module ones. No
pattern maintenance.
**Cons:** False positives — a real long-running task that produces no
output for 2.5s gets misidentified. Tunable but never perfect.

### C. Full stdin bridging

A background thread `os.read(0, ...)` → `child.send(...)`, always.
The user types into their terminal; the bytes flow to the child.
Display the panel for output only.

**Pros:** Truly transparent. Pause, vars_prompt, custom prompts, even
nested `expect`-like flows all "just work".
**Cons:**
- TUI mode breaks: Textual *needs* stdin for its own keys. Would have
  to be compact-mode-only or use a different model for TUI.
- AOM's own hotkeys (currently just Ctrl+C, which we trap in the
  parent) get muddier. Would need a "passthrough toggle" key, which
  is its own UX wart.
- Implementation has cross-platform PTY pitfalls (raw mode, echo
  suppression, signal forwarding).

### D. Hybrid (recommended)

**Compact mode:**
1. **Fast path:** pattern-match the two markers we *know* (`^\[pause\]`
   for ansible.builtin.pause, and the vars_prompt opener if we can
   identify a stable one). Trigger suspend-prompt immediately.
2. **Slow path:** stall detection (B) at 5s as a safety net for
   everything else. Configurable via `--prompt-timeout=Ns`, default 5.
3. **Reuse**: drive both through one new renderer method:

   ```python
   def handle_interactive_prompt(self, pending_text: str) -> str:
       """Stop panel, print pending_text, read a line, return it."""
   ```

   Mirrors `handle_password_prompt` but does **not** suppress echo.

**TUI mode:**
- Same `handle_interactive_prompt` method, implemented via
  `self.suspend()` + `input()` like the password path already does.
- Long-term: Textual modal screen with a single Input widget. Out of
  scope for the first slice.

**Pause-with-seconds (item 4):**
- Detect by parsing the JSONL `v2_playbook_on_task_start` for tasks
  with `action=pause` and `args.seconds` set. Surface as a log line
  `[pause] sleeping 30s…` and a countdown in the status bar. Pure
  cosmetic; no input needed.

## Plan as TDD slices

### IP1. Fix `ansible.builtin.pause` (compact mode) — the immediate user pain

**Scope:** Add `handle_interactive_prompt` to the Renderer Protocol
and CompactRenderer. Add `^\[pause\]` to the pexpect pattern list. On
match: suspend panel, print pending content, `input()`, sendline.

**Tests:**
- Unit: CompactRenderer.handle_interactive_prompt stops the display,
  prints the pending text, calls input(), returns the typed answer,
  restarts the display.
- Integration with a fake ansible-playbook command that emits
  `[pause]\nPress Enter:` (no newline at end) and reads a line back:
  verify input() is called, the typed answer flows through
  `child.sendline`, and the fake exits successfully.

**Size:** ~80 LoC src + ~120 LoC tests. One slice.

### IP2. Stall-detection safety net

**Scope:** Track `_last_event_at` and `_stall_count` in `_drive`. After
N consecutive TIMEOUTs with non-empty `child.before` and no recent
events, treat as an interactive prompt.

**Tests:**
- Unit: a fake child that emits 100 bytes then sits in TIMEOUT
  triggers the stall path after N timeouts; pending bytes get printed;
  input() is called.
- Unit: a fake child that emits a JSONL event every 200ms does NOT
  trigger the stall path even after 30s. (Use mocked time.)

**Size:** ~100 LoC src + ~180 LoC tests. One slice.

### IP3. `vars_prompt` plain-text support

**Scope:** vars_prompt fires in the PRE_RUN_PROMPTS phase. Existing
phase handles password vars_prompt; add the non-password case via the
same `handle_interactive_prompt` path. Pattern is likely the same
shape (`<prompt text>: `).

**Tests:**
- Fake command emits `Enter the deploy tag: ` (no newline), reads a
  line, then emits JSONL. Verify input flows.

**Size:** ~50 LoC src + ~100 LoC tests. Bundles with IP2.

### IP4. TUI integration

**Scope:** AOMApp.handle_interactive_prompt mirrors
handle_password_prompt but with echo (use input() not getpass.getpass).
The worker thread blocks until the user responds, same as today.

**Tests:** AOMApp.handle_interactive_prompt with mocked suspend +
input returns the typed string.

**Size:** ~40 LoC src + ~80 LoC tests.

### IP5. Pause-with-seconds visibility (cosmetic)

**Scope:** When `v2_playbook_on_task_start` fires for a `pause` task
with `args.seconds`, the renderer emits `[pause] sleeping Ns…` to the
log and the status bar shows a countdown.

**Tests:** unit-test the format function; integration verifies the
log line appears for a fake pause event.

**Size:** ~60 LoC src + ~100 LoC tests.

## Recommended landing order

| Order | Slice | Why |
|-------|-------|-----|
| 1 | IP1 | Unblocks the user's deploy playbook. Tightest scope. |
| 2 | IP2 | Generalises IP1; catches custom-module prompts. |
| 3 | IP3 + IP4 | vars_prompt + TUI parity, often delivered together. |
| 4 | IP5 | Polish — pause-with-seconds shouldn't be invisible. |

## Open questions / risks

1. **Echo handling.** `input()` echoes by default — that's correct
   for `pause`/`vars_prompt`. Don't accidentally use `getpass.getpass`
   here.
2. **EOF / Ctrl+C during the prompt.** Compact mode is fine — input()
   raises, we send empty string and the child decides what to do
   (pause aborts on Ctrl+C; that's the user's intent).
3. **Multi-line prompts.** Some pause prompts span multiple lines.
   The `child.before` content already contains them; printing it
   verbatim works.
4. **Interaction with stall-detection's false positives.** Mitigate
   by making the timeout configurable (`--prompt-timeout=N`,
   default 5s) and bumping it during known slow operations? Actually
   too clever; just document the flag.
5. **Race between newline arrival and stall trigger.** Worst case:
   we trigger the prompt and then a newline arrives just as we call
   `input()`. The newline would be consumed by `input()` (since stdin
   is shared). Acceptable in practice — the prompt still completes.

## Quick win

IP1 alone fixes the reported bug in ~1 hour of TDD. Suggest landing
it first as a focused commit, then IP2 as a follow-up once we've
seen IP1 work against the real playbook.

---

## Status: IP1–IP5 shipped

Landed 2026-05-11 in one focused pass after the user's pause-on-deploy
report. Implementation matches the plan with one tightening: stall
detection (IP2) is **flush-only**, never reads stdin, so a false
positive can never block the run. Highlights:

- `Renderer Protocol` gains `handle_interactive_prompt(prompt_text)`.
  CompactRenderer uses `display.stop` + `input()` + `display.start`
  with a `finally` block so a crashing input never leaves the panel
  torn down. AOMApp uses `self.suspend()` + `input()` to hand the
  terminal back to the user.
- `_INTERACTIVE_PROMPT_MARKERS` covers `[pause]`, `Press Enter`,
  `(yes/no)`, `[y/N]` and variants. `_looks_like_interactive_prompt`
  is the single gate: trailing `?` (any question) OR known marker
  with trailing `:` OR `^[varname]: $` / `[varname] (default): $`
  for vars_prompt's default format. Pure trailing-`:` is
  *intentionally* rejected — too common in real log output.
- `_handle_timeout_branch` in the runner is the new fork. High
  confidence → drain buffer, call renderer, sendline, reset count.
  Low confidence with sustained stall (~10s at 0.5s timeout) →
  flush as log lines, never block. Quiet child → tick clock.
- A crashing `handle_interactive_prompt` sends an empty line so the
  child can continue rather than blocking forever.
- IP5: pause-with-seconds emits `[pause] sleeping Ns…` in the
  compact renderer's log when `v2_playbook_on_task_start` carries
  `task.action="*pause"` + `task.args.seconds`. Tolerates string
  serialisation of the number.

Test coverage:
- `tests/unit/test_interactive_prompt.py` — 14 cases (Protocol
  conformance, CompactRenderer + AOMApp method behaviour, EOF /
  KeyboardInterrupt fallthrough, panel restart on crash).
- `tests/unit/test_runner_stall_flush.py` — 11 cases pinning the
  heuristic and the flush-only safety net (incl. log lines
  containing `[INFO]` are NOT treated as prompts).
- `tests/integration/test_runner_interactive_prompts.py` — 6 cases
  with a fake ansible-playbook that writes the captured stdin to
  a tempfile (PTY echo makes plain stdout assertions fragile).
- `tests/tui/test_app_end_to_end.py` — Pilot test exercising
  `handle_interactive_prompt` from the worker thread.
- `tests/unit/test_compact_pause_visibility.py` — 5 cases for IP5.

Full suite: 1749 passing, 6 skipped (up from 1710; +39 net).

### Known limitations (post-implementation)

1. The runner doesn't yet **bridge user keystrokes** outside of the
   detected prompt windows. If the user types into AOM's terminal
   when no prompt is detected, those bytes go to AOM's stdin and
   are never forwarded. Fine for the prompt cases (we drain stdin
   inside `input()` when the prompt fires), problematic for
   ambient interactive commands run by modules. Out of scope.
2. The stall-flush prints the held content **once** when the count
   crosses the threshold. If the child stays silent another 10s,
   nothing new prints — the count resets. Good enough; if we ever
   see a real "child holds output for 30s then prompts" pattern,
   raise the threshold or print a "still waiting…" line periodic.
3. A user typing into the terminal *before* AOM detects the prompt
   has their bytes sitting in the OS stdin buffer; `input()` reads
   them immediately. Considered acceptable behaviour — the user's
   intent is to respond either way.

## Multi-host prompts (2026-06-12)

`ansible.builtin.pause` sets `BYPASS_HOST_LOOP = True`: in a non-serial
multi-host play it runs once, templating against the first host and applying one
answer to all. Two supported per-host paths:

1. **`serial: 1`** — the play re-runs per host, so pause fires per host with that
   host's prompt. AOM already detects/routes these sequentially (validated;
   `tests/integration/test_serial_pause_multihost.py`). A preflight lint
   (`core/preflight_lints.py`) warns when a per-host prompt sits in a non-serial
   multi-host play.
2. **`aom.interactive.confirm`** (Phase 2) — a per-host action plugin that does
   not bypass the host loop and talks to AOM over a FIFO control channel, so
   per-host prompts work regardless of strategy (incl. parallel forks).

Note: ansible only emits a pause prompt when it considers stdin interactive (a
process-group / tcgetpgrp check in `Display.prompt_until`). When that check fails
(e.g. a non-interactive harness), ansible silently skips the pause — AOM can only
forward prompts ansible actually emits. The Phase 2 FIFO channel sidesteps this
entirely because the plugin reads its answer from a FIFO, not a TTY.
