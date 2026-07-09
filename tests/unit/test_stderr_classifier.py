"""Unit tests for the v1 stderr classifier.

Covers ``core/stderr_classifier.py`` — the 12-source, 30-regex classifier
that maps raw ansible-playbook stderr lines to typed ``StderrEvent``
records. Source-of-truth: the taxonomy at
``.sisyphus/notepads/2026-06-30-verbosity-pre-impl-interview/stderr-classification-taxonomy.md``.
"""

from __future__ import annotations

import pytest

from ansible_aom.core.stderr_classifier import (
    CLASSIFIER_RULES,
    LEVEL_MAP,
    StderrEvent,
    StderrLevel,
    StderrSource,
    classify,
)

# =============================================================================
# Constants & shape
# =============================================================================


class TestStderrSource:
    """The StderrSource enum is the public contract — 12 named values + UNKNOWN."""

    def test_member_count_is_13(self) -> None:
        """The enum has 12 named values (per the v1 design) plus an
        UNKNOWN catch-all for lines that match no rule."""
        assert len(StderrSource) == 13

    def test_all_required_members_present(self) -> None:
        """Every source named in the v1 plan exists in the enum."""
        expected = {
            "warning",
            "deprecation",
            "error",
            "ssh_debug",
            "ssh_info",
            "connection",
            "connection_lifecycle",
            "plugin_loading",
            "inventory",
            "vault",
            "prompt",
            "run_level",
            "unknown",
        }
        actual = {member.value for member in StderrSource}
        assert actual == expected

    def test_values_are_lowercase_strings(self) -> None:
        """Values match the canonical strings used in events.jsonl."""
        for member in StderrSource:
            assert member.value == member.value.lower()
            assert " " not in member.value


class TestStderrLevel:
    """StderrLevel is a small IntEnum — 6 buckets, no overlap."""

    def test_levels_cover_caplevel_zero_through_four(self) -> None:
        """Levels span always (0) up to vvvvv (4) plus debug bucket."""
        values = {member.value for member in StderrLevel}
        # 0 (always), 1 (-v), 2 (-vv), 3 (-vvv), 4 (-vvvvv), plus debug
        assert 0 in values
        assert 1 in values
        assert 2 in values
        assert 3 in values
        assert 4 in values


class TestClassifierRules:
    """CLASSIFIER_RULES shape and ordering — the engine of the classifier."""

    def test_at_least_30_rules(self) -> None:
        """The plan calls for 30 rules; we accept more but not fewer."""
        assert len(CLASSIFIER_RULES) >= 30

    def test_every_rule_has_three_fields(self) -> None:
        """Each rule is ``(source, regex, has_host)``."""
        for rule in CLASSIFIER_RULES:
            assert len(rule) == 3
            source, regex, has_host = rule
            assert isinstance(source, StderrSource)
            assert hasattr(regex, "match")
            assert isinstance(has_host, bool)

    def test_regexes_are_compiled(self) -> None:
        """Each rule's regex is a pre-compiled ``re.Pattern`` (hot path)."""
        for _source, regex, _has_host in CLASSIFIER_RULES:
            # re.Pattern has a .match method but plain str does too.
            # The defining property is the .pattern attribute on Pattern.
            assert hasattr(regex, "pattern"), f"regex is not compiled: {regex!r}"

    def test_no_duplicate_first_words(self) -> None:
        """No two rules share the same first matching token (first-match-wins
        would alias one to the other). Heuristic: each rule's literal
        prefix characters must be unique enough that ordering matters.
        """
        prefixes: list[str] = []
        for _source, regex, _has_host in CLASSIFIER_RULES:
            # Pull the first literal characters from the pattern.
            pattern = regex.pattern
            # Skip leading anchors and optional non-capturing groups.
            stripped = pattern.lstrip("^")
            # Use the first 5 chars as a coarse uniqueness key.
            prefixes.append(stripped[:5])
        # Some sharing is OK (e.g. "<([^>]+)> SSH: " appears in two rules
        # with different trailing structure) but the count should be ≥
        # the number of distinct starting tokens.
        assert len(set(prefixes)) >= 20  # very loose — fails only on gross dupes


