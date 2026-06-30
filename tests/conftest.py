"""Shared test fixtures for AOM test suite.

CRITICAL: All fixtures are IMMUTABLE. Each test must create its own
mutable state from these fixtures. Never modify fixture return values.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_state_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> Path:
    """Pin AOM's state directory to a per-test tmp dir for every test.

    Without this, runner integration tests write real sessions into
    ``~/.local/state/aom/sessions/``, polluting the user's machine and
    causing flaky test ordering.

    Uses ``tmp_path_factory`` (session-scoped) rather than the per-test
    ``tmp_path`` so the isolated state dir doesn't appear inside any
    test's own ``tmp_path`` directory listing (which would break tests
    that inspect ``tmp_path`` for emptiness or specific contents).
    """
    state_root = tmp_path_factory.mktemp("aom-state-iso", numbered=True)
    state = state_root / "sessions"
    state.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        "ansible_aom.ansible.runner._default_session_dir",
        lambda: state,
    )
    monkeypatch.setattr(
        "ansible_aom.inspect.cli._default_state_dir",
        lambda: state,
    )
    return state


# --- Event Fixtures ---


@pytest.fixture
def event_playbook_start() -> dict:
    """Minimal v2_playbook_on_start event."""
    return {
        "_event": "v2_playbook_on_start",
        "_timestamp": "2026-04-20T10:00:00Z",
    }


@pytest.fixture
def event_play_start() -> dict:
    """v2_playbook_on_play_start event."""
    return {
        "_event": "v2_playbook_on_play_start",
        "_timestamp": "2026-04-20T10:00:01Z",
        "play": {"id": "play-uuid-1", "name": "Setup webservers"},
    }


@pytest.fixture
def event_task_start() -> dict:
    """v2_playbook_on_task_start event (linear strategy)."""
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": "2026-04-20T10:00:02Z",
        "task": {"id": "task-uuid-1", "name": "Install nginx"},
        "play": {"id": "play-uuid-1"},
    }


@pytest.fixture
def event_runner_start() -> dict:
    """v2_runner_on_start event (free strategy)."""
    return {
        "_event": "v2_runner_on_start",
        "_timestamp": "2026-04-20T10:00:02Z",
        "task": {"id": "task-uuid-1", "name": "Install nginx"},
        "host": "web1",
    }


@pytest.fixture
def event_runner_ok() -> dict:
    """v2_runner_on_ok event."""
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-04-20T10:00:05Z",
        "task": {"id": "task-uuid-1", "name": "Install nginx"},
        "hosts": {"web1": {"ok": True, "changed": False}},
    }


@pytest.fixture
def event_runner_ok_changed() -> dict:
    """v2_runner_on_ok event with changed=True."""
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-04-20T10:00:05Z",
        "task": {"id": "task-uuid-1", "name": "Install nginx"},
        "hosts": {"web1": {"ok": True, "changed": True}},
    }


@pytest.fixture
def event_runner_failed() -> dict:
    """v2_runner_on_failed event."""
    return {
        "_event": "v2_runner_on_failed",
        "_timestamp": "2026-04-20T10:00:05Z",
        "task": {"id": "task-uuid-1", "name": "Install nginx"},
        "hosts": {"web1": {"failed": True, "msg": "Error installing package"}},
    }


@pytest.fixture
def event_runner_failed_ignore() -> dict:
    """v2_runner_on_failed event with ignore_errors=True."""
    return {
        "_event": "v2_runner_on_failed",
        "_timestamp": "2026-04-20T10:00:05Z",
        "task": {"id": "task-uuid-1", "name": "Install nginx"},
        "hosts": {
            "web1": {
                "_ansible_verbose_always": {"ignore_errors": True},
                "failed": True,
            }
        },
    }


@pytest.fixture
def event_runner_skipped() -> dict:
    """v2_runner_on_skipped event."""
    return {
        "_event": "v2_runner_on_skipped",
        "_timestamp": "2026-04-20T10:00:03Z",
        "task": {"id": "task-uuid-1", "name": "Install nginx"},
        "hosts": {"web1": {"skipped": True}},
    }


@pytest.fixture
def event_runner_unreachable() -> dict:
    """v2_runner_on_unreachable event."""
    return {
        "_event": "v2_runner_on_unreachable",
        "_timestamp": "2026-04-20T10:00:05Z",
        "task": {"id": "task-uuid-1", "name": "Install nginx"},
        "hosts": {"web1": {"unreachable": True, "msg": "SSH connection failed"}},
    }


@pytest.fixture
def event_stats() -> dict:
    """v2_playbook_on_stats event."""
    return {
        "_event": "v2_playbook_on_stats",
        "_timestamp": "2026-04-20T10:01:00Z",
        "stats": {
            "web1": {
                "ok": 5,
                "changed": 2,
                "failures": 0,
                "skipped": 1,
                "unreachable": 0,
                "rescued": 0,
                "ignored": 0,
            },
            "web2": {
                "ok": 5,
                "changed": 2,
                "failures": 0,
                "skipped": 1,
                "unreachable": 0,
                "rescued": 0,
                "ignored": 0,
            },
        },
        "custom_stats": {},
        "global_custom_stats": {},
    }


# --- Model Fixtures ---


@pytest.fixture
def task_definition() -> dict:
    """Minimal TaskDefinition fields."""
    return {
        "name": "Install nginx",
        "role": "nginx",
        "tags": ["web", "install"],
        "play_id": "1",
        "play_order": 0,
        "task_order": 0,
    }


@pytest.fixture
def play_definition() -> dict:
    """Minimal PlayDefinition fields."""
    return {
        "id": "1",
        "name": "Setup webservers",
        "hosts": "webservers",
        "resolved_hosts": ["web1", "web2"],
        "tasks": [],
    }


# --- PTY Stream Fixtures ---


@pytest.fixture
def jsonl_line() -> str:
    """A minimal JSONL event line."""
    return json.dumps({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})


@pytest.fixture
def password_prompt_ssh() -> str:
    """SSH password prompt line."""
    return "SSH password: "


@pytest.fixture
def password_prompt_vault() -> str:
    """Vault password prompt line."""
    return "Vault password: "


@pytest.fixture
def password_prompt_become() -> str:
    """BECOME password prompt line."""
    return "BECOME password: "


@pytest.fixture
def deprecation_warning_line() -> str:
    """Ansible deprecation warning line."""
    return "[DEPRECATION WARNING]: Setting 'foo' is deprecated and will be removed in version 2.20."


@pytest.fixture
def deprecated_removed_line() -> str:
    """Ansible removed feature deprecation line."""
    return "[DEPRECATED]: The 'bar' feature was removed in ansible-core 2.18."


@pytest.fixture
def warning_line() -> str:
    """Ansible regular warning line."""
    return "[WARNING]: Could not match supplied host pattern, ignoring"


@pytest.fixture
def recap_line() -> str:
    """PLAY RECAP header line."""
    return "PLAY RECAP *********************************************************************"


# --- List-tasks output fixtures ---


@pytest.fixture
def list_tasks_output() -> str:
    """Sample --list-tasks output."""
    return """playbook: site.yml

  play #1 (webservers): Setup web servers\tTAGS: []
    install nginx\tTAGS: [web]
    configure nginx\tTAGS: [web]
    deploy site\tTAGS: [deploy]

  play #2 (dbservers): Setup database\tTAGS: []
    install postgres\tTAGS: [db]
    configure postgres\tTAGS: [db]"""


@pytest.fixture
def list_hosts_output() -> str:
    """Sample --list-hosts output."""
    return """playbook: site.yml

  play #1 (webservers): Setup web servers\tTAGS: []
    pattern: ['webservers']
    hosts (2):
      web1.example.com
      web2.example.com

  play #2 (dbservers): Setup database\tTAGS: []
    pattern: ['dbservers']
    hosts (1):
      db1.example.com"""
