"""Integration tests for the 4-layer redaction pipeline with realistic Ansible events.

These tests build full ``v2_runner_on_*`` event dicts (in the shape
emitted by ``ansible.posix.jsonl`` and the bundled ``aom_jsonl`` callback)
and run them through ``redact_event`` end-to-end. Where the unit tests in
``tests/unit/test_redaction.py`` exercise the public functions in
isolation, these tests verify:

* The ``res`` payload survives Layer 1 (``_ansible_no_log``)
  before the other layers even touch it.
* A realistic envelope (``_event``, ``_timestamp``, ``task``, ``play``)
  is preserved unchanged while the inner ``res`` is redacted.
* Sensitive values embedded in nested ``invocation.module_args`` (which
  only appear at ``-vvv`` verbosity) are redacted recursively.
* Safe events (no sensitive data) pass through with structural
  integrity intact — copy-not-mutate, no field lost, no field invented.
* ``deepcopy``-based isolation: the original event dict and its nested
  values are not mutated by ``redact_event``.

The tests follow the GRUMPI_QA finding H5 directive: realistic Ansible
event dicts, not isolated function calls.

**Note on event shape**: ``ansible.posix.jsonl`` emits events of the form
``{_event, _timestamp, task, play, hosts: {host: <result_dict>}}`` where
``hosts[host]`` IS the result (containing ``ok``, ``changed``,
``invocation``, ``_ansible_no_log``, etc. directly). The
``redact_event`` public API operates on the per-result ``res`` payload
(the ansible task result dict), so the realistic-envelope fixture below
mirrors the shape of that single-host result — exactly as a caller
would extract it from a multi-host ansible event before invoking
``redact_event``.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from ansible_aom.core.config import RedactionConfig
from ansible_aom.core.redaction import (
    REDACTED,
    redact_event,
)

# =============================================================================
# Fixtures — realistic ansible.posix.jsonl event shapes
# =============================================================================


@pytest.fixture
def default_config() -> RedactionConfig:
    """Default RedactionConfig (empty whitelist, custom_fields, custom_patterns)."""
    return RedactionConfig()


def _ansible_event_with_res(res: dict[str, Any]) -> dict[str, Any]:
    """Build a realistic ``v2_runner_on_*`` event dict containing ``res``.

    Mirrors the shape of one host's result inside a real ansible.posix.jsonl
    event envelope (``{_event, _timestamp, task, play, res}``). In a real
    ansible run, the per-host result lives under
    ``event["hosts"][host_name]``; this fixture flattens that one level
    so the event can be passed directly to ``redact_event`` (whose contract
    operates on the per-result ``res`` payload).
    """
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-04-20T10:00:05Z",
        "task": {"id": "task-uuid-1", "name": "Install nginx"},
        "play": {"id": "play-uuid-1", "name": "Setup webservers"},
        "res": res,
    }


# =============================================================================
# Layer 1 — _ansible_no_log: entire res censored, envelope preserved
# =============================================================================


class TestLayer1NoLogOnFullEvent:
    """Layer 1 — when ``res._ansible_no_log=True`` the whole result is censored."""

    def test_entire_res_replaced_with_censored_marker(
        self, default_config: RedactionConfig
    ) -> None:
        """A realistic event with sensitive nested data is fully censored.

        Even though the result contains ``password``, ``api_key``, and a
        nested ``invocation.module_args`` dict that would normally be
        redacted by Layers 2/4, Layer 1 fires first and replaces the
        entire ``res`` with the canonical censored marker.
        """
        event = _ansible_event_with_res(
            {
                "changed": False,
                "password": "super-secret",
                "api_key": "sk_live_abc123",
                "invocation": {
                    "module_args": {"name": "nginx", "password": "hidden"},
                },
            }
        )
        event["res"]["_ansible_no_log"] = True

        result = redact_event(event, default_config)

        assert result["res"] == {"censored": "(no_log)"}
        # None of the sensitive plaintext should leak through.
        censored_str = str(result["res"])
        assert "super-secret" not in censored_str
        assert "sk_live_abc123" not in censored_str
        assert "hidden" not in censored_str

    def test_envelope_preserved_after_no_log_censorship(
        self, default_config: RedactionConfig
    ) -> None:
        """Layer 1 censors only ``res`` — the envelope stays intact.

        The outer keys (``_event``, ``_timestamp``, ``task``, ``play``)
        are not redacted values; they carry metadata that the renderers
        need to identify and group the event.
        """
        event = _ansible_event_with_res({"_ansible_no_log": True, "password": "leak"})

        result = redact_event(event, default_config)

        # Envelope preserved.
        assert result["_event"] == "v2_runner_on_ok"
        assert result["_timestamp"] == "2026-04-20T10:00:05Z"
        assert result["task"] == {"id": "task-uuid-1", "name": "Install nginx"}
        assert result["play"] == {"id": "play-uuid-1", "name": "Setup webservers"}
        # res itself replaced.
        assert result["res"] == {"censored": "(no_log)"}

    def test_no_log_false_passes_through_to_other_layers(
        self, default_config: RedactionConfig
    ) -> None:
        """``_ansible_no_log=False`` must NOT trigger Layer 1.

        Many ansible.posix.jsonl events emit ``_ansible_no_log: False``
        on tasks without sensitive data. This must NOT censor the
        result — the other layers must still run normally.
        """
        event = _ansible_event_with_res(
            {
                "_ansible_no_log": False,
                "password": "should-still-be-redacted-by-layer-2",
            }
        )

        result = redact_event(event, default_config)

        # Layer 1 did not fire — res is not the censored marker.
        assert result["res"] != {"censored": "(no_log)"}
        # Layer 2 still fired on the password field.
        assert result["res"]["password"] == REDACTED


class TestLayer1NoLogOnLoopItems:
    """Layer 1 — per-item censorship inside ``res.results`` loops."""

    def test_per_item_no_log_censors_only_marked_items(
        self, default_config: RedactionConfig
    ) -> None:
        """Loop results with mixed ``_ansible_no_log`` flags.

        Items 0 and 2 have ``_ansible_no_log=False`` and stay intact (Layer 2
        still runs on item 0 because it contains a ``password`` field).
        Item 1 has ``_ansible_no_log=True`` and is replaced wholesale.
        """
        event = _ansible_event_with_res(
            {
                "results": [
                    {
                        "item": "alpha",
                        "password": "leak-me",
                        "_ansible_no_log": False,
                    },
                    {
                        "item": "beta",
                        "secret_value": "do-not-show",
                        "_ansible_no_log": True,
                    },
                    {
                        "item": "gamma",
                        "visible": True,
                        "_ansible_no_log": False,
                    },
                ]
            }
        )

        result = redact_event(event, default_config)

        results = result["res"]["results"]
        # Item 0: Layer 2 redacts the password field, rest preserved.
        assert results[0]["item"] == "alpha"
        assert results[0]["password"] == REDACTED
        assert results[0]["_ansible_no_log"] is False
        # Item 1: Layer 1 replaced the whole thing.
        assert results[1] == {"censored": "(no_log)"}
        # Item 2: untouched.
        assert results[2] == {
            "item": "gamma",
            "visible": True,
            "_ansible_no_log": False,
        }


# =============================================================================
# Layer 2 — password field redaction on realistic events
# =============================================================================


class TestLayer2PasswordFieldsOnEvents:
    """Layer 2 — password-like keys in res are replaced with ``********``."""

    def test_known_ansible_password_fields_redacted(self, default_config: RedactionConfig) -> None:
        """All ``ANSIBLE_PASSWORD_FIELDS`` get redacted inside ``res``."""
        event = _ansible_event_with_res(
            {
                "ansible_ssh_pass": "ssh-secret",
                "ansible_password": "conn-secret",
                "ansible_become_pass": "become-secret",
                "ansible_become_password": "become-pw",
                "ansible_vault_password": "vault-pw",
                "changed": False,
            }
        )

        result = redact_event(event, default_config)

        res = result["res"]
        assert res["ansible_ssh_pass"] == REDACTED
        assert res["ansible_password"] == REDACTED
        assert res["ansible_become_pass"] == REDACTED
        assert res["ansible_become_password"] == REDACTED
        assert res["ansible_vault_password"] == REDACTED
        # Non-sensitive fields untouched.
        assert res["changed"] is False
        # Plaintext must not leak.
        assert "ssh-secret" not in str(res)
        assert "conn-secret" not in str(res)

    def test_generic_secret_fields_redacted(self, default_config: RedactionConfig) -> None:
        """All ``GENERIC_SECRET_FIELDS`` (api_key, token, etc.) redacted."""
        event = _ansible_event_with_res(
            {
                "api_key": "sk_live_abc",
                "api_token": "tok_xyz",
                "secret": "shh",
                "secret_key": "sk-1",
                "token": "tkn-1",
                "auth_token": "at-1",
                "access_token": "act-1",
                "private_key": "-----BEGIN RSA PRIVATE KEY-----",
                "credential": "creds",
                "credentials": {"user": "admin", "password": "leak"},
                "name": "should-stay",
            }
        )

        result = redact_event(event, default_config)

        res = result["res"]
        for sensitive_key in (
            "api_key",
            "api_token",
            "secret",
            "secret_key",
            "token",
            "auth_token",
            "access_token",
            "private_key",
            "credential",
        ):
            assert res[sensitive_key] == REDACTED, (
                f"Field '{sensitive_key}' should have been redacted"
            )
        # credentials dict is redacted wholesale (it's a known sensitive key),
        # so its inner password is also gone.
        assert res["credentials"] == REDACTED
        assert "admin" not in str(res["credentials"])
        assert res["name"] == "should-stay"

    def test_password_match_regex_field_redacted(self, default_config: RedactionConfig) -> None:
        """Fields matching ``PASSWORD_MATCH`` regex (e.g. ``db_password``) redacted."""
        event = _ansible_event_with_res(
            {
                "password": "p1",
                "db_password": "p2",
                "user_passphrase": "p3",
                "admin_passwd": "p4",
                "name": "public",
            }
        )

        result = redact_event(event, default_config)

        res = result["res"]
        assert res["password"] == REDACTED
        assert res["db_password"] == REDACTED
        assert res["user_passphrase"] == REDACTED
        assert res["admin_passwd"] == REDACTED
        assert res["name"] == "public"

    def test_whitelisted_pass_fields_not_redacted(self, default_config: RedactionConfig) -> None:
        """Fields in ``PASSWORD_WHITELIST`` (e.g. ``passenger_version``) preserved.

        These are NOT secrets even though they match ``PASSWORD_MATCH``.
        A naive regex would falsely redact them — the whitelist exists
        to prevent that.
        """
        event = _ansible_event_with_res(
            {
                "passenger_version": "6.0.18",
                "passenger_pool": "4",
                "bypass": "true",
                "overpass": "yes",
                "compass": "north",
                "underpass": "low",
                "passport_number": "12345",
                # Genuine password, must still be redacted.
                "password": "leak",
            }
        )

        result = redact_event(event, default_config)

        res = result["res"]
        assert res["passenger_version"] == "6.0.18"
        assert res["passenger_pool"] == "4"
        assert res["bypass"] == "true"
        assert res["overpass"] == "yes"
        assert res["compass"] == "north"
        assert res["underpass"] == "low"
        assert res["passport_number"] == "12345"
        # The genuine password still gets redacted.
        assert res["password"] == REDACTED

    def test_nested_passwords_in_realistic_dict_redacted(
        self, default_config: RedactionConfig
    ) -> None:
        """A realistic nested res dict with passwords at multiple depths."""
        event = _ansible_event_with_res(
            {
                "changed": True,
                "stdout": "connected",
                "dest": "/etc/app.conf",
                "attributes": {
                    "owner": "root",
                    "mode": "0644",
                    "backup": True,
                },
                "connection": {
                    "user": "deploy",
                    "password": "ssh-pass",
                    "host": "db1.internal",
                    "port": 5432,
                },
                "database": {
                    "name": "app",
                    "password": "db-pass",
                    "ssl": {
                        "enabled": True,
                        "client_key_password": "key-pass",
                    },
                },
            }
        )

        result = redact_event(event, default_config)

        res = result["res"]
        # Non-sensitive fields preserved.
        assert res["changed"] is True
        assert res["stdout"] == "connected"
        assert res["dest"] == "/etc/app.conf"
        assert res["attributes"] == {"owner": "root", "mode": "0644", "backup": True}
        assert res["connection"]["user"] == "deploy"
        assert res["connection"]["host"] == "db1.internal"
        assert res["connection"]["port"] == 5432
        # Sensitive nested fields redacted.
        assert res["connection"]["password"] == REDACTED
        assert res["database"]["password"] == REDACTED
        assert res["database"]["ssl"]["client_key_password"] == REDACTED
        # Plaintext didn't leak.
        assert "ssh-pass" not in str(res)
        assert "db-pass" not in str(res)
        assert "key-pass" not in str(res)


# =============================================================================
# Layer 3 — string sanitization in cmd/stdout/stderr/msg
# =============================================================================


class TestLayer3StringSanitizationOnEvents:
    """Layer 3 — credentials embedded in strings are stripped."""

    def test_cmd_field_url_credentials_stripped(self, default_config: RedactionConfig) -> None:
        """A ``cmd`` string containing ``mysql://user:pass@host`` is sanitized."""
        event = _ansible_event_with_res(
            {
                "cmd": "mysql --host=db1 --user=admin --password=hunter2 inventory < dump.sql",
            }
        )

        result = redact_event(event, default_config)

        cmd = result["res"]["cmd"]
        assert "hunter2" not in cmd
        assert "password=" in cmd  # flag preserved
        assert REDACTED in cmd  # value redacted

    def test_cmd_list_each_entry_sanitized(self, default_config: RedactionConfig) -> None:
        """``cmd`` as a list of strings — every entry is sanitized.

        This is the realistic shape for ``ansible.builtin.command`` and
        ``ansible.builtin.shell`` modules, which emit argv-style lists.
        """
        event = _ansible_event_with_res(
            {
                "cmd": [
                    "mysql",
                    "-h",
                    "db.internal",
                    "-u",
                    "root",
                    "--password=hunter2",
                    "inventory",
                ],
            }
        )

        result = redact_event(event, default_config)

        cmd_list = result["res"]["cmd"]
        assert isinstance(cmd_list, list)
        joined = " ".join(cmd_list)
        assert "hunter2" not in joined
        assert REDACTED in joined

    def test_stdout_field_url_credentials_stripped(self, default_config: RedactionConfig) -> None:
        """``stdout`` containing a URL with embedded creds — creds stripped."""
        event = _ansible_event_with_res(
            {
                "stdout": (
                    "Connection established to postgres://app:p4ssw0rd@db1.internal:5432/mydb"
                ),
            }
        )

        result = redact_event(event, default_config)

        stdout = result["res"]["stdout"]
        assert "p4ssw0rd" not in stdout
        assert REDACTED in stdout
        # URL structure preserved.
        assert "postgres://" in stdout
        assert "db1.internal" in stdout

    def test_stderr_field_cli_credentials_stripped(self, default_config: RedactionConfig) -> None:
        """``stderr`` containing ``--token=`` — token stripped."""
        event = _ansible_event_with_res(
            {
                "stderr": "Error: authentication failed for --token=gho_secrettoken",
            }
        )

        result = redact_event(event, default_config)

        stderr = result["res"]["stderr"]
        assert "gho_secrettoken" not in stderr
        assert REDACTED in stderr

    def test_msg_field_cli_credentials_stripped(self, default_config: RedactionConfig) -> None:
        """``msg`` (debug output) containing ``--api-key=`` — key stripped."""
        event = _ansible_event_with_res(
            {
                "msg": "Configured with --api-key=sk_live_realtoken and restarted daemon",
            }
        )

        result = redact_event(event, default_config)

        msg = result["res"]["msg"]
        assert "sk_live_realtoken" not in msg
        assert REDACTED in msg

    def test_all_sanitized_fields_together(self, default_config: RedactionConfig) -> None:
        """All four string fields can be sanitized in one event."""
        event = _ansible_event_with_res(
            {
                "cmd": "curl --user=admin --password=topsecret https://api.example.com",
                "stdout": "Failed to connect to mysql://root:dbroot@db1",
                "stderr": "Auth rejected: --password=hunter2",
                "msg": "Tried with --token=ghp_supersecret",
            }
        )

        result = redact_event(event, default_config)

        res = result["res"]
        for field, plaintext in (
            ("cmd", "topsecret"),
            ("stdout", "dbroot"),
            ("stderr", "hunter2"),
            ("msg", "ghp_supersecret"),
        ):
            assert plaintext not in str(res[field]), (
                f"Plaintext '{plaintext}' leaked through in '{field}'"
            )
            assert REDACTED in str(res[field]), (
                f"No REDACTED marker in '{field}' — got: {res[field]!r}"
            )


