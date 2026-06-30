"""TypedDict for the JSONL event structure emitted by ``ansible.posix.jsonl``.

AOM parses events produced by ``ansible.posix.jsonl`` (or the bundled
``aom_jsonl`` callback that subclasses it). Every event is a JSON object
with a discriminator field ``_event`` and a UTC ``_timestamp``. The
shape is otherwise heterogeneous: ``v2_playbook_on_play_start`` carries
``play.id``/``play.name``/``play.duration``, ``v2_runner_on_*`` carry
``task``, ``hosts``, and per-host result fields, ``v2_playbook_on_stats``
carries per-host ``stats``. Because each event type carries a different
subset of fields, a single TypedDict with ``total=False`` is the most
honest description.

This TypedDict exists to give the event handlers in
:mod:`ansible_aom.core.models` a concrete parameter type instead of
``dict[str, Any]``. It is intentionally permissive: only the fields that
AOM actually reads are listed, and all of them are optional because each
event type carries a different subset. Callers continue to use
``.get()`` for field access; ``total=False`` makes that pattern
type-check cleanly.

Architecture rules:
- Lives in ``core/`` because both infrastructure (compact, tui, formats)
  and other ``core/`` modules import it. It must not import from
  ``compact/``, ``tui/``, ``formats/``, or ``renderer/``.
- Mirrors the field set observed in ``tests/fixtures/*.jsonl`` and the
  ``v2_runner_item_on_*`` events produced by the bundled callback.
- Where a field can be a list (e.g. ``task`` may be a UUID string from
  mitogen mid-task drops), we keep the type loose so the defensive
  ``isinstance`` checks in :mod:`core.models` continue to compile.
"""

from __future__ import annotations

from typing import Any, TypedDict


class JsonlPlay(TypedDict, total=False):
    """Subset of the ``play`` field on ``v2_playbook_on_play_start`` and friends."""

    id: str
    name: str
    duration: dict[str, Any]


class JsonlTask(TypedDict, total=False):
    """Subset of the ``task`` field on task and runner events.

    The ``path`` field uses the ``"file.yml:line_number"`` format described
    in AGENTS.md. ``role`` is the role name prepended with the
    ``"role : "`` runtime prefix (e.g. ``"common"`` from
    ``"common : ping"``). ``action`` and ``args`` carry module info
    observed on ``v2_playbook_on_task_start`` events for tasks like
    ``ansible.builtin.pause`` (used by the compact renderer's pause hint).
    """

    id: str
    name: str
    path: str
    role: str
    action: str
    args: dict[str, Any]


class JsonlHostResult(TypedDict, total=False):
    """Per-host result embedded in ``hosts`` dicts on ``v2_runner_on_*``.

    The shape varies per module — ``changed`` / ``failed`` / ``msg`` /
    ``_ansible_verbose_always`` are observed in fixtures and live
    runs, but new modules can carry additional fields.
    """

    ok: bool
    changed: bool
    failed: bool
    skipped: bool
    unreachable: bool
    skip_reason: str
    msg: str
    _ansible_verbose_always: dict[str, Any]
    _ansible_no_log: bool


class JsonlHostStats(TypedDict, total=False):
    """Per-host aggregate counts on ``v2_playbook_on_stats``."""

    ok: int
    changed: int
    failures: int
    skipped: int
    unreachable: int
    rescued: int
    ignored: int


class JsonlEvent(TypedDict, total=False):
    """Canonical shape of a JSONL event from ``ansible.posix.jsonl``.

    Every field is optional because each event type (``v2_playbook_on_*``,
    ``v2_runner_on_*``, ``v2_runner_item_on_*``) carries a different
    subset. Callers should access fields with ``.get()`` and treat
    missing keys as "this event type doesn't carry that data".

    Field catalogue (with the events that carry them):
    - ``_event``: discriminator string (all events).
    - ``_timestamp``: ISO 8601 UTC timestamp (all events).
    - ``playbook``: ``{"file": "ansible/site.yml"}`` on
      ``v2_playbook_on_start``.
    - ``play``: ``JsonlPlay`` on play-start, task-start, and runner
      events (may be absent on ``v2_runner_item_on_*``).
    - ``task``: ``JsonlTask`` on task and runner events. May be a bare
      UUID string or ``None`` when mitogen drops mid-task — callers
      must defend with ``isinstance`` checks.
    - ``host``: single hostname on ``v2_runner_on_start``.
    - ``hosts``: ``dict[hostname, JsonlHostResult]`` on
      ``v2_runner_on_*`` (and the item variants).
    - ``stats``: ``dict[hostname, JsonlHostStats]`` on
      ``v2_playbook_on_stats``.
    - ``custom_stats``, ``global_custom_stats``: empty dicts on
      ``v2_playbook_on_stats`` in canonical output.
    - ``res``: result dict on runner events (used by
      :mod:`core.redaction`).
    """

    _event: str
    _timestamp: str
    playbook: dict[str, Any]
    play: JsonlPlay
    task: JsonlTask | str | None
    host: str
    hosts: dict[str, JsonlHostResult]
    stats: dict[str, JsonlHostStats]
    custom_stats: dict[str, Any]
    global_custom_stats: dict[str, Any]
    res: dict[str, Any]