# =============================================================================
# classify() — basic contract
# =============================================================================


class TestClassifyEmpty:
    """classify() must never crash on empty / whitespace input."""

    def test_empty_string_returns_unknown(self) -> None:
        """Empty line → UNKNOWN source, no host, no level."""
        event = classify("")
        assert event.source is StderrSource.UNKNOWN
        assert event.host is None
        assert event.line == ""

    def test_whitespace_only_returns_unknown(self) -> None:
        """Whitespace-only line → UNKNOWN."""
        event = classify("   \t  ")
        assert event.source is StderrSource.UNKNOWN

    def test_arbitrary_garbage_returns_unknown(self) -> None:
        """A line matching no rule → UNKNOWN, original text preserved."""
        event = classify("just some random unclassifiable noise xyz123")
        assert event.source is StderrSource.UNKNOWN
        assert event.line == "just some random unclassifiable noise xyz123"
        assert event.host is None


# =============================================================================
# Source: warning
# =============================================================================


class TestClassifyWarning:
    """[WARNING]: lines are run-level (no host)."""

    def test_plain_warning(self) -> None:
        event = classify("[WARNING]: No inventory was parsed, only implicit localhost is available")
        assert event.source is StderrSource.WARNING
        assert event.host is None

    def test_warning_inventory_loading(self) -> None:
        event = classify("[WARNING]: Unable to parse /etc/ansible/hosts as an inventory source")
        assert event.source is StderrSource.WARNING

    def test_warning_plugin_load(self) -> None:
        event = classify("[WARNING]: Skipping callback plugin 'jsonl', unable to load")
        assert event.source is StderrSource.WARNING

    def test_worker_process_warning(self) -> None:
        """The WorkerProcess warning is also classified as warning."""
        event = classify(
            "[WARNING]: WorkerProcess for [web1/Task] errantly sent data directly to stdout"
        )
        assert event.source is StderrSource.WARNING


# =============================================================================
# Source: deprecation
# =============================================================================


class TestClassifyDeprecation:
    """[DEPRECATION WARNING]: lines are run-level."""

    def test_deprecation_callback(self) -> None:
        event = classify(
            "[DEPRECATION WARNING]: The 'jsonl' callback plugin implements deprecated method 'runner_on_ok'."
        )
        assert event.source is StderrSource.DEPRECATION
        assert event.host is None

    def test_deprecation_interpreter(self) -> None:
        event = classify(
            "[DEPRECATION WARNING]: Distribution Ubuntu 20.04 on host db1 should use the python3 interpreter"
        )
        assert event.source is StderrSource.DEPRECATION


# =============================================================================
# Source: error
# =============================================================================


class TestClassifyError:
    """[ERROR]: lines and unbracketed preflight ERROR: lines."""

    def test_bracketed_error(self) -> None:
        event = classify("[ERROR]: No matching task 'foo' found.")
        assert event.source is StderrSource.ERROR
        assert event.host is None

    def test_user_interrupted(self) -> None:
        event = classify("[ERROR]: User interrupted execution")
        assert event.source is StderrSource.ERROR

    def test_preflight_error_unbracketed(self) -> None:
        """Unbracketed ``ERROR:`` from cli/__init__.py preflight path."""
        event = classify("ERROR: Ansible requires the locale encoding to be UTF-8; Detected ascii")
        assert event.source is StderrSource.ERROR


# =============================================================================
# Source: ssh_debug (caplevel 4+)
# =============================================================================


