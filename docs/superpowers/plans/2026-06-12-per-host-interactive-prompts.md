# Per-host Interactive Prompts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give per-host interactive prompts (distinct prompt text + distinct answer per host) under AOM, for both the `serial: 1` case (Phase 1, already works — lock it in + signpost) and the strategy-independent case via a bundled `aom.interactive.confirm` action plugin (Phase 2).

**Architecture:** Phase 1 adds a pure preflight lint that warns when a `pause` prompt will be collapsed by `BYPASS_HOST_LOOP`, plus a real two-host `serial: 1` integration test and docs. Phase 2 adds an ansible action plugin (shipped as an installable collection, also bundled for under-AOM resolution) that runs per host and talks to AOM over a polled FIFO + control-dir channel; AOM's existing `_drive` poll loop services requests and routes answers through `renderer.handle_interactive_prompt`.

**Tech Stack:** Python 3.14, pexpect, pytest, ansible-core (integration tier), PyYAML (already a transitive dep via ansible; used only in the pure detector's caller).

**Reference spec:** `docs/superpowers/specs/2026-06-12-per-host-interactive-prompts-design.md`

**Conventions to honor (from AGENTS.md):**
- TDD: failing test first, every task. Run `uv run pytest tests/ -q` green before each commit.
- `core/` must never import from `compact/`/`tui/`/`renderer/`.
- Never add `Co-Authored-By:` trailers. Conventional commit prefixes.
- Never add `# type: ignore`; use the module-level mypy override in `pyproject.toml` if needed.

---

## File Structure

**Phase 1**
- Create `src/ansible_aom/core/preflight_lints.py` — pure detector `detect_bypass_host_loop_prompts`.
- Modify `src/ansible_aom/ansible/runner.py` — read playbook YAML best-effort, build `(play, count)` pairs, call the detector, forward warnings.
- Create `.sisyphus/test-fixtures/serial_pause_multi.yml` + `.sisyphus/test-fixtures/inventory_two_hosts.ini` — real fixture for the integration test.
- Create `tests/unit/test_preflight_lints.py` — detector unit tests.
- Create `tests/integration/test_serial_pause_multihost.py` — real-ansible two-host `serial: 1` test.
- Modify `README.md`, `SPECIFICATION.md`, `.sisyphus/notepads/plans/interactive-prompts.md` — docs.

**Phase 2**
- Create `src/ansible_aom/core/prompt_channel.py` — pure request schema + answer interpretation (AOM-side + tests).
- Create `src/ansible_aom/ansible/prompt_channel.py` — infra `PromptChannel` (create dir, scan/read `.req`, write answer to FIFO, cleanup, drain).
- Modify `src/ansible_aom/ansible/runner.py` — create/cleanup the control dir, inject env, poll the channel in `_drive`, drain on teardown.
- Create the bundled collection tree:
  - `src/ansible_aom/ansible/collections/ansible_collections/aom/interactive/galaxy.yml`
  - `.../aom/interactive/plugins/action/confirm.py`
  - `.../aom/interactive/plugins/modules/confirm.py`
- Create `tests/unit/test_prompt_channel.py` — pure schema tests.
- Create `tests/integration/test_prompt_channel_controller.py` — controller-side FIFO/req handling with a fake renderer + thread.
- Create `tests/integration/test_aom_confirm_plugin.py` — real-ansible two-host (no serial) per-host firing.
- Modify docs + `TEST_SPECIFICATION.md`.

---

# PHASE 1 — `serial: 1` path (ship fast)

## Task 1: Pure detector for bypassed per-host prompts

**Files:**
- Create: `src/ansible_aom/core/preflight_lints.py`
- Test: `tests/unit/test_preflight_lints.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_preflight_lints.py
"""Unit tests for the bypass-host-loop prompt detector (Phase 1.2)."""

from __future__ import annotations

from ansible_aom.core.preflight_lints import detect_bypass_host_loop_prompts


def _play(tasks, *, serial=None, name="Deploy"):
    play = {"name": name, "hosts": "all", "tasks": tasks}
    if serial is not None:
        play["serial"] = serial
    return play


PAUSE_TASK = {
    "name": "Confirm deployment",
    "ansible.builtin.pause": {"prompt": "Deploy to {{ inventory_hostname }}? Enter to go"},
}


def test_warns_when_host_prompt_in_non_serial_multihost_play():
    warnings = detect_bypass_host_loop_prompts([(_play([PAUSE_TASK]), 3)])
    assert len(warnings) == 1
    assert "Confirm deployment" in warnings[0]
    assert "3" in warnings[0]
    assert "serial" in warnings[0]


def test_no_warning_when_single_host():
    assert detect_bypass_host_loop_prompts([(_play([PAUSE_TASK]), 1)]) == []


def test_no_warning_when_serial_is_one():
    assert detect_bypass_host_loop_prompts([(_play([PAUSE_TASK], serial=1), 3)]) == []


def test_warns_when_serial_greater_than_one():
    # serial: 5 still bypasses within the batch -> still collapses.
    assert len(detect_bypass_host_loop_prompts([(_play([PAUSE_TASK], serial=5), 10)])) == 1


def test_no_warning_when_prompt_has_no_host_var():
    task = {"name": "Pause", "ansible.builtin.pause": {"prompt": "Continue? Enter to go"}}
    assert detect_bypass_host_loop_prompts([(_play([task]), 3)]) == []


def test_no_warning_for_non_pause_task():
    task = {"name": "Debug", "ansible.builtin.debug": {"msg": "{{ inventory_hostname }}"}}
    assert detect_bypass_host_loop_prompts([(_play([task]), 3)]) == []


def test_detects_bare_pause_key_and_action_form():
    bare = {"name": "P1", "pause": {"prompt": "{{ inventory_hostname }}: ok? "}}
    action = {
        "name": "P2",
        "action": {"module": "pause", "prompt": "{{ ansible_host }}: ok? "},
    }
    out = detect_bypass_host_loop_prompts([(_play([bare]), 2), (_play([action]), 2)])
    assert len(out) == 2


def test_prompt_as_plain_string_value_is_handled():
    # pause with no args at all (prompt is None) must not crash.
    task = {"name": "P", "ansible.builtin.pause": None}
    assert detect_bypass_host_loop_prompts([(_play([task]), 3)]) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_preflight_lints.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'ansible_aom.core.preflight_lints'`.

- [ ] **Step 3: Write the implementation**

```python
# src/ansible_aom/core/preflight_lints.py
"""Pure preflight lints — best-effort warnings derived from parsed playbook data.

Currently one lint: a ``pause`` task whose prompt varies per host
(``inventory_hostname`` etc.) inside a play that ansible will collapse via
``BYPASS_HOST_LOOP`` (no ``serial: 1``). Ansible runs such a pause once for the
whole batch, showing only the first host's text and applying one answer to all —
see the design doc. The lint nudges the user toward ``serial: 1`` or the
``aom.interactive.confirm`` plugin.

Pure: parsed-data in, ``list[str]`` of human warnings out. The infrastructure
caller (``ansible/runner.py``) owns reading + parsing the YAML and is responsible
for wrapping this in try/except — a lint must never abort a run.
"""

from __future__ import annotations

# Vars whose value differs per host; their presence in a prompt means the user
# expects per-host text.
_HOST_VARYING_VARS: tuple[str, ...] = (
    "inventory_hostname_short",
    "inventory_hostname",
    "ansible_hostname",
    "ansible_host",
)

# Task keys that denote the pause module in its various spellings.
_PAUSE_KEYS: frozenset[str] = frozenset({"pause", "ansible.builtin.pause"})


def _pause_prompt(task: dict) -> str | None:
    """Return the templated prompt string for a pause task, or None.

    Handles the three task spellings:
      ``pause: {prompt: ...}`` / ``ansible.builtin.pause: {prompt: ...}`` /
      ``action: {module: pause, prompt: ...}``. A pause with no args (value
      ``None``) or no ``prompt`` returns None.
    """
    for key in _PAUSE_KEYS:
        if key in task:
            args = task[key]
            if isinstance(args, dict):
                prompt = args.get("prompt")
                return prompt if isinstance(prompt, str) else None
            return None
    action = task.get("action")
    if isinstance(action, dict) and action.get("module") in _PAUSE_KEYS:
        prompt = action.get("prompt")
        return prompt if isinstance(prompt, str) else None
    return None


def _is_serial_one(play: dict) -> bool:
    """True only when the play runs strictly one host at a time.

    ``serial: 1`` (int or str) is safe — ansible re-runs the play per host, so
    pause fires per host. Any other value (absent, >1, percentages, lists) can
    still collapse a multi-host batch, so we do *not* treat it as safe.
    """
    serial = play.get("serial")
    if isinstance(serial, list):
        serial = serial[0] if serial else None
    return str(serial) == "1"


def detect_bypass_host_loop_prompts(
    plays_with_counts: list[tuple[dict, int]],
) -> list[str]:
    """Warn about per-host pause prompts that BYPASS_HOST_LOOP will collapse.

    Args:
        plays_with_counts: ``(raw_play_mapping, resolved_host_count)`` pairs, in
            playbook order. The caller aligns counts; a play it can't resolve
            should simply be omitted.

    Returns:
        One human-readable warning per offending pause task. Empty when nothing
        qualifies. Only top-level ``tasks`` are scanned (not blocks / pre_tasks /
        post_tasks / included files) — best-effort; a missed warning is harmless.
    """
    warnings: list[str] = []
    for play, host_count in plays_with_counts:
        if host_count <= 1 or _is_serial_one(play):
            continue
        for task in play.get("tasks", []):
            if not isinstance(task, dict):
                continue
            prompt = _pause_prompt(task)
            if prompt is None:
                continue
            if not any(var in prompt for var in _HOST_VARYING_VARS):
                continue
            task_name = task.get("name") or "pause"
            warnings.append(
                f"Task '{task_name}' uses a per-host prompt but the play is not "
                f"serial: 1; ansible will prompt once for all {host_count} hosts. "
                f"Use serial: 1, or aom.interactive.confirm for true per-host prompts."
            )
    return warnings
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_preflight_lints.py -q`
Expected: PASS (8 passed).

- [ ] **Step 5: Lint + type-check the new module**

Run: `uv run ruff format src/ansible_aom/core/preflight_lints.py && uv run ruff check --fix src/ansible_aom/core/preflight_lints.py && uv run mypy src/ansible_aom/core/preflight_lints.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/core/preflight_lints.py tests/unit/test_preflight_lints.py
git commit -m "feat(preflight): pure lint for bypassed per-host pause prompts"
```

---

## Task 2: Wire the lint into the runner's preflight stage

**Files:**
- Modify: `src/ansible_aom/ansible/runner.py` (after the `for err in pre_result.errors:` loop, around line 360)
- Test: `tests/unit/test_runner_preflight_lint.py` (create)

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_runner_preflight_lint.py
"""The runner forwards bypass-prompt lint warnings to the renderer."""

from __future__ import annotations

from pathlib import Path

from ansible_aom.ansible import runner


def test_emit_bypass_warnings_reads_yaml_and_calls_detector(tmp_path, monkeypatch):
    playbook = tmp_path / "deploy.yml"
    playbook.write_text(
        "- name: Deploy\n"
        "  hosts: all\n"
        "  tasks:\n"
        "    - name: Confirm deployment\n"
        "      ansible.builtin.pause:\n"
        "        prompt: 'Deploy to {{ inventory_hostname }}? '\n"
    )

    captured: list[str] = []

    class FakeRenderer:
        def add_warning(self, message: str, is_deprecation: bool) -> None:
            captured.append(message)

    # Two resolved hosts for play 1.
    runner._emit_bypass_prompt_warnings(
        playbook=str(playbook),
        resolved_host_counts=[2],
        renderer=FakeRenderer(),
    )
    assert len(captured) == 1
    assert "Confirm deployment" in captured[0]


def test_emit_bypass_warnings_never_raises_on_bad_yaml(tmp_path):
    playbook = tmp_path / "broken.yml"
    playbook.write_text("this: : : not valid yaml :::\n")

    class FakeRenderer:
        def add_warning(self, message: str, is_deprecation: bool) -> None:
            raise AssertionError("should not be called for unparseable YAML")

    # Must swallow the parse error and simply emit nothing.
    runner._emit_bypass_prompt_warnings(
        playbook=str(playbook),
        resolved_host_counts=[2],
        renderer=FakeRenderer(),
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_runner_preflight_lint.py -q`
Expected: FAIL — `AttributeError: module 'ansible_aom.ansible.runner' has no attribute '_emit_bypass_prompt_warnings'`.

- [ ] **Step 3: Add the helper and call it**

Add this helper near the other module-level helpers in `runner.py` (e.g. just below `_callback_env`):

```python
def _emit_bypass_prompt_warnings(
    *,
    playbook: str,
    resolved_host_counts: list[int],
    renderer: Renderer,
) -> None:
    """Best-effort: warn when a per-host pause prompt will be collapsed.

    Reads + parses the playbook YAML, aligns each top-level play with its
    resolved host count (by order), and forwards
    ``detect_bypass_host_loop_prompts`` results through ``renderer.add_warning``.

    Wrapped end-to-end in try/except: a lint must never abort or slow a run, so
    any read/parse/alignment problem yields silence.
    """
    try:
        import yaml  # noqa: PLC0415 — lazy; only needed for the lint

        from ansible_aom.core.preflight_lints import detect_bypass_host_loop_prompts

        with open(playbook, encoding="utf-8") as fh:
            doc = yaml.safe_load(fh)
        if not isinstance(doc, list):
            return
        # Top-level plays only; skip import_playbook entries (no 'hosts').
        plays = [p for p in doc if isinstance(p, dict) and "hosts" in p]
        pairs = list(zip(plays, resolved_host_counts))
        for message in detect_bypass_host_loop_prompts(pairs):
            renderer.add_warning(message, False)
    except Exception as exc:  # noqa: BLE001 — lint is strictly best-effort
        logger.debug("bypass-prompt lint skipped: %s", exc)
```

Then, in `run_playbook`, right after the existing `for err in pre_result.errors:` loop (currently around line 360-362), add the call. Build per-play counts from the preflight definitions:

```python
    for err in pre_result.errors:
        renderer.add_warning(err, False)
        sink.record_stderr(err)

    _emit_bypass_prompt_warnings(
        playbook=playbook,
        resolved_host_counts=[len(p.resolved_hosts) for p in pre_result.definitions],
        renderer=renderer,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_runner_preflight_lint.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Run the full suite + type-check**

Run: `uv run pytest tests/ -q && uv run mypy src/ansible_aom`
Expected: all green (note: `runner.py` is in the relaxed-mypy set; no new errors).

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/ansible/runner.py tests/unit/test_runner_preflight_lint.py
git commit -m "feat(preflight): warn on bypassed per-host pause prompts at startup"
```

---

## Task 3: Real two-host `serial: 1` integration test + fixtures

**Files:**
- Create: `.sisyphus/test-fixtures/inventory_two_hosts.ini`
- Create: `.sisyphus/test-fixtures/serial_pause_multi.yml`
- Test: `tests/integration/test_serial_pause_multihost.py`

- [ ] **Step 1: Create the fixtures**

```ini
# .sisyphus/test-fixtures/inventory_two_hosts.ini
[web]
web1 ansible_connection=local
web2 ansible_connection=local
```

```yaml
# .sisyphus/test-fixtures/serial_pause_multi.yml
# serial: 1 forces ansible to re-run the play per host, so the pause fires
# once per host with that host's templated prompt. Used by AOM's integration
# test to prove per-host prompts arrive sequentially.
- name: Per-host confirm
  hosts: web
  gather_facts: false
  serial: 1
  tasks:
    - name: Confirm deployment
      ansible.builtin.pause:
        prompt: "Deploy to {{ inventory_hostname }}? Press Enter to continue"
    - name: Note
      ansible.builtin.debug:
        msg: "deployed {{ inventory_hostname }}"
```

- [ ] **Step 2: Write the failing test**

```python
# tests/integration/test_serial_pause_multihost.py
"""Integration: serial:1 + pause yields one per-host prompt under AOM.

Drives the real ansible-playbook runner over a two-host local inventory with
serial: 1. The mock renderer answers each prompt with "" (Enter). Proves AOM
detects and routes a distinct prompt per host — the Phase 1 guarantee.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest

FIXTURES = Path(__file__).resolve().parents[2] / ".sisyphus" / "test-fixtures"

_NEEDS_ANSIBLE = pytest.mark.skipif(
    shutil.which("ansible-playbook") is None,
    reason="ansible-playbook unavailable",
)


@_NEEDS_ANSIBLE
def test_serial_one_pause_prompts_per_host(tmp_path):
    from ansible_aom.ansible.runner import run_playbook

    renderer = MagicMock()
    seen: list[str] = []

    def answer(text: str) -> str:
        seen.append(text)
        return ""  # Enter == continue

    renderer.handle_interactive_prompt.side_effect = answer

    exit_code = run_playbook(
        str(FIXTURES / "serial_pause_multi.yml"),
        ["-i", str(FIXTURES / "inventory_two_hosts.ini"), "-c", "local"],
        renderer,
        timeout=0.3,
        session_dir=tmp_path,
        record=False,
    )

    assert exit_code == 0, "playbook should complete after both confirmations"
    assert renderer.handle_interactive_prompt.call_count == 2
    joined = "\n".join(seen)
    assert "web1" in joined and "web2" in joined, f"expected both hosts, got: {seen!r}"
```

- [ ] **Step 3: Run the test**

Run: `uv run pytest tests/integration/test_serial_pause_multihost.py -q`
Expected: PASS where ansible-playbook is installed (2 prompts, both hosts). If ansible is absent it auto-skips — run it in an env with ansible to confirm.

> If it FAILS with only 1 prompt seen, that is a real AOM bug in sequential-prompt handling (not anticipated from the empirical check). Stop and investigate `_handle_timeout_branch`'s stall sentinel before continuing — do **not** paper over it.

- [ ] **Step 4: Commit**

```bash
git add .sisyphus/test-fixtures/inventory_two_hosts.ini .sisyphus/test-fixtures/serial_pause_multi.yml tests/integration/test_serial_pause_multihost.py
git commit -m "test(integration): serial:1 pause prompts per host end-to-end"
```

---

## Task 4: Phase 1 docs

**Files:**
- Modify: `README.md` (add a "Per-host prompts" subsection under interactive/prompt docs)
- Modify: `SPECIFICATION.md` (Section 5.10 area — interactive prompts)
- Modify: `.sisyphus/notepads/plans/interactive-prompts.md` (append the multi-host finding)

- [ ] **Step 1: Append to the notepad**

Add this section to the end of `.sisyphus/notepads/plans/interactive-prompts.md`:

```markdown
## Multi-host prompts (2026-06-12)

`ansible.builtin.pause` sets `BYPASS_HOST_LOOP = True`: in a non-serial
multi-host play it runs once, templating against the first host and applying one
answer to all. Two supported per-host paths:

1. **`serial: 1`** — the play re-runs per host, so pause fires per host with that
   host's prompt. AOM already detects/routes these sequentially (verified;
   `tests/integration/test_serial_pause_multihost.py`). A preflight lint
   (`core/preflight_lints.py`) warns when a per-host prompt sits in a non-serial
   multi-host play.
2. **`aom.interactive.confirm`** (Phase 2) — a per-host action plugin that does
   not bypass the host loop and talks to AOM over a FIFO control channel, so
   per-host prompts work regardless of strategy (incl. parallel forks).
```

- [ ] **Step 2: Add user-facing docs**

In `README.md`, under the section describing interactive prompts, add:

```markdown
### Per-host prompts

`ansible.builtin.pause` runs **once per batch** (it bypasses the host loop), so a
prompt like `Deploy to {{ inventory_hostname }}?` in a multi-host play shows only
the first host and one Enter releases all hosts.

- For per-host confirmation, set `serial: 1` on the play — ansible then prompts
  once per host and AOM shows each in turn.
- AOM warns at startup when it spots a per-host prompt in a non-serial multi-host
  play.
```

Add an equivalent note to `SPECIFICATION.md`'s interactive-prompt section (5.10).

- [ ] **Step 3: Commit**

```bash
git add README.md SPECIFICATION.md .sisyphus/notepads/plans/interactive-prompts.md
git commit -m "docs: per-host prompt behavior and serial:1 guidance"
```

---

# PHASE 2 — `aom.interactive.confirm` per-host plugin

> Phase 2 is independently shippable later. It does not change Phase 1 behavior.

## Task 5: Pure prompt-channel schema (AOM side)

**Files:**
- Create: `src/ansible_aom/core/prompt_channel.py`
- Test: `tests/unit/test_prompt_channel.py`

> Note: this is the AOM-controller-side schema. The action plugin (Task 9) runs
> inside ansible's interpreter and cannot import `ansible_aom`, so it carries its
> own tiny stdlib copy of the same JSON contract. Keep the two in sync; the
> contract is intentionally trivial (4 keys).

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_prompt_channel.py
"""Pure schema for the per-host prompt control channel."""

from __future__ import annotations

from ansible_aom.core.prompt_channel import (
    ENV_VAR,
    FIFO_SUFFIX,
    REQUEST_SUFFIX,
    PromptRequest,
    decode_request,
    encode_request,
    is_abort,
)


def test_env_var_and_suffixes_are_stable():
    assert ENV_VAR == "AOM_PROMPT_CONTROL_DIR"
    assert REQUEST_SUFFIX == ".req"
    assert FIFO_SUFFIX == ".fifo"


def test_request_round_trips():
    req = PromptRequest(id="abc", host="web1", prompt="Deploy web1? ", created=1.5)
    decoded = decode_request(encode_request(req))
    assert decoded == req


def test_decode_tolerates_missing_created():
    decoded = decode_request('{"id": "x", "host": "h", "prompt": "p"}')
    assert decoded.id == "x" and decoded.host == "h" and decoded.prompt == "p"
    assert decoded.created == 0.0


def test_is_abort_recognizes_negatives_case_insensitively():
    for word in ("no", "No", "NO", "abort", "cancel", "n"):
        assert is_abort(word) is True


def test_is_abort_false_for_continue_and_empty():
    for word in ("", "yes", "y", "ok", "  ", "go ahead"):
        assert is_abort(word) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_prompt_channel.py -q`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

```python
# src/ansible_aom/core/prompt_channel.py
"""Pure schema for the per-host interactive-prompt control channel.

The AOM runner and the bundled ``aom.interactive.confirm`` action plugin exchange
JSON request files in a control directory and a one-line answer over a per-request
FIFO. This module is the *AOM side* of that contract (plus the answer-interpretation
helper) and is import-clean for ``core/``. The plugin keeps a stdlib-only mirror of
the same 4-key JSON shape because it can't import this package.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

ENV_VAR = "AOM_PROMPT_CONTROL_DIR"
REQUEST_SUFFIX = ".req"
FIFO_SUFFIX = ".fifo"

# Answers (case-insensitive, stripped) that mean "abort this host".
_ABORT_WORDS: frozenset[str] = frozenset({"n", "no", "abort", "cancel"})


@dataclass(frozen=True)
class PromptRequest:
    """One per-host prompt awaiting an answer."""

    id: str
    host: str
    prompt: str
    created: float = 0.0


def encode_request(req: PromptRequest) -> str:
    """Serialize a request to a single JSON line."""
    return json.dumps(
        {"id": req.id, "host": req.host, "prompt": req.prompt, "created": req.created}
    )


def decode_request(text: str) -> PromptRequest:
    """Parse a request JSON line; ``created`` defaults to 0.0 when absent."""
    data = json.loads(text)
    return PromptRequest(
        id=str(data["id"]),
        host=str(data["host"]),
        prompt=str(data["prompt"]),
        created=float(data.get("created", 0.0)),
    )


def is_abort(answer: str) -> bool:
    """True when the operator's answer means "abort this host"."""
    return answer.strip().lower() in _ABORT_WORDS
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_prompt_channel.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Lint + type-check**

Run: `uv run ruff format src/ansible_aom/core/prompt_channel.py && uv run ruff check --fix src/ansible_aom/core/prompt_channel.py && uv run mypy src/ansible_aom/core/prompt_channel.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/core/prompt_channel.py tests/unit/test_prompt_channel.py
git commit -m "feat(prompt-channel): pure request schema + answer interpretation"
```

---

## Task 6: Controller-side `PromptChannel` (infra)

**Files:**
- Create: `src/ansible_aom/ansible/prompt_channel.py`
- Test: `tests/integration/test_prompt_channel_controller.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_prompt_channel_controller.py
"""Controller side of the prompt channel: scan .req, prompt, answer via FIFO."""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path

from ansible_aom.ansible.prompt_channel import PromptChannel
from ansible_aom.core.prompt_channel import FIFO_SUFFIX, REQUEST_SUFFIX


def _drop_request(ctrl_dir: Path, host: str, prompt: str) -> tuple[str, Path]:
    """Mimic the plugin: mkfifo + atomic-write a .req. Return (id, fifo_path)."""
    rid = uuid.uuid4().hex
    fifo = ctrl_dir / f"{rid}{FIFO_SUFFIX}"
    os.mkfifo(fifo)
    payload = {"id": rid, "host": host, "prompt": prompt, "created": time.time()}
    tmp = ctrl_dir / f"{rid}{REQUEST_SUFFIX}.tmp"
    tmp.write_text(json.dumps(payload))
    tmp.rename(ctrl_dir / f"{rid}{REQUEST_SUFFIX}")
    return rid, fifo


def test_poll_routes_each_answer_to_its_fifo(tmp_path):
    ctrl = tmp_path / "ctrl"
    ctrl.mkdir()
    channel = PromptChannel(ctrl)

    answers: dict[str, str] = {}

    class FakeRenderer:
        def handle_interactive_prompt(self, prompt_text: str) -> str:
            # Answer encodes which host we were asked about.
            return "yes-web1" if "web1" in prompt_text else "yes-web2"

    # Two pending requests (two hosts hitting the prompt in parallel).
    _, fifo1 = _drop_request(ctrl, "web1", "Deploy web1? ")
    _, fifo2 = _drop_request(ctrl, "web2", "Deploy web2? ")

    # Reader threads unblock the controller's FIFO write and capture the answer.
    def reader(fifo: Path, key: str) -> None:
        with open(fifo, encoding="utf-8") as fh:
            answers[key] = fh.readline().rstrip("\n")

    t1 = threading.Thread(target=reader, args=(fifo1, "web1"))
    t2 = threading.Thread(target=reader, args=(fifo2, "web2"))
    t1.start()
    t2.start()

    # Poll until both handled (controller processes them one at a time).
    deadline = time.time() + 5
    while channel.poll(FakeRenderer()) or time.time() < deadline:
        if answers.get("web1") and answers.get("web2"):
            break
        time.sleep(0.02)

    t1.join(2)
    t2.join(2)
    assert answers == {"web1": "yes-web1", "web2": "yes-web2"}
    # .req files cleaned up after handling.
    assert list(ctrl.glob(f"*{REQUEST_SUFFIX}")) == []


def test_drain_sends_empty_answer_to_outstanding_requests(tmp_path):
    ctrl = tmp_path / "ctrl"
    ctrl.mkdir()
    channel = PromptChannel(ctrl)
    _, fifo = _drop_request(ctrl, "web1", "Deploy? ")

    captured: list[str] = []

    def reader() -> None:
        with open(fifo, encoding="utf-8") as fh:
            captured.append(fh.readline().rstrip("\n"))

    t = threading.Thread(target=reader)
    t.start()
    channel.drain()  # teardown: unblock any worker with an empty (=continue) answer
    t.join(2)
    assert captured == [""]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/integration/test_prompt_channel_controller.py -q`
Expected: FAIL — module not found.

- [ ] **Step 3: Write the implementation**

```python
# src/ansible_aom/ansible/prompt_channel.py
"""Controller side of the per-host prompt channel.

AOM creates a control directory and exports its path (``AOM_PROMPT_CONTROL_DIR``).
The bundled ``aom.interactive.confirm`` action plugin drops one ``<id>.req`` JSON
file per host and blocks reading a per-request ``<id>.fifo``. This class, polled
from the runner's existing 0.5s loop, picks up requests in arrival order, routes
each through ``renderer.handle_interactive_prompt`` (which suspends the live panel),
and writes the answer back to that request's FIFO.

All filesystem errors are swallowed and logged — a broken channel must never crash
the run; worst case the worker stays blocked until ``drain`` unblocks it on teardown.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Protocol

from ansible_aom.core.prompt_channel import (
    FIFO_SUFFIX,
    REQUEST_SUFFIX,
    decode_request,
)

logger = logging.getLogger(__name__)


class _PromptRenderer(Protocol):
    def handle_interactive_prompt(self, prompt_text: str) -> str: ...


class PromptChannel:
    """Watches a control dir for prompt requests and answers them via FIFO."""

    def __init__(self, control_dir: Path) -> None:
        self._dir = control_dir
        self._handled: set[str] = set()

    def _pending(self) -> list[Path]:
        """Return unhandled ``.req`` files, oldest first."""
        try:
            reqs = [
                p
                for p in self._dir.glob(f"*{REQUEST_SUFFIX}")
                if p.stem not in self._handled
            ]
        except OSError as exc:
            logger.debug("prompt channel scan failed: %s", exc)
            return []
        reqs.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0.0)
        return reqs

    def _answer(self, request_id: str, answer: str) -> None:
        """Write a single answer line to the request's FIFO (best-effort)."""
        fifo = self._dir / f"{request_id}{FIFO_SUFFIX}"
        try:
            # Opening for write blocks until the plugin opens for read — which it
            # already has (it wrote the .req then blocked on the FIFO).
            with open(fifo, "w", encoding="utf-8") as fh:
                fh.write(answer + "\n")
        except OSError as exc:
            logger.debug("prompt channel answer write failed (%s): %s", fifo.name, exc)

    def poll(self, renderer: _PromptRenderer) -> bool:
        """Handle at most one pending request. Return True if one was handled.

        One-at-a-time keeps the UX serial when many hosts prompt at once and
        keeps each suspend/restore of the live panel tightly scoped.
        """
        pending = self._pending()
        if not pending:
            return False
        req_path = pending[0]
        try:
            request = decode_request(req_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, KeyError) as exc:
            logger.debug("prompt channel: bad request %s: %s", req_path.name, exc)
            self._handled.add(req_path.stem)
            return False

        answer = renderer.handle_interactive_prompt(request.prompt)
        self._answer(request.id, answer)
        self._handled.add(req_path.stem)
        try:
            req_path.unlink(missing_ok=True)
        except OSError:
            pass
        return True

    def drain(self) -> None:
        """Unblock every outstanding request with an empty (=continue) answer.

        Called on teardown so no plugin worker hangs on its FIFO if the run ends
        (Ctrl+C, crash, normal exit) while a request is pending.
        """
        for req_path in self._pending():
            stem = req_path.stem
            self._answer(stem, "")
            self._handled.add(stem)
            try:
                req_path.unlink(missing_ok=True)
            except OSError:
                pass
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/integration/test_prompt_channel_controller.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Full suite + type-check**

Run: `uv run pytest tests/ -q && uv run mypy src/ansible_aom`
Expected: green.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/ansible/prompt_channel.py tests/integration/test_prompt_channel_controller.py
git commit -m "feat(prompt-channel): controller-side FIFO request handler"
```

---

## Task 7: Control-dir lifecycle + env injection in the runner

**Files:**
- Modify: `src/ansible_aom/ansible/runner.py` (`run_playbook` env setup near line 310; `_callback_env` neighborhood)
- Test: `tests/unit/test_runner_prompt_env.py` (create)

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_runner_prompt_env.py
"""The runner provisions a prompt control dir and exports it + the collection."""

from __future__ import annotations

from pathlib import Path

from ansible_aom.ansible import runner
from ansible_aom.core.prompt_channel import ENV_VAR


def test_prompt_control_env_sets_dir_and_collection_path(tmp_path):
    env: dict[str, str] = {}
    ctrl_dir = runner._provision_prompt_channel_env(env, base_dir=tmp_path)

    assert env[ENV_VAR] == str(ctrl_dir)
    assert ctrl_dir.is_dir()
    # The bundled collection root is appended to ANSIBLE_COLLECTIONS_PATH.
    assert "ANSIBLE_COLLECTIONS_PATH" in env
    assert runner._bundled_collections_dir() is not None
    assert str(runner._bundled_collections_dir()) in env["ANSIBLE_COLLECTIONS_PATH"]


def test_bundled_collections_dir_contains_confirm_plugin():
    root = runner._bundled_collections_dir()
    assert root is not None
    action = (
        root
        / "ansible_collections"
        / "aom"
        / "interactive"
        / "plugins"
        / "action"
        / "confirm.py"
    )
    assert action.is_file()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/unit/test_runner_prompt_env.py -q`
Expected: FAIL — helpers don't exist (and the collection files don't exist yet; Task 9 adds them, so `test_bundled_collections_dir_contains_confirm_plugin` stays red until then — that's expected and called out in Step 4).

- [ ] **Step 3: Add the helpers and wire env**

Add to `runner.py` near `_bundled_callback_dir`:

```python
def _bundled_collections_dir() -> Path | None:
    """Resolve the root holding AOM's bundled ansible collections.

    This is the directory that *contains* ``ansible_collections/`` so it can be
    placed on ``ANSIBLE_COLLECTIONS_PATH``. Returns None when the tree is missing
    (packaging glitch) so the caller degrades to "plugin resolvable only if the
    user installed the collection" rather than breaking the run.
    """
    root = Path(__file__).resolve().parent / "collections"
    if (root / "ansible_collections" / "aom" / "interactive").is_dir():
        return root
    return None


def _provision_prompt_channel_env(env: dict[str, str], *, base_dir: Path | None = None) -> Path:
    """Create a per-run prompt control dir and register it (+ the collection) in env.

    Returns the control directory path. The directory is unique per run; the
    runner removes it on teardown. ``base_dir`` is an injection point for tests;
    production passes None and a temp dir is used.
    """
    import tempfile

    parent = base_dir if base_dir is not None else Path(tempfile.gettempdir())
    control_dir = Path(tempfile.mkdtemp(prefix="aom-prompt-", dir=parent))
    env[ENV_VAR] = str(control_dir)

    collections_root = _bundled_collections_dir()
    if collections_root is not None:
        existing = env.get("ANSIBLE_COLLECTIONS_PATH", "")
        parts = [str(collections_root), *([existing] if existing else [])]
        env["ANSIBLE_COLLECTIONS_PATH"] = os.pathsep.join(parts)
    return control_dir
```

Add the import at the top of `runner.py` with the other core imports:

```python
from ansible_aom.core.prompt_channel import ENV_VAR
```

In `run_playbook`, after `env.update(_callback_env())` (around line 311), provision the channel and keep the dir for `_drive` + teardown:

```python
    env = os.environ.copy()
    env.update(_callback_env())
    prompt_control_dir = _provision_prompt_channel_env(env)
```

(The `_drive` call and teardown cleanup are wired in Task 8.)

- [ ] **Step 4: Run the env tests (collection test still red)**

Run: `uv run pytest tests/unit/test_runner_prompt_env.py::test_prompt_control_env_sets_dir_and_collection_path -q`
Expected: PASS. The `_bundled_collections_dir`-not-None portion may be None until Task 9 creates the tree — `test_bundled_collections_dir_contains_confirm_plugin` is expected to fail until Task 9. Do not delete it.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/ansible/runner.py tests/unit/test_runner_prompt_env.py
git commit -m "feat(runner): provision per-host prompt control dir + collection env"
```

---

## Task 8: Poll the channel in `_drive` + drain on teardown

**Files:**
- Modify: `src/ansible_aom/ansible/runner.py` (`_drive` signature + TIMEOUT branch; `run_playbook` `_drive` call + `finally`)
- Test: `tests/integration/test_runner_prompt_channel_e2e.py` (create)

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_runner_prompt_channel_e2e.py
"""A fake 'ansible-playbook' speaks the prompt channel; the runner services it."""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

from ansible_aom.core.prompt_channel import ENV_VAR


def _fake_channel_client(answers_out: Path) -> tuple[str, list[str]]:
    """Fake child: read AOM_PROMPT_CONTROL_DIR, drop two requests, collect answers.

    Mimics two per-host plugin invocations (web1, web2): for each, mkfifo +
    atomic-write a .req, then block reading the FIFO. Writes the two answers it
    received (newline-joined) to answers_out as proof they were routed.
    """
    code = textwrap.dedent(
        f"""
        import json, os, time, uuid
        ctrl = os.environ[{ENV_VAR!r}]
        got = []
        for host in ("web1", "web2"):
            rid = uuid.uuid4().hex
            fifo = os.path.join(ctrl, rid + ".fifo")
            os.mkfifo(fifo)
            payload = {{"id": rid, "host": host, "prompt": "Deploy " + host + "? ", "created": time.time()}}
            tmp = os.path.join(ctrl, rid + ".req.tmp")
            with open(tmp, "w") as f:
                f.write(json.dumps(payload))
            os.rename(tmp, os.path.join(ctrl, rid + ".req"))
            with open(fifo) as f:
                got.append(f.readline().rstrip(chr(10)))
        with open({str(answers_out)!r}, "w") as f:
            f.write(chr(10).join(got))
        """
    )
    return sys.executable, ["-c", code]


def test_runner_services_channel_requests(tmp_path):
    from ansible_aom.ansible.runner import run_playbook

    answers_out = tmp_path / "answers.txt"
    renderer = MagicMock()
    renderer.handle_interactive_prompt.side_effect = (
        lambda p: "ok-web1" if "web1" in p else "ok-web2"
    )
    cmd, args = _fake_channel_client(answers_out)

    with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
        rc = run_playbook("pb.yml", [], renderer, timeout=0.2, session_dir=tmp_path, record=False)

    assert rc == 0
    assert renderer.handle_interactive_prompt.call_count == 2
    assert answers_out.read_text().splitlines() == ["ok-web1", "ok-web2"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/integration/test_runner_prompt_channel_e2e.py -q`
Expected: FAIL — the runner doesn't poll the channel yet, so the fake child blocks and the test times out / `handle_interactive_prompt` is never called.

- [ ] **Step 3: Wire the channel into `_drive` and teardown**

Change `_drive`'s signature to accept the channel, and poll it in the TIMEOUT branch. In `run_playbook`, construct the channel, pass it to `_drive`, and drain+cleanup in `finally`.

In `run_playbook`, build the channel right before the spawn try-block:

```python
    from ansible_aom.ansible.prompt_channel import PromptChannel

    prompt_channel = PromptChannel(prompt_control_dir)
```

Update the `_drive` call:

```python
            exit_code = _drive(
                child, parser, renderer, timeout, sink, diag=diag, prompt_channel=prompt_channel
            )
```

In the `finally` block of `run_playbook`, before/after `renderer.stop()`, drain and remove the control dir:

```python
    finally:
        try:
            prompt_channel.drain()
        except Exception as exc:  # noqa: BLE001 — teardown must not raise
            logger.debug("prompt channel drain failed: %s", exc)
        renderer.stop()
        try:
            import shutil

            shutil.rmtree(prompt_control_dir, ignore_errors=True)
        except Exception:  # noqa: BLE001
            pass
        try:
            stderr_tty = sys.stderr.isatty()
        except (AttributeError, ValueError):
            stderr_tty = False
        _print_session_footer(
            session_id=getattr(sink, "session_id", None),
            stderr_isatty=stderr_tty,
        )
```

Update `_drive`'s signature and TIMEOUT branch. Signature:

```python
def _drive(
    child: pexpect.spawn,
    parser: PtyStreamParser,
    renderer: Renderer,
    timeout: float,
    sink: _SessionSink | _NullSink,
    *,
    diag: diagnostics.RunDiagnostics | None = None,
    prompt_channel: "PromptChannel | None" = None,
) -> int:
```

Add the import for the type at the top of `runner.py` (under TYPE_CHECKING is fine, but a plain import is acceptable here since `prompt_channel.py` only imports from `core`):

```python
from ansible_aom.ansible.prompt_channel import PromptChannel
```

In the `elif idx == timeout_idx:` branch, after the existing `stall_count = _handle_timeout_branch(...)` call and before `continue`, service the channel:

```python
            stall_count = _handle_timeout_branch(child, renderer, sink, stall_count, prior)
            if prompt_channel is not None:
                # Drain all currently-pending per-host requests this tick so N
                # parallel hosts don't wait N timeouts to all be answered.
                while prompt_channel.poll(renderer):
                    pass
            if diag is not None:
                diag.note_timeout()
                diag.note_stall(stall_count if stall_count > 0 else 0)
```

> Note: the existing `_drive` callers in unit tests that call it without
> `prompt_channel` keep working because the parameter defaults to None.

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/integration/test_runner_prompt_channel_e2e.py -q`
Expected: PASS (1 passed), both answers routed.

- [ ] **Step 5: Full suite + type-check**

Run: `uv run pytest tests/ -q && uv run mypy src/ansible_aom`
Expected: green. If any pre-existing `_drive` unit test patches the signature, confirm it still passes (the new param is keyword-only with a default).

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/ansible/runner.py tests/integration/test_runner_prompt_channel_e2e.py
git commit -m "feat(runner): service per-host prompt channel in the drive loop"
```

---

## Task 9: The bundled `aom.interactive.confirm` collection (action plugin + module)

**Files:**
- Create: `src/ansible_aom/ansible/collections/ansible_collections/aom/interactive/galaxy.yml`
- Create: `src/ansible_aom/ansible/collections/ansible_collections/aom/interactive/plugins/action/confirm.py`
- Create: `src/ansible_aom/ansible/collections/ansible_collections/aom/interactive/plugins/modules/confirm.py`
- Modify: `pyproject.toml` (ensure the collection tree ships as package data)

> The action plugin runs inside ansible's interpreter and must be **stdlib-only**
> (no `ansible_aom` import). It mirrors the 4-key JSON contract from
> `core/prompt_channel.py` directly.

- [ ] **Step 1: Create `galaxy.yml`**

```yaml
# src/ansible_aom/ansible/collections/ansible_collections/aom/interactive/galaxy.yml
namespace: aom
name: interactive
version: 0.1.0
readme: README.md
authors:
  - AOM
description: Per-host interactive prompts that cooperate with the AOM monitor.
license:
  - GPL-3.0-or-later
build_ignore: []
```

- [ ] **Step 2: Create the module stub**

Pause-style actions need a paired (empty) module so ansible's loader resolves the
action by name. The module body never runs (the action plugin short-circuits), but
it carries documentation.

```python
# .../aom/interactive/plugins/modules/confirm.py
# GNU General Public License v3.0-or-later
DOCUMENTATION = r"""
---
module: confirm
short_description: Per-host interactive confirmation (AOM-aware)
description:
  - Prompts once per host (does not bypass the host loop). Under the AOM monitor,
    the prompt is shown by AOM and the answer routed back over a control channel.
    Run without AOM, it falls back to reading the controller's stdin like
    ansible.builtin.pause.
options:
  prompt:
    description: Prompt text shown to the operator (templated per host).
    type: str
    required: false
author:
  - AOM
"""

RETURN = r""" # """
```

- [ ] **Step 3: Create the action plugin**

```python
# .../aom/interactive/plugins/action/confirm.py
# GNU General Public License v3.0-or-later
"""Per-host confirmation action plugin.

Deliberately does NOT set BYPASS_HOST_LOOP, so ansible runs it once per host with
that host's templated args. Communicates with the AOM monitor via the control
directory named in ``AOM_PROMPT_CONTROL_DIR``: write an ``<id>.req`` JSON file,
block reading ``<id>.fifo`` for the answer. With no AOM (env var absent), fall back
to reading the controller's stdin.

Answer semantics: empty / yes / anything not in the abort set -> continue this
host; ``no`` / ``n`` / ``abort`` / ``cancel`` -> fail this host only.
"""

from __future__ import annotations

import json
import os
import time
import uuid

from ansible.plugins.action import ActionBase

_ABORT_WORDS = {"n", "no", "abort", "cancel"}
_ENV_VAR = "AOM_PROMPT_CONTROL_DIR"
_REQUEST_SUFFIX = ".req"
_FIFO_SUFFIX = ".fifo"


class ActionModule(ActionBase):
    # NOTE: intentionally no `BYPASS_HOST_LOOP = True` — that's the whole point.

    def run(self, tmp=None, task_vars=None):
        super_result = super().run(tmp, task_vars)
        del tmp  # unused
        prompt = self._task.args.get("prompt") or "Continue? "
        host = (task_vars or {}).get("inventory_hostname", "?")

        answer = self._collect_answer(prompt, host)

        result = dict(super_result)
        if answer.strip().lower() in _ABORT_WORDS:
            result.update(failed=True, msg="aborted by operator")
        else:
            result.update(changed=False, msg="confirmed")
        return result

    def _collect_answer(self, prompt: str, host: str) -> str:
        ctrl = os.environ.get(_ENV_VAR)
        if ctrl:
            try:
                return self._answer_via_channel(ctrl, prompt, host)
            except OSError:
                # Channel broke mid-handshake — fail open (continue) rather than
                # wedge the host forever.
                return ""
        return self._answer_via_stdin(prompt)

    def _answer_via_channel(self, ctrl: str, prompt: str, host: str) -> str:
        rid = uuid.uuid4().hex
        fifo = os.path.join(ctrl, rid + _FIFO_SUFFIX)
        os.mkfifo(fifo)
        try:
            payload = {"id": rid, "host": host, "prompt": prompt, "created": time.time()}
            tmp = os.path.join(ctrl, rid + _REQUEST_SUFFIX + ".tmp")
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(payload))
            os.rename(tmp, os.path.join(ctrl, rid + _REQUEST_SUFFIX))
            # Blocks until AOM opens the FIFO for writing and sends the answer.
            with open(fifo, encoding="utf-8") as fh:
                return fh.readline().rstrip("\n")
        finally:
            try:
                os.unlink(fifo)
            except OSError:
                pass

    def _answer_via_stdin(self, prompt: str) -> str:
        # Bare run (no AOM): behave like pause. Clean under serial: 1.
        try:
            import sys

            sys.stdout.write(prompt)
            sys.stdout.flush()
            return sys.stdin.readline().rstrip("\n")
        except (EOFError, OSError):
            return ""
```

- [ ] **Step 4: Ship the collection as package data**

In `pyproject.toml`, ensure hatchling includes the collection tree (the callback
dir is already shipped; mirror it). Locate the `[tool.hatch.build]` / force-include
or package-data section and confirm `src/ansible_aom/ansible/collections/**` is
included. If the project relies on default inclusion of the package dir, add an
explicit artifact rule:

```toml
[tool.hatch.build.targets.wheel.force-include]
"src/ansible_aom/ansible/collections" = "ansible_aom/ansible/collections"
```

(If an analogous rule already exists for `callback/`, match its style instead.)

- [ ] **Step 5: Verify the bundled-collection runner tests now pass**

Run: `uv run pytest tests/unit/test_runner_prompt_env.py -q`
Expected: PASS (both tests now, including `test_bundled_collections_dir_contains_confirm_plugin`).

- [ ] **Step 6: Sanity-check the collection loads in ansible**

Run:
```bash
ANSIBLE_COLLECTIONS_PATH=src/ansible_aom/ansible/collections uv run ansible-doc -t module aom.interactive.confirm 2>&1 | head -5
```
Expected: prints the module doc header (proves ansible resolves the collection). Skip if ansible is unavailable.

- [ ] **Step 7: Commit**

```bash
git add src/ansible_aom/ansible/collections pyproject.toml
git commit -m "feat(plugin): bundle aom.interactive.confirm per-host action plugin"
```

---

## Task 10: Real-ansible end-to-end — per-host firing without `serial`

**Files:**
- Create: `.sisyphus/test-fixtures/aom_confirm_multi.yml`
- Test: `tests/integration/test_aom_confirm_plugin.py`

- [ ] **Step 1: Create the fixture**

```yaml
# .sisyphus/test-fixtures/aom_confirm_multi.yml
# No serial: proves aom.interactive.confirm fires per host even when the play
# runs all hosts together (the case plain pause cannot do).
- name: Per-host confirm without serial
  hosts: web
  gather_facts: false
  tasks:
    - name: Confirm deployment
      aom.interactive.confirm:
        prompt: "Deploy to {{ inventory_hostname }}? "
    - name: Note
      ansible.builtin.debug:
        msg: "deployed {{ inventory_hostname }}"
```

- [ ] **Step 2: Write the failing test**

```python
# tests/integration/test_aom_confirm_plugin.py
"""Real ansible: aom.interactive.confirm prompts per host with no serial."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest

FIXTURES = Path(__file__).resolve().parents[2] / ".sisyphus" / "test-fixtures"

_NEEDS_ANSIBLE = pytest.mark.skipif(
    shutil.which("ansible-playbook") is None,
    reason="ansible-playbook unavailable",
)


@_NEEDS_ANSIBLE
def test_confirm_plugin_fires_per_host(tmp_path):
    from ansible_aom.ansible.runner import run_playbook

    renderer = MagicMock()
    seen: list[str] = []
    renderer.handle_interactive_prompt.side_effect = lambda p: seen.append(p) or ""

    rc = run_playbook(
        str(FIXTURES / "aom_confirm_multi.yml"),
        ["-i", str(FIXTURES / "inventory_two_hosts.ini"), "-c", "local"],
        renderer,
        timeout=0.3,
        session_dir=tmp_path,
        record=False,
    )

    assert rc == 0
    assert renderer.handle_interactive_prompt.call_count == 2
    joined = "\n".join(seen)
    assert "web1" in joined and "web2" in joined
```

- [ ] **Step 3: Run the test**

Run: `uv run pytest tests/integration/test_aom_confirm_plugin.py -q`
Expected: PASS where ansible is installed — two per-host prompts, no serial.

> If ansible can't resolve `aom.interactive.confirm`, confirm Task 7's env
> injection runs in `run_playbook` (it adds the bundled collection root to
> `ANSIBLE_COLLECTIONS_PATH`). The runner — not the test — supplies that env.

- [ ] **Step 4: Full suite**

Run: `uv run pytest tests/ -q`
Expected: green.

- [ ] **Step 5: Commit**

```bash
git add .sisyphus/test-fixtures/aom_confirm_multi.yml tests/integration/test_aom_confirm_plugin.py
git commit -m "test(integration): aom.interactive.confirm fires per host without serial"
```

---

## Task 11: Phase 2 docs + TEST_SPECIFICATION entries

**Files:**
- Modify: `README.md`, `SPECIFICATION.md`
- Modify: `TEST_SPECIFICATION.md`
- Modify: `.sisyphus/notepads/plans/interactive-prompts.md`

- [ ] **Step 1: Document the plugin**

Add to `README.md` under "Per-host prompts":

```markdown
#### Strategy-independent per-host prompts

For per-host confirmation without `serial: 1` (e.g. parallel forks), use the
bundled `aom.interactive.confirm` action:

```yaml
- name: Confirm deployment
  aom.interactive.confirm:
    prompt: "Deploy to {{ inventory_hostname }}? "
```

Under AOM each host gets its own prompt and answer. Typing `no`/`abort` fails that
host only; Enter continues. Run **without** AOM, the playbook still works — the
action falls back to reading stdin (install the collection so plain
`ansible-playbook` can resolve it).
```

Mirror a concise version into `SPECIFICATION.md` §5.10.

- [ ] **Step 2: Record test cases**

Append to `TEST_SPECIFICATION.md` (use the next free TC numbers):

```markdown
- TC-xxx: serial:1 + pause yields one per-host prompt under AOM
  (`tests/integration/test_serial_pause_multihost.py`).
- TC-xxx: bypass-host-loop prompt lint warns / stays silent appropriately
  (`tests/unit/test_preflight_lints.py`).
- TC-xxx: prompt-channel request schema round-trips; abort words recognized
  (`tests/unit/test_prompt_channel.py`).
- TC-xxx: controller routes each answer to its FIFO; drain unblocks pending
  (`tests/integration/test_prompt_channel_controller.py`).
- TC-xxx: runner services channel requests during the drive loop
  (`tests/integration/test_runner_prompt_channel_e2e.py`).
- TC-xxx: aom.interactive.confirm fires per host without serial
  (`tests/integration/test_aom_confirm_plugin.py`).
```

- [ ] **Step 3: Update the notepad status**

In `.sisyphus/notepads/plans/interactive-prompts.md`, mark Phase 2 shipped with a
one-paragraph summary mirroring the existing "Status:" convention.

- [ ] **Step 4: Final full suite + lint + type-check**

Run: `uv run ruff format && uv run ruff check --fix && uv run mypy src/ansible_aom && uv run pytest tests/ -q`
Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add README.md SPECIFICATION.md TEST_SPECIFICATION.md .sisyphus/notepads/plans/interactive-prompts.md
git commit -m "docs: per-host aom.interactive.confirm plugin + test spec"
```

---

## Self-Review notes (for the implementer)

- **Spec coverage:** Phase 1 = detector (T1) + wiring (T2) + serial:1 e2e (T3) + docs (T4). Phase 2 = pure schema (T5) + controller (T6) + env/lifecycle (T7) + drive-loop polling & drain (T8) + bundled collection (T9) + real e2e (T10) + docs/test-spec (T11). Every spec section maps to a task.
- **Known cross-task dependency:** `test_bundled_collections_dir_contains_confirm_plugin` (T7) is intentionally red until T9 creates the collection tree. Don't "fix" it by weakening the assertion.
- **Type/name consistency:** `ENV_VAR`/`REQUEST_SUFFIX`/`FIFO_SUFFIX` come from `core/prompt_channel.py` and are reused verbatim by the controller (T6) and runner (T7/T8); the action plugin (T9) mirrors them as local constants because it can't import the package. `PromptChannel.poll`/`.drain` names are stable across T6 and T8.
- **Best-effort discipline:** every channel/lint path swallows its own errors and logs at debug — a broken channel or unparseable playbook must never abort a run.
