"""Unit tests for aom inspect --warnings extraction and rendering."""

from __future__ import annotations

from ansible_aom.core.inspect_model import (
    extract_warnings,
)
from ansible_aom.inspect.formatters import (
    format_warnings_json,
    format_warnings_section,
)


def _sample_events_with_warnings() -> list[dict]:
    return [
        {
            "_event": "v2_playbook_on_start",
            "_timestamp": "2026-06-24T10:00:00Z",
        },
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-06-24T10:00:01Z",
            "play": {"id": "p1", "name": "Deploy Web"},
        },
        # Task 1: Deprecation in runner result
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-06-24T10:00:02Z",
            "task": {
                "id": "t1",
                "name": "Install docker",
                "path": "roles/docker/tasks/main.yml:12",
                "role": "docker",
            },
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-06-24T10:00:03Z",
            "task": {
                "id": "t1",
                "name": "Install docker",
                "path": "roles/docker/tasks/main.yml:12",
                "role": "docker",
            },
            "hosts": {
                "web1": {
                    "changed": False,
                    "deprecations": [
                        {
                            "msg": (
                                "The docker_compose module is deprecated. "
                                "Use community.docker.docker_compose_v2."
                            ),
                            "version": "2.18",
                        }
                    ],
                    "warnings": ["Consider using systemd service instead"],
                }
            },
        },
        # Task 2: Stderr warning event
        {
            "_event": "aom_stderr_line",
            "_timestamp": "2026-06-24T10:00:04Z",
            "line": "[WARNING]: Module did not use an absolute path: 'var/run/app'",
            "source": "stderr",
        },
    ]


def test_extract_warnings_empty() -> None:
    session = {"events": []}
    records = extract_warnings(session)
    assert records == []


def test_extract_warnings_finds_all() -> None:
    session = {"playbook": "site.yml", "events": _sample_events_with_warnings()}
    records = extract_warnings(session)
    assert len(records) == 3

    # Check deprecation
    depr = next(r for r in records if r.warning_type == "deprecation")
    assert "docker_compose module is deprecated" in depr.message
    assert depr.task_name == "Install docker"
    assert depr.role == "docker"
    assert depr.host == "web1"

    # Check runner warning
    warn1 = next(r for r in records if "systemd service" in r.message)
    assert warn1.warning_type == "warning"
    assert warn1.task_name == "Install docker"

    # Check stderr warning
    warn2 = next(r for r in records if "Module did not use an absolute path" in r.message)
    assert warn2.warning_type == "warning"


def test_format_warnings_section_plain_text() -> None:
    session = {"playbook": "site.yml", "events": _sample_events_with_warnings()}
    records = extract_warnings(session)
    text = format_warnings_section(records, session_id="0195171a-4d2b-7412-88ef-961fa2b73091")

    assert "Warnings & Deprecations (3):" in text
    assert "[DEPRECATION]" in text
    assert "docker_compose module is deprecated" in text
    assert "[WARNING]" in text
    assert "Module did not use an absolute path" in text


def test_format_warnings_json() -> None:
    session = {"playbook": "site.yml", "events": _sample_events_with_warnings()}
    records = extract_warnings(session)
    payload = format_warnings_json(records, session_id="0195171a-4d2b-7412-88ef-961fa2b73091")

    assert payload["session_id"] == "0195171a-4d2b-7412-88ef-961fa2b73091"
    assert payload["total_warnings"] == 3
    assert len(payload["warnings"]) == 3