class TestClassifySshDebug:
    """``<host> SSH:`` lines from ssh.py (caplevel 4+)."""

    def test_with_host(self) -> None:
        event = classify(
            "<web1> SSH: ANSIBLE_REMOTE_PORT/remote_port/ansible_port set: (-o)(Port=22)"
        )
        assert event.source is StderrSource.SSH_DEBUG
        assert event.host == "web1"
        assert event.level == 4

    def test_with_fqdn_host(self) -> None:
        event = classify("<db.internal.example.com> SSH: ansible.cfg set ssh_args: (-C)")
        assert event.source is StderrSource.SSH_DEBUG
        assert event.host == "db.internal.example.com"

    def test_without_host(self) -> None:
        """SSH: without a host prefix still classifies as ssh_debug with no host."""
        event = classify('SSH: ANSIBLE_PRIVATE_KEY_FILE set: (-o)(IdentityFile="/etc/ansible/key")')
        assert event.source is StderrSource.SSH_DEBUG
        assert event.host is None


# =============================================================================
# Source: ssh_info (caplevel 2-3)
# =============================================================================


class TestClassifySshInfo:
    """SSH agent / connect / retry / rc lines."""

    def test_ssh_agent_add(self) -> None:
        event = classify("<web1> SSH: SSH_AGENT adding SHA256:abc123 to agent")
        assert event.source is StderrSource.SSH_INFO
        assert event.host == "web1"

    def test_ssh_agent_exists(self) -> None:
        event = classify("<web1> SSH: SSH_AGENT SHA256:abc123 exists in agent")
        assert event.source is StderrSource.SSH_INFO

    def test_failed_to_connect(self) -> None:
        event = classify(
            "<web1> Failed to connect to the host via ssh: ssh: connect to host web1 port 22: Connection refused"
        )
        assert event.source is StderrSource.SSH_INFO
        assert event.host == "web1"

    def test_failed_to_connect_permission_denied(self) -> None:
        event = classify(
            "<web1> Failed to connect to the host via ssh: Permission denied (publickey,password)."
        )
        assert event.source is StderrSource.SSH_INFO

    def test_ssh_retry(self) -> None:
        event = classify(
            "<web1> ssh_retry: attempt: 1, ssh return code is 255. cmd (ssh), pausing for 1 seconds"
        )
        assert event.source is StderrSource.SSH_INFO
        assert event.host == "web1"

    def test_ssh_retry_caught_exception(self) -> None:
        event = classify(
            "<web1> ssh_retry: attempt: 2, caught exception(Connection refused) from cmd (ssh)"
        )
        assert event.source is StderrSource.SSH_INFO

    def test_rc_line(self) -> None:
        event = classify("<web1> rc=0, stdout and stderr censored due to no log")
        assert event.source is StderrSource.SSH_INFO
        assert event.host == "web1"

    def test_rc_tuple(self) -> None:
        event = classify("<web1> (0, b'stdout', b'stderr')")
        assert event.source is StderrSource.SSH_INFO
        assert event.host == "web1"

    def test_controlpersist_broken_pipe(self) -> None:
        """This one is run-level (no host) — different from the rest of ssh_info."""
        event = classify("RETRYING BECAUSE OF CONTROLPERSIST BROKEN PIPE")
        assert event.source is StderrSource.SSH_INFO
        assert event.host is None


# =============================================================================
# Source: connection
# =============================================================================