# =============================================================================
# Layer 4 — invocation.module_args recursive redaction
# =============================================================================


class TestLayer4InvocationModuleArgs:
    """Layer 4 — ``res.invocation.module_args`` is recursively redacted (-vvv output)."""

    def test_module_args_password_and_nested_secrets_redacted(
        self, default_config: RedactionConfig
    ) -> None:
        """Realistic ``module_args`` with mixed sensitive and benign fields."""
        event = _ansible_event_with_res(
            {
                "invocation": {
                    "module_args": {
                        "name": "nginx",
                        "state": "started",
                        "password": "should-be-redacted",
                        "api_key": "should-be-redacted",
                        "config": {
                            "worker_processes": 4,
                            "db_password": "should-be-redacted",
                        },
                    }
                },
            }
        )

        result = redact_event(event, default_config)

        ma = result["res"]["invocation"]["module_args"]
        # Benign fields preserved.
        assert ma["name"] == "nginx"
        assert ma["state"] == "started"
        assert ma["config"]["worker_processes"] == 4
        # Sensitive fields redacted at all depths.
        assert ma["password"] == REDACTED
        assert ma["api_key"] == REDACTED
        assert ma["config"]["db_password"] == REDACTED

    def test_module_args_max_depth_does_not_crash(self, default_config: RedactionConfig) -> None:
        """A deeply nested ``module_args`` must not recurse past ``MAX_DEPTH=10``.

        The implementation stops recursing at 10 levels to prevent stack
        overflows on pathological inputs. The test verifies that even a
        12-deep nesting completes without raising.
        """
        # Build a 12-deep nesting: root → d1 → d2 → ... → d12
        deep: dict[str, Any] = {"password": "should-be-redacted"}
        for level in range(12, 0, -1):
            deep = {f"d{level}": deep}
        event = _ansible_event_with_res({"invocation": {"module_args": deep}})

        # Must not raise.
        result = redact_event(event, default_config)

        # Navigate back down and verify the leaf survived (the deepest
        # password may not be redacted because of MAX_DEPTH=10 — that
        # is by design, the function returns early).
        ma = result["res"]["invocation"]["module_args"]
        cursor: Any = ma
        for level in range(1, 13):
            cursor = cursor[f"d{level}"]
        # The leaf may be plaintext (depth > MAX_DEPTH) or REDACTED —
        # both are acceptable as long as we didn't crash.
        assert cursor["password"] in {"should-be-redacted", REDACTED}

    def test_module_args_list_values_recursively_redacted(
        self, default_config: RedactionConfig
    ) -> None:
        """``module_args.users`` as a list of dicts — each dict redacted.

        Common pattern for ``ansible.builtin.user`` loops and the
        ``with_items`` form of password rotation tasks.
        """
        event = _ansible_event_with_res(
            {
                "invocation": {
                    "module_args": {
                        "users": [
                            {"name": "alice", "password": "alice-pw"},
                            {"name": "bob", "password": "bob-pw"},
                        ]
                    }
                },
            }
        )

        result = redact_event(event, default_config)

        users = result["res"]["invocation"]["module_args"]["users"]
        assert users[0]["name"] == "alice"
        assert users[0]["password"] == REDACTED
        assert users[1]["name"] == "bob"
        assert users[1]["password"] == REDACTED


