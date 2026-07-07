"""Unit tests for the QC-002 redaction rewrite (Phase 2 / Task 2.1).

This file pins the new Layer 4 contract:

- **Layer 1 (hard-coded, exact-match keys):** ``password``, ``vault_password``,
  ``api_key``, ``private_key``, ``token``, ``secret``, ``passwd``, ``ssh_pass``.
  These are matched by *exact* lowercased key, not by regex / value substring.
- **Layer 2 (user-config):** ``RedactionConfig.custom_fields`` (exact key) and
  ``RedactionConfig.custom_key_patterns`` (regex over keys).
- **Whitelist:** ``RedactionConfig.whitelist`` and the default
  ``DEFAULT_PASSPHRASE_WHITELIST`` (``passenger_version``, ``bypass``, ...)
  prevent false positives.

The redaction module recurses into dicts/lists by **KEY** — never by value
substring. That is the QC-002 bypass class fix: the old PASSWORD_MATCH regex
matched ``passenger_version`` (false positive on values) and was exploited
through nested structures where value-substring matching could leak secrets.
"""

from __future__ import annotations

import pytest

from ansible_aom.core.config import RedactionConfig
from ansible_aom.core.redaction import (
    DEFAULT_PASSPHRASE_WHITELIST,
    EXACT_MATCH_SECRET_KEYS,
    PASSWORD_WHITELIST,
    REDACTED,
    redact_dict,
    redact_event,
    sanitize_string,
    should_redact,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def default_config() -> RedactionConfig:
    """Default redaction config — no user overrides."""
    return RedactionConfig()


@pytest.fixture
def user_regex_config() -> RedactionConfig:
    """User-config with regex key patterns: ``*_password``, ``*_token``,
    ``*_secret`` are added (typical user extension to the exact-match set)."""
    return RedactionConfig(
        custom_key_patterns=[
            r".*_password$",
            r".*_token$",
            r".*_secret$",
            r".*_key$",
        ],
    )


# ---------------------------------------------------------------------------
# TestLayer1ExactMatchKeys — 8 cases
# ---------------------------------------------------------------------------


class TestLayer1ExactMatchKeys:
    """Layer 1: exact-match keys from QC-002 list are redacted."""

    @pytest.mark.parametrize(
        "key,value",
        [
            ("password", "hunter2"),
            ("Password", "hunter2"),
            ("PASSWORD", "hunter2"),
            ("vault_password", "vault"),
            ("api_key", "sk-1234"),
            ("private_key", "-----BEGIN RSA-----"),
            ("token", "ghp_abc"),
            ("secret", "shh"),
            ("passwd", "pw"),
            ("ssh_pass", "openssh"),
        ],
    )
    def test_qc002_exact_match_keys_redacted(
        self, key: str, value: str, default_config: RedactionConfig
    ) -> None:
        """QC-002: every exact-match key in the QC-002 list is redacted
        under the default config (no user opt-in required)."""
        event = {"res": {key: value}}
        result = redact_event(event, default_config)
        assert result["res"][key] == REDACTED, (
            f"Key '{key}' should be redacted by exact-match Layer 1; got '{result['res'][key]}'"
        )
        assert value not in str(result["res"][key])

    def test_qc002_exact_match_keys_frozenset_contents(self) -> None:
        """The exact-match set is exactly the QC-002 list — no more, no less.

        This locks the wire-format: changing this set is a breaking change
        for downstream tooling that reads the unredacted form via the API.
        """
        assert EXACT_MATCH_SECRET_KEYS == frozenset(
            {
                "password",
                "vault_password",
                "api_key",
                "private_key",
                "token",
                "secret",
                "passwd",
                "ssh_pass",
            }
        )

    def test_exact_match_is_case_insensitive_on_lookup(
        self, default_config: RedactionConfig
    ) -> None:
        """Uppercase / mixed-case keys still match via lower() comparison."""
        for variant in ("Password", "PASSWORD", "pAsSwOrD"):
            assert should_redact(variant, default_config) is True, (
                f"should_redact({variant!r}) must be True (case-insensitive)"
            )

    def test_exact_match_does_not_catch_suffix_or_prefix(
        self, default_config: RedactionConfig
    ) -> None:
        """QC-002 fix: ``top_level_password`` / ``password_hash`` are NOT
        auto-redacted. They require a user-config custom_key_pattern (Layer 2)
        or an explicit ``custom_fields`` entry. This is the bypass-class fix —
        the old PASSWORD_MATCH regex matched these and leaked via false
        negatives elsewhere."""
        for key in (
            "top_level_password",
            "password_hash",
            "password_hash_new",
            "user_password",
            "api_password",
            "my_password_field",
            "secret_pass",
            "passwordless",  # contains "pass" but no "password" semantics
        ):
            assert should_redact(key, default_config) is False, (
                f"Key '{key}' must NOT be redacted by Layer 1 (exact-match) "
                f"alone; the bypass class is closed only by exact-match."
            )


# ---------------------------------------------------------------------------
# TestLayer2UserConfig
# ---------------------------------------------------------------------------


class TestLayer2UserConfig:
    """Layer 2: user-config adds exact keys and regex patterns."""

    def test_custom_fields_extends_exact_match(self, default_config: RedactionConfig) -> None:
        """``RedactionConfig.custom_fields`` adds exact keys (case-insensitive)."""
        cfg = RedactionConfig(custom_fields=["my_secret_var", "db_string"])
        for key in ("my_secret_var", "My_Secret_Var", "db_string"):
            assert should_redact(key, cfg) is True
        # Default keys still work.
        assert should_redact("password", cfg) is True

    def test_custom_key_patterns_matches_suffix(self, user_regex_config: RedactionConfig) -> None:
        """User regex pattern ``.*_password$`` catches ``db_password`` etc."""
        for key in ("db_password", "root_password", "api_password"):
            assert should_redact(key, user_regex_config) is True, (
                f"User regex should redact '{key}'"
            )

    def test_custom_key_patterns_matches_token_suffix(
        self, user_regex_config: RedactionConfig
    ) -> None:
        """User regex pattern ``.*_token$`` catches ``auth_token`` etc."""
        for key in ("auth_token", "access_token", "refresh_token"):
            assert should_redact(key, user_regex_config) is True

    def test_custom_key_patterns_invalid_regex_skipped(
        self, default_config: RedactionConfig
    ) -> None:
        """Invalid regex in custom_key_patterns is silently skipped, not fatal.

        A bad pattern must not crash should_redact — degrade to no match.
        """
        cfg = RedactionConfig(custom_key_patterns=["[invalid", r"valid_\d+"])
        # Should not raise.
        assert should_redact("valid_42", cfg) is True
        assert should_redact("password", cfg) is True  # Layer 1 still applies.

    def test_layer2_does_not_rediscover_exact_match_keys(
        self, default_config: RedactionConfig
    ) -> None:
        """Layer 2 is *additive* — exact-match keys (Layer 1) work even when
        the user has no custom_key_patterns configured."""
        assert default_config.custom_key_patterns == []
        assert should_redact("password", default_config) is True
        assert should_redact("api_key", default_config) is True


# ---------------------------------------------------------------------------
# TestRecurseByKeyNotValue — the QC-002 bypass class fix
# ---------------------------------------------------------------------------


class TestRecurseByKeyNotValue:
    """The bypass class fix: redaction recurses by KEY, never by VALUE substring.

    The old code matched ``*_password`` *inside* string values (a value-substring
    match), which led to: (a) false positives on values that *happened* to
    contain "password", and (b) — more importantly — bypass opportunities where
    a secret value was placed in a field whose key did NOT contain "password",
    and the old PASSWORD_MATCH regex would not catch it.

    The new code matches *only on keys*. Values that happen to contain
    "password" in a non-secret field (e.g. ``description: "use password
    authentication"``) must NOT be redacted.
    """

    def test_value_substring_password_not_redacted(self, default_config: RedactionConfig) -> None:
        """A field named ``description`` whose value contains the literal
        substring ``password`` must NOT be redacted. The new model only
        inspects keys, never values."""
        event = {
            "res": {
                "description": "uses password authentication for the api",
                "msg": "please set a password and store it in vault",
            }
        }
        result = redact_event(event, default_config)
        assert result["res"]["description"] == "uses password authentication for the api"
        assert result["res"]["msg"] == "please set a password and store it in vault"

    def test_secret_in_value_under_safe_key_not_redacted(
        self, default_config: RedactionConfig
    ) -> None:
        """A value that *looks* like a secret (a GitHub PAT shape) under a
        non-secret key (e.g. ``comment``) is NOT redacted by Layer 1.

        This is a deliberate trade-off documented in QC-002: redaction is
        about *key* semantics, not *value* shape. The user opts in to
        value-shape detection via custom_patterns in sanitize_string.
        """
        event = {"res": {"comment": "deploy with token ghp_abcdef1234567890"}}
        result = redact_event(event, default_config)
        # The whole field is left as-is (Layer 1 only looks at keys).
        assert result["res"]["comment"] == "deploy with token ghp_abcdef1234567890"

    def test_dict_recursion_redacts_nested_exact_match_keys(
        self, default_config: RedactionConfig
    ) -> None:
        """Recursion by key: an exact-match key nested 5 levels deep is still
        caught (depth budget = 10)."""
        event = {
            "res": {
                "outer": {"level2": {"level3": {"level4": {"level5": {"api_key": "deep-secret"}}}}}
            }
        }
        result = redact_event(event, default_config)
        assert result["res"]["outer"]["level2"]["level3"]["level4"]["level5"]["api_key"] == REDACTED

    def test_list_recursion_redacts_dict_items(self, default_config: RedactionConfig) -> None:
        """Recursion by key into list-of-dict: each dict item is inspected
        by its own keys; matching keys are redacted."""
        event = {
            "res": {
                "items": [
                    {"name": "alpha", "password": "first"},
                    {"name": "beta", "token": "second"},
                    {"name": "gamma", "visible": "data"},
                ]
            }
        }
        result = redact_event(event, default_config)
        assert result["res"]["items"][0]["password"] == REDACTED
        assert result["res"]["items"][0]["name"] == "alpha"
        assert result["res"]["items"][1]["token"] == REDACTED
        assert result["res"]["items"][1]["name"] == "beta"
        assert result["res"]["items"][2]["visible"] == "data"

    def test_recursion_depth_bounded(self, default_config: RedactionConfig) -> None:
        """Depth budget prevents runaway recursion on malicious input."""
        nested: dict = {"password": "shallow"}
        cur = nested
        for _ in range(20):
            cur["n"] = {"password": "deep"}
            cur = cur["n"]
        # Must not crash; outer password is redacted, deep ones may be
        # truncated at the depth budget (implementation-defined, but no crash).
        result = redact_dict(nested, default_config)
        assert result["password"] == REDACTED


# ---------------------------------------------------------------------------
# TestWhitelistStillWorks
# ---------------------------------------------------------------------------


class TestWhitelistStillWorks:
    """Default passphrase-whitelist prevents false positives on
    ``passenger_version``, ``bypass`` etc. — the keys that historically
    matched the old PASSWORD_MATCH regex."""

    def test_passenger_version_not_redacted(self, default_config: RedactionConfig) -> None:
        event = {"res": {"passenger_version": "6.0.18"}}
        result = redact_event(event, default_config)
        assert result["res"]["passenger_version"] == "6.0.18"

    def test_bypass_not_redacted(self, default_config: RedactionConfig) -> None:
        event = {"res": {"bypass": "true"}}
        result = redact_event(event, default_config)
        assert result["res"]["bypass"] == "true"

    def test_default_passthrough_whitelist_intact(self) -> None:
        """Lock the default whitelist contents — the bypass class
        mitigation depends on this set staying frozen."""
        assert DEFAULT_PASSPHRASE_WHITELIST == frozenset(
            {
                "passenger_version",
                "passenger_pool",
                "bypass",
                "overpass",
                "compass",
                "underpass",
                "passport_number",
            }
        )
        assert PASSWORD_WHITELIST == DEFAULT_PASSPHRASE_WHITELIST

    def test_config_whitelist_extends_defaults(self, default_config: RedactionConfig) -> None:
        """User-supplied ``whitelist`` is added to (not replacing) the
        default passphrase-whitelist."""
        cfg = RedactionConfig(whitelist=["my_bypass_field"])
        # Default still works.
        assert should_redact("passenger_version", cfg) is False
        # User's entry also works.
        assert should_redact("my_bypass_field", cfg) is False


# ---------------------------------------------------------------------------
# TestNoLogLayer0_StillWorks
# ---------------------------------------------------------------------------


class TestNoLogLayer0StillWorks:
    """Layer 0 (upstream ``_ansible_no_log``) takes precedence over Layers 1/2."""

    def test_no_log_replaces_entire_result(self, default_config: RedactionConfig) -> None:
        event = {
            "res": {
                "password": "visible-but-overridden",
                "token": "also-visible-but-overridden",
                "_ansible_no_log": True,
            }
        }
        result = redact_event(event, default_config)
        assert result["res"] == {"censored": "(no_log)"}

    def test_no_log_loop_item_censored(self, default_config: RedactionConfig) -> None:
        event = {
            "res": {
                "results": [
                    {"item": "a", "password": "should-redact", "_ansible_no_log": False},
                    {"item": "b", "_ansible_no_log": True},
                ]
            }
        }
        result = redact_event(event, default_config)
        # Item 0: password redacted (Layer 1), no_log=False so kept.
        assert result["res"]["results"][0]["password"] == REDACTED
        # Item 1: censored (Layer 0).
        assert result["res"]["results"][1] == {"censored": "(no_log)"}


# ---------------------------------------------------------------------------
# TestInvocationsLayer4_StaysConsistent
# ---------------------------------------------------------------------------


class TestInvocationsLayer4StaysConsistent:
    """``res.invocation.module_args`` is still redacted recursively."""

    def test_invocation_module_args_uses_layer1(self, default_config: RedactionConfig) -> None:
        event = {
            "res": {
                "invocation": {
                    "module_args": {
                        "name": "nginx",
                        "password": "secret",
                        "api_key": "key",
                    }
                }
            }
        }
        result = redact_event(event, default_config)
        assert result["res"]["invocation"]["module_args"]["password"] == REDACTED
        assert result["res"]["invocation"]["module_args"]["api_key"] == REDACTED
        assert result["res"]["invocation"]["module_args"]["name"] == "nginx"


# ---------------------------------------------------------------------------
# TestSanitizeStringLayer3_Unchanged
# ---------------------------------------------------------------------------


class TestSanitizeStringLayer3Unchanged:
    """URL/CLI string sanitization is independent of the key-match rewrite."""

    def test_url_credentials_sanitized(self, default_config: RedactionConfig) -> None:
        out = sanitize_string("mysql://admin:hunter2@db.example.com", default_config)
        assert "hunter2" not in out
        assert REDACTED in out
        assert ":********@" in out

    def test_cli_password_sanitized(self, default_config: RedactionConfig) -> None:
        out = sanitize_string("--password=hunter2 --user=root", default_config)
        assert "hunter2" not in out
        assert REDACTED in out

    def test_custom_patterns_applied_to_strings(self, default_config: RedactionConfig) -> None:
        cfg = RedactionConfig(
            custom_patterns=[{"regex": r"DB_PW=\S+", "replacement": "DB_PW=********"}]
        )
        out = sanitize_string("export DB_PW=hunter2", cfg)
        assert "hunter2" not in out
        assert "DB_PW=********" in out