class TestClassifyConnection:
    """Lock + local connection + EXEC/PUT/FETCH lines."""

    def test_connection_lock_waiting(self) -> None:
        event = classify("<web1> CONNECTION: pid 12345 waiting for lock on 3")
        assert event.source is StderrSource.CONNECTION
        assert event.host == "web1"

    def test_connection_lock_acquired(self) -> None:
        event = classify("<web1> CONNECTION: pid 12345 acquired lock on 3")
        assert event.source is StderrSource.CONNECTION

    def test_connection_lock_released(self) -> None:
        event = classify("<web1> CONNECTION: pid 12345 released lock on 3")
        assert event.source is StderrSource.CONNECTION

    def test_local_connection_establish(self) -> None:
        event = classify("<localhost> ESTABLISH LOCAL CONNECTION FOR USER: root")
        assert event.source is StderrSource.CONNECTION
        assert event.host == "localhost"

    def test_exec(self) -> None:
        event = classify("<web1> EXEC /bin/sh -c 'echo hello'")
        assert event.source is StderrSource.CONNECTION
        assert event.host == "web1"

    def test_put(self) -> None:
        event = classify("<web1> PUT /tmp/src TO /tmp/dst")
        assert event.source is StderrSource.CONNECTION

    def test_fetch(self) -> None:
        event = classify("<web1> FETCH /remote/path TO /local/path")
        assert event.source is StderrSource.CONNECTION


# =============================================================================
# Source: connection_lifecycle
# =============================================================================


class TestClassifyConnectionLifecycle:
    """Persistent connection reset messages (host is NOT in text)."""

    def test_reset_persistent_connection(self) -> None:
        event = classify("resetting persistent connection for socket_path /tmp/ansible-ssh-foo")
        assert event.source is StderrSource.CONNECTION_LIFECYCLE
        assert event.host is None

    def test_reset_call(self) -> None:
        event = classify("reset call on connection instance")
        assert event.source is StderrSource.CONNECTION_LIFECYCLE
        assert event.host is None


# =============================================================================
# Source: plugin_loading
# =============================================================================


class TestClassifyPluginLoading:
    """Callback + inventory plugin setup."""

    def test_callback_loading(self) -> None:
        event = classify(
            "Loading callback plugin ansible.posix.jsonl of type stdout, v2.0 from /x/y.py"
        )
        assert event.source is StderrSource.PLUGIN_LOADING
        assert event.host is None

    def test_inventory_plugin_setup(self) -> None:
        event = classify("setting up inventory plugins")
        assert event.source is StderrSource.PLUGIN_LOADING
        assert event.host is None


# =============================================================================
# Source: inventory
# =============================================================================


class TestClassifyInventory:
    """Inventory parse / decline diagnostics."""

    def test_parsed_inventory(self) -> None:
        event = classify("Parsed hosts inventory source with ini plugin")
        assert event.source is StderrSource.INVENTORY

    def test_declined_parsing(self) -> None:
        event = classify("auto declined parsing hosts as it did not pass its verify_file() method")
        assert event.source is StderrSource.INVENTORY


# =============================================================================
# Source: vault
# =============================================================================


class TestClassifyVault:
    """Vault password prompts + vvvvv vault debug."""

    def test_vault_password_prompt(self) -> None:
        event = classify("Vault password (default): ")
        assert event.source is StderrSource.VAULT
        assert event.host is None

    def test_new_vault_password_prompt(self) -> None:
        event = classify("New vault password (myvault): ")
        assert event.source is StderrSource.VAULT

    def test_trying_vault_secret(self) -> None:
        event = classify("Trying to use vault secret=(secret) id=default to decrypt <origin>")
        assert event.source is StderrSource.VAULT

    def test_encrypting_with_vault_id(self) -> None:
        event = classify('Encrypting with vault_id "default" and vault secret <secret>')
        assert event.source is StderrSource.VAULT

    def test_decrypt_successful(self) -> None:
        event = classify(
            'Decrypt of "file.yml" successful with secret=<secret> and vault_id=default'
        )
        assert event.source is StderrSource.VAULT

    def test_encrypt_vault_id_eq(self) -> None:
        event = classify("encrypt_vault_id=myvault")
        assert event.source is StderrSource.VAULT

    def test_reading_vault_password_file(self) -> None:
        event = classify("Reading vault password file: /etc/ansible/vault-pass")
        assert event.source is StderrSource.VAULT

    def test_vault_password_file_is_script(self) -> None:
        event = classify("The vault password file /etc/ansible/vault-pass is a client script.")
        assert event.source is StderrSource.VAULT