# =============================================================================
# End-to-end: full 4-layer pipeline on a single realistic event
# =============================================================================


class TestFullPipelineOnRealisticEvent:
    """All four layers fired in sequence on a realistic ansible event dict."""

    def test_layers_compose_on_verbose_deploy_event(self, default_config: RedactionConfig) -> None:
        """A single event that exercises Layers 1, 2, 3, and 4 in turn.

        This event has:
        * Layer 2 candidates: ``password``, ``api_key``, ``secret_key`` at top level.
        * Layer 3 candidates: ``cmd`` (CLI args + URL), ``stdout`` (URL).
        * Layer 4 candidates: ``invocation.module_args`` nested password.
        * Layer 1 is NOT triggered (``_ansible_no_log=False``).
        """
        event = {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "task-uuid-7", "name": "Deploy app"},
            "play": {"id": "play-uuid-1", "name": "Deploy"},
            "res": {
                "_ansible_no_log": False,
                "changed": True,
                "password": "deploy-pass",
                "api_key": "deploy-key",
                "secret_key": "deploy-secret",
                "cmd": ("psql postgresql://app:dbpass@db1.internal/mydb --password=cliarg"),
                "stdout": ("Connected to redis://cache:r3dis@redis1.internal:6379/0"),
                "invocation": {
                    "module_args": {
                        "name": "myapp",
                        "state": "present",
                        "db_password": "modarg-pass",
                    }
                },
            },
        }

        result = redact_event(event, default_config)
        res = result["res"]

        # Layer 1 did NOT fire — res is not the censored marker.
        assert res != {"censored": "(no_log)"}
        # Layer 2: top-level secret fields redacted.
        assert res["password"] == REDACTED
        assert res["api_key"] == REDACTED
        assert res["secret_key"] == REDACTED
        assert res["changed"] is True  # non-sensitive field preserved
        # Layer 3: cmd sanitized — both URL credentials and CLI --password.
        assert "dbpass" not in res["cmd"]
        assert "cliarg" not in res["cmd"]
        assert REDACTED in res["cmd"]
        # Layer 3: stdout URL credentials stripped.
        assert "r3dis" not in res["stdout"]
        assert REDACTED in res["stdout"]
        assert "redis1.internal" in res["stdout"]  # host preserved
        # Layer 4: invocation.module_args recursive redaction.
        ma = res["invocation"]["module_args"]
        assert ma["db_password"] == REDACTED
        assert ma["name"] == "myapp"
        assert ma["state"] == "present"
        # Envelope preserved.
        assert result["_event"] == "v2_runner_on_ok"
        assert result["task"]["name"] == "Deploy app"
        # Plaintext leakage check — none of the secrets should appear anywhere.
        blob = str(result)
        for plaintext in (
            "deploy-pass",
            "deploy-key",
            "deploy-secret",
            "dbpass",
            "cliarg",
            "r3dis",
            "modarg-pass",
        ):
            assert plaintext not in blob, f"Plaintext '{plaintext}' leaked into redacted output"


