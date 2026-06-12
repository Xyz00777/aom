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