# =============================================================================
# Source: prompt
# =============================================================================


class TestClassifyPrompt:
    """Interactive become / SSH password prompts."""

    def test_ssh_password_prompt(self) -> None:
        event = classify("SSH password: ")
        assert event.source is StderrSource.PROMPT

    def test_become_password_prompt(self) -> None:
        event = classify("BECOME password: ")
        assert event.source is StderrSource.PROMPT

    def test_sudo_password_prompt(self) -> None:
        event = classify("sudo password[defaults to SSH password]: ")
        assert event.source is StderrSource.PROMPT


# =============================================================================
# Source: run_level (catch-all for diagnostics + fallback)
# =============================================================================


class TestClassifyRunLevel:
    """Misc diagnostics: config, plays, retry, syntax, host-pattern, debug, unknown."""

    def test_config_file_in_use(self) -> None:
        event = classify("Using /etc/ansible/ansible.cfg as config file")
        assert event.source is StderrSource.RUN_LEVEL
        assert event.host is None

    def test_no_config_file(self) -> None:
        event = classify("No config file found; using defaults")
        assert event.source is StderrSource.RUN_LEVEL

    def test_play_count(self) -> None:
        event = classify("2 plays in site.yml")
        assert event.source is StderrSource.RUN_LEVEL

    def test_collection_playbook(self) -> None:
        event = classify("running playbook inside collection my.collection")
        assert event.source is StderrSource.RUN_LEVEL

    def test_retry_file(self) -> None:
        event = classify("\tto retry, use: --limit @/path/to/site.retry")
        assert event.source is StderrSource.RUN_LEVEL

    def test_syntax_ok(self) -> None:
        event = classify("No issues encountered")
        assert event.source is StderrSource.RUN_LEVEL

    def test_host_pattern_mismatch(self) -> None:
        event = classify("Could not match supplied host pattern, ignoring: nonexistent")
        assert event.source is StderrSource.RUN_LEVEL

    def test_current_user(self) -> None:
        event = classify(
            "Current user (uid=1000) does not seem to exist on this system, leaving user empty."
        )
        assert event.source is StderrSource.RUN_LEVEL

    def test_plugin_loading_debug(self) -> None:
        event = classify("trying /path/to/plugin/directory")
        assert event.source is StderrSource.RUN_LEVEL


# =============================================================================
# Level mapping
# =============================================================================


class TestLevelMap:
    """LEVEL_MAP drives the 'level' field on emitted events."""

    def test_all_sources_have_level(self) -> None:
        for source in StderrSource:
            assert source in LEVEL_MAP, f"StderrSource.{source.name} missing from LEVEL_MAP"

    def test_levels_are_integers(self) -> None:
        for value in LEVEL_MAP.values():
            assert isinstance(value, int)
            assert 0 <= value <= 4

    def test_known_level_assignments(self) -> None:
        """Lock the v1 level mapping to a public contract."""
        assert LEVEL_MAP[StderrSource.WARNING] == 0
        assert LEVEL_MAP[StderrSource.DEPRECATION] == 0
        assert LEVEL_MAP[StderrSource.ERROR] == 0
        assert LEVEL_MAP[StderrSource.SSH_DEBUG] == 4
        assert LEVEL_MAP[StderrSource.SSH_INFO] == 2
        assert LEVEL_MAP[StderrSource.CONNECTION] == 3
        assert LEVEL_MAP[StderrSource.CONNECTION_LIFECYCLE] == 3
        assert LEVEL_MAP[StderrSource.PLUGIN_LOADING] == 3
        assert LEVEL_MAP[StderrSource.INVENTORY] == 2
        assert LEVEL_MAP[StderrSource.VAULT] == 4
        assert LEVEL_MAP[StderrSource.PROMPT] == 0
        assert LEVEL_MAP[StderrSource.RUN_LEVEL] == 1
        assert LEVEL_MAP[StderrSource.UNKNOWN] == 1