# =============================================================================
# Negative case: safe event passes through unchanged
# =============================================================================


class TestSafeEventUnchanged:
    """Events with no sensitive data are passed through verbatim."""

    def test_no_sensitive_fields_event_unchanged(self, default_config: RedactionConfig) -> None:
        """An event with only benign fields is returned with all fields intact.

        This guards against over-aggressive redaction: if the pipeline
        starts treating ordinary keys as sensitive, this test will fail.
        """
        event = {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "task-uuid-3", "name": "Gather facts"},
            "play": {"id": "play-uuid-1", "name": "Setup"},
            "res": {
                "ansible_facts": {
                    "ansible_distribution": "Ubuntu",
                    "ansible_kernel": "5.15.0",
                    "ansible_memtotal_mb": 16384,
                },
                "changed": False,
            },
        }

        result = redact_event(event, default_config)

        # Whole structure preserved, values unchanged.
        assert result["_event"] == event["_event"]
        assert result["_timestamp"] == event["_timestamp"]
        assert result["task"] == event["task"]
        assert result["play"] == event["play"]
        assert result["res"]["ansible_facts"] == (event["res"]["ansible_facts"])
        assert result["res"]["changed"] is False
        # No REDACTED markers anywhere in the result.
        assert REDACTED not in str(result)


