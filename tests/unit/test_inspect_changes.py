"""Unit tests for aom inspect --changes extraction and rendering."""

from __future__ import annotations

from ansible_aom.core.inspect_model import (
    extract_changes,
)
from ansible_aom.inspect.formatters import (
    format_changes_json,
    format_changes_section,
)


def _sample_events_with_changes() -> list[dict]:
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
        # Task 1: OK (not changed)
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-06-24T10:00:02Z",
            "task": {"id": "t1", "name": "Ping hosts", "path": "roles/web/tasks/main.yml:10"},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-06-24T10:00:03Z",
            "task": {"id": "t1", "name": "Ping hosts", "path": "roles/web/tasks/main.yml:10"},
            "hosts": {"web1": {"changed": False, "ping": "pong"}},
        },
        # Task 2: Changed command on web1
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-06-24T10:00:04Z",
            "task": {
                "id": "t2",
                "name": "Generate SSL cert",
                "path": "roles/web/tasks/ssl.yml:25",
                "role": "web",
            },
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-06-24T10:00:06Z",
            "task": {
                "id": "t2",
                "name": "Generate SSL cert",
                "path": "roles/web/tasks/ssl.yml:25",
                "role": "web",
            },
            "hosts": {
                "web1": {
                    "changed": True,
                    "action": "ansible.builtin.command",
                    "cmd": ["openssl", "req", "-new", "-out", "/etc/ssl/server.csr"],
                    "stdout": "Generating a RSA private key",
                    "stderr": "",
                    "rc": 0,
                }
            },
        },
        # Task 3: Template change with diff
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-06-24T10:00:07Z",
            "task": {
                "id": "t3",
                "name": "Configure nginx.conf",
                "path": "roles/web/tasks/nginx.yml:40",
                "role": "web",
            },
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-06-24T10:00:09Z",
            "task": {
                "id": "t3",
                "name": "Configure nginx.conf",
                "path": "roles/web/tasks/nginx.yml:40",
                "role": "web",
            },
            "hosts": {
                "web1": {
                    "changed": True,
                    "action": "ansible.builtin.template",
                    "dest": "/etc/nginx/nginx.conf",
                    "diff": [
                        {
                            "before": "worker_processes 1;\n",
                            "after": "worker_processes auto;\n",
                            "before_header": "/etc/nginx/nginx.conf",
                            "after_header": "/etc/nginx/nginx.conf",
                        }
                    ],
                },
                "web2": {
                    "changed": True,
                    "action": "ansible.builtin.template",
                    "dest": "/etc/nginx/nginx.conf",
                    "diff": [
                        {
                            "before": "worker_processes 1;\n",
                            "after": "worker_processes auto;\n",
                            "before_header": "/etc/nginx/nginx.conf",
                            "after_header": "/etc/nginx/nginx.conf",
                        }
                    ],
                },
            },
        },
        # Task 4: Loop items with mixed changes
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-06-24T10:00:10Z",
            "task": {
                "id": "t4",
                "name": "Install packages",
                "path": "roles/web/tasks/pkg.yml:15",
                "role": "web",
            },
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-06-24T10:00:12Z",
            "task": {
                "id": "t4",
                "name": "Install packages",
                "path": "roles/web/tasks/pkg.yml:15",
                "role": "web",
            },
            "hosts": {
                "web1": {
                    "changed": True,
                    "action": "ansible.builtin.apt",
                    "results": [
                        {"item": "curl", "changed": False, "msg": "ok"},
                        {"item": "nginx", "changed": True, "msg": "installed"},
                    ],
                }
            },
        },
    ]


def test_extract_changes_empty() -> None:
    session = {"events": []}
    records = extract_changes(session)
    assert records == []


def test_extract_changes_finds_all_changed_tasks() -> None:
    session = {"playbook": "site.yml", "events": _sample_events_with_changes()}
    records = extract_changes(session)
    # 4 task-host pairs had changed: true (t2 on web1, t3 on web1, t3 on web2, t4 on web1)
    assert len(records) == 4

    # Check Task 2 (Generate SSL cert)
    ssl_rec = next(r for r in records if r.task_name == "Generate SSL cert")
    assert ssl_rec.play_name == "Deploy Web"
    assert ssl_rec.role == "web"
    assert ssl_rec.file_line == "roles/web/tasks/ssl.yml:25"
    assert ssl_rec.action == "ansible.builtin.command"
    assert ssl_rec.host == "web1"
    assert ssl_rec.cmd == "openssl req -new -out /etc/ssl/server.csr"
    assert ssl_rec.stdout == "Generating a RSA private key"

    # Check Task 3 (Configure nginx.conf)
    nginx_recs = [r for r in records if r.task_name == "Configure nginx.conf"]
    assert len(nginx_recs) == 2
    assert {r.host for r in nginx_recs} == {"web1", "web2"}
    assert nginx_recs[0].diff is not None

    # Check Task 4 (Loop items)
    pkg_rec = next(r for r in records if r.task_name == "Install packages")
    assert len(pkg_rec.changed_items) == 1
    assert pkg_rec.changed_items[0].label == "nginx"


def test_extract_changes_filters() -> None:
    session = {"playbook": "site.yml", "events": _sample_events_with_changes()}
    # Filter by host
    web2_records = extract_changes(session, host="web2")
    assert len(web2_records) == 1
    assert web2_records[0].host == "web2"

    # Filter by task
    ssl_records = extract_changes(session, task_name="Generate SSL cert")
    assert len(ssl_records) == 1
    assert ssl_records[0].task_name == "Generate SSL cert"


def test_format_changes_section_plain_text() -> None:
    session = {"playbook": "site.yml", "events": _sample_events_with_changes()}
    records = extract_changes(session)
    text = format_changes_section(
        records, session_id="0195171a-4d2b-7412-88ef-961fa2b73091", show_diff=True
    )

    assert "Changed Tasks (4):" in text
    assert "Generate SSL cert" in text
    assert "roles/web/tasks/ssl.yml:25" in text
    assert "openssl req -new" in text
    assert "Configure nginx.conf" in text
    assert "worker_processes auto;" in text


def test_format_changes_json() -> None:
    session = {"playbook": "site.yml", "events": _sample_events_with_changes()}
    records = extract_changes(session)
    payload = format_changes_json(records, session_id="0195171a-4d2b-7412-88ef-961fa2b73091")

    assert payload["session_id"] == "0195171a-4d2b-7412-88ef-961fa2b73091"
    assert payload["total_changes"] == 4
    assert len(payload["changes"]) == 4
    assert payload["changes"][0]["task_name"] == "Generate SSL cert"