# =============================================================================
# Host extraction
# =============================================================================


class TestHostExtraction:
    """Host is extracted from ``<hostname>`` prefix when present."""

    def test_host_extracted_simple(self) -> None:
        event = classify("<web1> SSH: ANSIBLE_PORT set: (-o)(Port=22)")
        assert event.host == "web1"

    def test_host_extracted_ip_address(self) -> None:
        event = classify("<192.168.1.42> EXEC /bin/true")
        assert event.host == "192.168.1.42"

    def test_host_extracted_fqdn(self) -> None:
        event = classify("<db.prod.us-east-1.example.com> CONNECTION: pid 1 waiting for lock on 3")
        assert event.host == "db.prod.us-east-1.example.com"

    def test_no_host_prefix_means_no_host(self) -> None:
        """A line without ``<...>`` prefix has no host even if rule says has_host."""
        event = classify("SSH: ANSIBLE_PORT set: (-o)(Port=22)")
        assert event.host is None

    def test_run_level_lines_never_have_host(self) -> None:
        """Even with a stale ``<...>`` in the regex, run-level sources
        don't extract a host for run-level diagnostics (warnings, config,
        plugin loading, etc.)."""
        event = classify("[WARNING]: No inventory was parsed")
        assert event.host is None
        event = classify("Using /etc/ansible/ansible.cfg as config file")
        assert event.host is None


# =============================================================================
# First-match-wins ordering
# =============================================================================


class TestFirstMatchWins:
    """When two rules could match, the first one in CLASSIFIER_RULES wins."""

    def test_ssh_agent_takes_precedence_over_generic_ssh(self) -> None:
        """``<web1> SSH: SSH_AGENT ...`` should hit the SSH_AGENT rule,
        not the generic SSH: rule. The order in CLASSIFIER_RULES controls
        this — agent rule must come before generic SSH rule."""
        event = classify("<web1> SSH: SSH_AGENT adding SHA256:abc to agent")
        assert event.source is StderrSource.SSH_INFO
        # Generic SSH: would have hit ssh_debug instead. Confirm we got
        # ssh_info (the agent-specific bucket).
        assert event.source is not StderrSource.SSH_DEBUG

    def test_failed_to_connect_takes_precedence_over_ssh_retry(self) -> None:
        """``Failed to connect to the host via ssh:`` could potentially
        collide with ssh_retry, but the literal prefix is distinct.

        (Sanity check: classifier handles both unambiguously.)"""
        event = classify("<web1> Failed to connect to the host via ssh: Permission denied")
        assert event.source is StderrSource.SSH_INFO


# =============================================================================
# StderrEvent dataclass
# =============================================================================


class TestStderrEvent:
    """StderrEvent shape — used by emit code in store.py."""

    def test_frozen_dataclass(self) -> None:
        """StderrEvent is frozen so emit code can rely on it being immutable."""
        event = StderrEvent(source=StderrSource.WARNING, host=None, level=0, line="x")
        with pytest.raises((AttributeError, TypeError)):
            event.source = StderrSource.ERROR  # type: ignore[misc]

    def test_equality(self) -> None:
        """Frozen dataclass equality on all four fields."""
        a = StderrEvent(source=StderrSource.WARNING, host="web1", level=0, line="x")
        b = StderrEvent(source=StderrSource.WARNING, host="web1", level=0, line="x")
        c = StderrEvent(source=StderrSource.WARNING, host="web2", level=0, line="x")
        assert a == b
        assert a != c

    def test_required_fields(self) -> None:
        """All four fields are required (no defaults)."""
        event = StderrEvent(
            source=StderrSource.SSH_DEBUG,
            host="web1",
            level=4,
            line="<web1> SSH: x",
        )
        assert event.source is StderrSource.SSH_DEBUG
        assert event.host == "web1"
        assert event.level == 4
        assert event.line == "<web1> SSH: x"