# =============================================================================
# Mutation safety: redact_event must not mutate the input
# =============================================================================


class TestRedactionDoesNotMutateInput:
    """``redact_event`` must be a pure function (deepcopy-based, no in-place edits)."""

    def test_input_event_unchanged_after_redaction(self, default_config: RedactionConfig) -> None:
        """The original event dict is structurally identical after redaction.

        Multiple layers of nesting are checked to verify no in-place
        edits, list mutations, or accidental shared references.
        """
        original = _ansible_event_with_res(
            {
                "_ansible_no_log": False,
                "password": "should-not-mutate",
                "api_key": "should-not-mutate",
                "cmd": "psql postgresql://app:dbpass@db1",
                "stdout": "https://admin:topsecret@internal.example.com",
                "invocation": {
                    "module_args": {
                        "name": "x",
                        "password": "should-not-mutate",
                    }
                },
            }
        )
        # Snapshot for comparison.
        snapshot = copy.deepcopy(original)

        result = redact_event(original, default_config)

        # The input was not mutated.
        assert original == snapshot, "redact_event mutated its input — should use deepcopy"
        # The result IS different (sanitized/redacted).
        assert result != original
        # And the redacted version actually redacts.
        assert result["res"]["password"] == REDACTED
        assert "dbpass" not in result["res"]["cmd"]
        assert "topsecret" not in result["res"]["stdout"]

    def test_shared_list_references_not_aliased(self, default_config: RedactionConfig) -> None:
        """Lists inside the event are not shared between input and output.

        A naive implementation might reuse the list object after
        sanitizing its items. The test creates a list with a sentinel
        item and verifies the input list retains it after redaction.
        """
        original = _ansible_event_with_res(
            {
                "cmd": ["mysql", "-u", "root", "--password=hunter2", "db"],
            }
        )

        result = redact_event(original, default_config)

        # Result list is sanitized.
        assert "hunter2" not in " ".join(result["res"]["cmd"])
        # Input list is unchanged.
        assert original["res"]["cmd"][3] == "--password=hunter2"
        # And the two lists are distinct objects (no shared reference).
        assert result["res"]["cmd"] is not original["res"]["cmd"]


# =============================================================================
# Custom config integration: custom_fields, custom_patterns, whitelist
# =============================================================================


class TestCustomConfigOnRealisticEvents:
    """Custom ``RedactionConfig`` settings integrate cleanly with the pipeline."""

    def test_custom_fields_redacted_on_event(self) -> None:
        """``custom_fields`` adds new keys to redact on top of defaults."""
        config = RedactionConfig(custom_fields=["vault_token", "internal_api_secret"])
        event = _ansible_event_with_res(
            {
                "vault_token": "vault-leak",
                "internal_api_secret": "api-leak",
                "name": "visible",
            }
        )

        result = redact_event(event, config)

        res = result["res"]
        assert res["vault_token"] == REDACTED
        assert res["internal_api_secret"] == REDACTED
        assert res["name"] == "visible"
        assert "vault-leak" not in str(res)
        assert "api-leak" not in str(res)

    def test_custom_whitelist_extends_default(self) -> None:
        """``whitelist`` items are skipped by Layer 2 even if they match the regex."""
        config = RedactionConfig(whitelist=["session_passphrase"])
        event = _ansible_event_with_res(
            {
                "session_passphrase": "should-not-be-redacted",
                "real_password": "should-be-redacted",
            }
        )

        result = redact_event(event, config)

        res = result["res"]
        assert res["session_passphrase"] == "should-not-be-redacted"
        assert res["real_password"] == REDACTED

    def test_custom_patterns_sanitize_strings_on_event(self) -> None:
        """``custom_patterns`` regexes run during Layer 3 sanitization."""
        config = RedactionConfig(
            custom_patterns=[
                {
                    "regex": r"Bearer\s+\S+",
                    "replacement": "Bearer ********",
                },
            ]
        )
        event = _ansible_event_with_res(
            {
                "stdout": "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.signature",
            }
        )

        result = redact_event(event, config)

        stdout = result["res"]["stdout"]
        assert "eyJhbGciOiJIUzI1NiJ9.payload.signature" not in stdout
        assert "Bearer ********" in stdout