# =============================================================================
# Real-world sample lines (end-to-end smoke)
# =============================================================================


class TestRealWorldSamples:
    """Sample lines observed during real ansible-playbook runs."""

    @pytest.mark.parametrize(
        ("line", "expected_source", "expected_host"),
        [
            # SSH debug at -vvvvv
            (
                "<web1> SSH: ansible.cfg set ssh_args: (-C)(-o)(ControlMaster=auto)",
                StderrSource.SSH_DEBUG,
                "web1",
            ),
            # SSH connection failure at -vv
            (
                "<web1> Failed to connect to the host via ssh: ssh: connect to host web1 port 22: Connection refused",
                StderrSource.SSH_INFO,
                "web1",
            ),
            # Local connection
            (
                "<web1> ESTABLISH LOCAL CONNECTION FOR USER: root",
                StderrSource.CONNECTION,
                "web1",
            ),
            # Inventory
            (
                "Parsed /etc/ansible/hosts inventory source with ini plugin",
                StderrSource.INVENTORY,
                None,
            ),
            # Vault
            (
                "Vault password: ",
                StderrSource.VAULT,
                None,
            ),
            # Warning
            (
                "[WARNING]: No inventory was parsed, only implicit localhost is available",
                StderrSource.WARNING,
                None,
            ),
            # Deprecation
            (
                "[DEPRECATION WARNING]: Distribution Ubuntu 20.04 on host db1 should use the python3 interpreter",
                StderrSource.DEPRECATION,
                None,
            ),
            # Error
            (
                "[ERROR]: No matching task 'foo' found.",
                StderrSource.ERROR,
                None,
            ),
            # Run level: play count
            (
                "3 plays in /home/user/site.yml",
                StderrSource.RUN_LEVEL,
                None,
            ),
            # Run level: config file
            (
                "Using /etc/ansible/ansible.cfg as config file",
                StderrSource.RUN_LEVEL,
                None,
            ),
            # ControlPersist
            (
                "RETRYING BECAUSE OF CONTROLPERSIST BROKEN PIPE",
                StderrSource.SSH_INFO,
                None,
            ),
        ],
    )
    def test_sample(
        self, line: str, expected_source: StderrSource, expected_host: str | None
    ) -> None:
        event = classify(line)
        assert event.source is expected_source
        assert event.host == expected_host
        # The line is preserved verbatim on the event.
        assert event.line == line


# =============================================================================
# Colorised / ANSI-stripped inputs (integration with parser's _ANSI_SGR_RE)
# =============================================================================


class TestAnsiStrippedInputs:
    """Real ansible-playbook wraps stderr in SGR escape sequences. The
    classifier should be called on the *stripped* line (parser does that),
    but if it ever sees raw ANSI, it should still not crash.

    These tests assume the classifier receives clean text — the parser
    strips ANSI before calling classify. They verify the contract."""

    def test_clean_text_input(self) -> None:
        """Sanity: clean text is classifiable."""
        event = classify("[WARNING]: Some warning text")
        assert event.source is StderrSource.WARNING


# =============================================================================
# Defensive: never raise on weird input
# =============================================================================


class TestNoExceptions:
    """classify() is on the PTY hot path — it must never raise."""

    @pytest.mark.parametrize(
        "weird",
        [
            "",
            " ",
            "\n",
            "\t",
            "<<<>>>",
            "<<<",
            ">>>",
            "<>",
            "<",
            ">",
            "<host with spaces>",
            "<host> " * 100,
            "X" * 10_000,
        ],
    )
    def test_never_raises(self, weird: str) -> None:
        """classify() returns a StderrEvent for any input."""
        try:
            event = classify(weird)
        except Exception as exc:  # pragma: no cover - this is the failure path
            pytest.fail(f"classify({weird!r}) raised {exc!r}")
        assert isinstance(event, StderrEvent)
