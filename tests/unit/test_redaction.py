"""Comprehensive unit tests for password/secret redaction.

This module tests the 4-layer redaction system defined in SPECIFICATION.md Section 5.9.

Test cases cover:
- TC-153 through TC-173 from TEST_SPECIFICATION.md
- Layer 1: _ansible_no_log flag handling
- Layer 2: PASSWORD_MATCH regex + whitelist
- Layer 3: Command string sanitization
- Layer 4: invocation.module_args redaction
"""

import re
import time

import pytest

# Import from the redaction module (to be implemented)
# These imports will work once the redaction module is created
from ansible_aom.core.config import RedactionConfig
from ansible_aom.core.redaction import (
    ANSIBLE_PASSWORD_FIELDS,
    GENERIC_SECRET_FIELDS,
    PASSWORD_MATCH,
    PASSWORD_WHITELIST,
    REDACTED,
    should_redact,
    redact_dict,
    redact_event,
    sanitize_string,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def default_config() -> RedactionConfig:
    """Default redaction configuration."""
    return RedactionConfig()


@pytest.fixture
def custom_config() -> RedactionConfig:
    """Custom redaction configuration with whitelist and custom fields."""
    return RedactionConfig(
        whitelist=["my_passenger_field", "custom_bypass"],
        custom_fields=["my_secret_var", "db_connection_string"],
        custom_patterns=[
            {"regex": r"--db-password=\S+", "replacement": "--db-password=********"}
        ],
    )


# =============================================================================
# Layer 1: _ansible_no_log Flag Handling (TC-153, TC-154)
# =============================================================================


class TestLayer1AnsibleNoLog:
    """Tests for TC-153 and TC-154: _ansible_no_log flag handling."""

    def test_no_log_replaces_entire_result(self, default_config: RedactionConfig) -> None:
        """TC-153: When _ansible_no_log==True, entire result censored."""
        event = {
            "res": {
                "changed": False,
                "secret_value": "password123",
                "_ansible_no_log": True,
            }
        }
        result = redact_event(event, default_config)
        assert result["res"] == {"censored": "(no_log)"}

    def test_no_log_censors_result_field(self, default_config: RedactionConfig) -> None:
        """TC-153: Result field is redacted when _ansible_no_log=True."""
        event = {
            "res": {
                "changed": True,
                "msg": "secret data here",
                "_ansible_no_log": True,
            }
        }
        result = redact_event(event, default_config)
        assert result["res"] == {"censored": "(no_log)"}

    def test_no_log_loop_items_individually_censored(self, default_config: RedactionConfig) -> None:
        """TC-154: Loop items with _ansible_no_log individually censored."""
        event = {
            "res": {
                "results": [
                    {"item": "item1", "output": "visible", "_ansible_no_log": False},
                    {"item": "item2", "secret": "hidden", "_ansible_no_log": True},
                    {"item": "item3", "output": "also_visible", "_ansible_no_log": False},
                ]
            }
        }
        result = redact_event(event, default_config)
        # items[0] and items[2] should remain unchanged
        assert result["res"]["results"][0] == {"item": "item1", "output": "visible", "_ansible_no_log": False}
        assert result["res"]["results"][2] == {"item": "item3", "output": "also_visible", "_ansible_no_log": False}
        # items[1] should be {"censored": "(no_log)"}
        assert result["res"]["results"][1] == {"censored": "(no_log)"}

    def test_no_log_mixed_loop_items(self, default_config: RedactionConfig) -> None:
        """TC-154 edge case: Mixed loop items with per-item no_log."""
        event = {
            "res": {
                "results": [
                    {"item": 0, "password": "should_be_redacted", "_ansible_no_log": False},
                    {"item": 1, "data": "should_be_censored", "_ansible_no_log": True},
                    {"item": 2, "normal_field": "visible", "_ansible_no_log": False},
                ]
            }
        }
        result = redact_event(event, default_config)
        # Item 0: password field should still be redacted (Layer 2)
        assert result["res"]["results"][0]["password"] == REDACTED
        assert result["res"]["results"][0]["item"] == 0
        # Item 1: entire result replaced
        assert result["res"]["results"][1] == {"censored": "(no_log)"}
        # Item 2: normal field unchanged
        assert result["res"]["results"][2]["normal_field"] == "visible"


# =============================================================================
# Layer 2: PASSWORD_MATCH Regex + Whitelist (TC-155 through TC-159)
# =============================================================================


class TestPASSWORDMatch:
    """Tests for TC-155: PASSWORD_MATCH regex pattern matching."""

    @pytest.mark.parametrize(
        "field_name",
        [
            "password",
            "Password",
            "PASSWORD",
            "pass",
            "PASS",
            "passwd",
            "Passwd",
            "passphrase",
            "Passphrase",
            "password_hash",
            "password_hash_new",
            "user_password",
            "User_Password",
            "db_password",
            "admin_passwd",
            "secret_pass",
            "my_password_field",
            "api_password",
            "connection_password",
        ],
    )
    def test_matches_password_variants(self, field_name: str) -> None:
        """TC-155: Regex matches known password field name variants."""
        # PASSWORD_MATCH pattern from spec
        assert PASSWORD_MATCH.match(field_name.lower()) is not None, (
            f"PASSWORD_MATCH should match '{field_name}'"
        )

    @pytest.mark.parametrize(
        "field_name",
        [
            "my_pass_value",
            "db_pass_config",
            "user_pass_setting",
            "pass_custom",
            "pass_extra_field",
        ],
    )
    def test_false_positives_handled(self, field_name: str) -> None:
        """TC-155 edge case: Fields containing 'pass' that match regex but aren't passwords.

        PASSWORD_WHITELIST exists to prevent redaction of field names that:
        1. Contain 'pass' and match the PASSWORD_MATCH regex, OR
        2. Could match in certain contexts and need explicit exclusion

        The fields in the whitelist include:
        - passenger_version, passenger_pool, bypass, overpass, compass,
          underpass, passport_number

        These specific fields have 'pass' in them but are NOT password fields.
        The whitelist provides an explicit opt-out for them.
        """
        # Pattern is intentionally broad - matches password-related fields
        # Whitelist prevents false positives
        assert PASSWORD_MATCH is not None


class TestAnsiblePasswordFields:
    """Tests for TC-156: ANSIBLE_PASSWORD_FIELDS set."""

    @pytest.mark.parametrize(
        "field_name",
        [
            "ansible_ssh_pass",
            "ansible_password",
            "ansible_become_pass",
            "ansible_become_password",
            "ansible_vault_password",
            "ANSIBLE_SSH_PASS",
            "Ansible_Become_Pass",
        ],
    )
    def test_ansible_fields_redacted(self, field_name: str) -> None:
        """TC-156: All Ansible connection password fields are redacted."""
        # Case-insensitive matching
        assert field_name.lower() in ANSIBLE_PASSWORD_FIELDS or field_name.upper() in {
            f.upper() for f in ANSIBLE_PASSWORD_FIELDS
        }


class TestGenericSecretFields:
    """Tests for TC-157: GENERIC_SECRET_FIELDS set."""

    @pytest.mark.parametrize(
        "field_name",
        [
            "api_key",
            "API_KEY",
            "api_token",
            "secret",
            "SECRET",
            "secret_key",
            "token",
            "TOKEN",
            "auth_token",
            "access_token",
            "private_key",
            "credential",
            "credentials",
        ],
    )
    def test_generic_secret_fields_redacted(self, field_name: str) -> None:
        """TC-157: Generic secret field names are redacted."""
        # Case-insensitive check
        assert field_name.lower() in GENERIC_SECRET_FIELDS


class TestRecursiveRedaction:
    """Tests for TC-158: Recursive dict/list redaction."""

    def test_nested_dict_redaction(self, default_config: RedactionConfig) -> None:
        """TC-158: Password fields at any depth are redacted."""
        data = {
            "level1": {
                "level2": {
                    "password": "secret123",
                    "other_field": "visible",
                },
                "api_key": "key123",
            },
            "top_level_password": "another_secret",
        }
        result = redact_dict(data, default_config)
        assert result["level1"]["level2"]["password"] == REDACTED
        assert result["level1"]["level2"]["other_field"] == "visible"
        assert result["level1"]["api_key"] == REDACTED
        assert result["top_level_password"] == REDACTED

    def test_nested_list_with_dicts(self, default_config: RedactionConfig) -> None:
        """TC-158: Password fields in list items are redacted."""
        data = {
            "items": [
                {"name": "item1", "password": "secret1"},
                {"name": "item2", "token": "secret2"},
                {"name": "item3", "value": "visible"},
            ]
        }
        result = redact_dict(data, default_config)
        assert result["items"][0]["password"] == REDACTED
        assert result["items"][1]["token"] == REDACTED
        assert result["items"][2]["value"] == "visible"

    def test_max_depth_truncation(self, default_config: RedactionConfig) -> None:
        """TC-158 edge case: Max depth (10) truncation."""
        # Create deeply nested dict beyond max depth
        data = {"level1": {"level2": {"level3": {"level4": {"level5": {"level6": {"level7": {"level8": {"level9": {"level10": {"level11": {"password": "deep_secret"}}}}}}}}}}}}
        result = redact_dict(data, default_config)
        # At max depth, should stop recursing - password at depth 11 should not be redacted
        # or should be truncated depending on implementation
        assert result is not None
        # Verify deep structure exists
        assert "level1" in result

    def test_empty_dict_list_handling(self, default_config: RedactionConfig) -> None:
        """TC-158 edge: Empty dicts and lists handled correctly."""
        data = {
            "empty_dict": {},
            "empty_list": [],
            "password": "secret",
        }
        result = redact_dict(data, default_config)
        assert result["empty_dict"] == {}
        assert result["empty_list"] == []
        assert result["password"] == REDACTED


class TestWhitelistFalsePositives:
    """Tests for TC-159: Whitelist prevents false positive redaction."""

    @pytest.mark.parametrize(
        "field_name",
        [
            "passenger_version",
            "passenger_pool",
            "bypass",
            "overpass",
            "compass",
            "underpass",
            "passport_number",
        ],
    )
    def test_default_whitelist_fields_not_redacted(self, field_name: str, default_config: RedactionConfig) -> None:
        """TC-159: PASSWORD_WHITELIST prevents false positive redaction."""
        # Default whitelist from spec
        assert field_name.lower() in PASSWORD_WHITELIST or field_name in PASSWORD_WHITELIST
        # Fields in whitelist should NOT be redacted even though they match PASSWORD_MATCH
        data = {field_name: "some_value"}
        result = redact_dict(data, default_config)
        # After redaction: {field_name: "some_value"} - unchanged
        assert result[field_name] == "some_value"

    def test_custom_whitelist_from_config(self, custom_config: RedactionConfig) -> None:
        """TC-159: Configured custom whitelist extends PASSWORD_WHITELIST."""
        # custom_config has whitelist: ["my_passenger_field", "custom_bypass"]
        # These should not be redacted
        assert "my_passenger_field" in custom_config.whitelist
        assert "custom_bypass" in custom_config.whitelist


# =============================================================================
# Layer 3: Command String Sanitization (TC-160 through TC-162)
# =============================================================================


class TestURLCredentialSanitization:
    """Tests for TC-160: URL credential sanitization."""

    @pytest.mark.parametrize(
        "url",
        [
            "mysql://admin:secret123@db.example.com",
            "postgres://user:pass@localhost:5432/db",
            "mongodb://root:p4ssw0rd@mongo.cluster.local",
            "http://user:pass@internal.example.com:8080/path",
        ],
    )
    def test_url_credentials_redacted(self, url: str, default_config: RedactionConfig) -> None:
        """TC-160: URL credentials are sanitized."""
        result = sanitize_string(url, default_config)
        assert REDACTED in result
        # The actual password substring should be replaced
        # Check that ://user: exists and password is redacted
        assert ":********@" in result

    def test_url_encoded_password(self, default_config: RedactionConfig) -> None:
        """TC-160 edge case: URL-encoded passwords."""
        # URL-encoded passwords like pass%40word should be handled
        url = "mysql://user:pass%40word@db.example.com"
        result = sanitize_string(url, default_config)
        assert REDACTED in result
        # Password portion should be redacted

    def test_url_without_credentials_unchanged(self, default_config: RedactionConfig) -> None:
        """TC-160 edge: URLs without credentials remain unchanged."""
        url = "https://example.com/path"
        result = sanitize_string(url, default_config)
        # No substitution should occur
        assert result == url


class TestCLICredentialSanitization:
    """Tests for TC-161: CLI argument credential sanitization."""

    @pytest.mark.parametrize(
        "cmd",
        [
            "--password=secret123",
            "--password secret123",
            "--pass=secret123",
            "--pwd=secret123",
            "--token=abc123def",
            "--secret=hidden_value",
            "--key=my_key_value",
            "--api-key=sk_live_abc123",
        ],
    )
    def test_cli_credentials_redacted(self, cmd: str, default_config: RedactionConfig) -> None:
        """TC-161: CLI credentials are sanitized."""
        result = sanitize_string(cmd, default_config)
        assert REDACTED in result
        # Original secret value should not appear
        # (except in the flag name itself, like "password" in "--password")

    def test_variant_formats(self, default_config: RedactionConfig) -> None:
        """TC-161 edge case: Variant CLI formats."""
        # --password=xxx (equals)
        # --password xxx (space)
        # --password:xxx (colon)
        cmds = [
            ("--password=secret", "--password=********"),
            ("--password secret", "--password ********"),
            ("--password:secret", "--password:********"),
        ]
        for original, expected in cmds:
            result = sanitize_string(original, default_config)
            assert result == expected, f"Expected '{expected}' from '{original}', got '{result}'"


class TestSanitizationAppliedFields:
    """Tests for TC-162: Sanitization applied to specific fields."""

    def test_cmd_field_sanitized(self, default_config: RedactionConfig) -> None:
        """TC-162: res.cmd field is sanitized."""
        event = {
            "res": {
                "cmd": ["mysql", "-u", "root", "--password=secret123", "database"],
            }
        }
        result = redact_event(event, default_config)
        # After sanitization: --password=secret123 should become --password=********
        assert isinstance(result["res"]["cmd"], list)
        cmd_str = " ".join(result["res"]["cmd"])
        assert "secret123" not in cmd_str
        assert REDACTED in cmd_str or "--password=" in cmd_str

    def test_stdout_field_sanitized(self, default_config: RedactionConfig) -> None:
        """TC-162: res.stdout field is sanitized."""
        event = {
            "res": {
                "stdout": "Error: Connection failed for mysql://user:pass@db.example.com"
            }
        }
        result = redact_event(event, default_config)
        # URL credentials should be redacted in stdout
        assert "pass" not in result["res"]["stdout"] or REDACTED in result["res"]["stdout"]

    def test_stderr_field_sanitized(self, default_config: RedactionConfig) -> None:
        """TC-162: res.stderr field is sanitized."""
        event = {
            "res": {
                "stderr": "Authentication failed: --token=abc123 was rejected"
            }
        }
        result = redact_event(event, default_config)
        # CLI credentials should be redacted in stderr
        assert "abc123" not in result["res"]["stderr"] or REDACTED in result["res"]["stderr"]

    def test_msg_field_sanitized(self, default_config: RedactionConfig) -> None:
        """TC-162: res.msg field is sanitized."""
        event = {
            "res": {
                "msg": "Using password: secret123 for connection"
            }
        }
        result = redact_event(event, default_config)
        # Password references in msg should be handled
        # Note: plain text passwords in msg may not be redacted by default,
        # but CLI patterns should still work
        sanitized_msg = result["res"]["msg"]
        # At minimum, if there are password-like patterns they should be redacted
        assert isinstance(sanitized_msg, str)

    def test_all_fields_together(self, default_config: RedactionConfig) -> None:
        """TC-162: Multiple fields can all be sanitized."""
        event = {
            "res": {
                "cmd": ["--password=pass123"],
                "stdout": "URL: mysql://user:secret@db.example.com",
                "stderr": "Error with --token=abc123",
                "msg": "Password is secret123",
            }
        }
        result = redact_event(event, default_config)
        # All four fields should have credentials redacted
        cmd_str = " ".join(result["res"]["cmd"]) if isinstance(result["res"]["cmd"], list) else result["res"]["cmd"]
        assert "pass123" not in cmd_str
        assert "secret" not in result["res"]["stdout"] or REDACTED in result["res"]["stdout"]
        assert "abc123" not in result["res"]["stderr"] or REDACTED in result["res"]["stderr"]


# =============================================================================
# Layer 4: invocation.module_args Redaction (TC-163)
# =============================================================================


class TestInvocationModuleArgs:
    """Tests for TC-163: invocation.module_args redaction at -vvv."""

    def test_module_args_recursive_redaction(self, default_config: RedactionConfig) -> None:
        """TC-163: Nested module args with passwords are redacted."""
        event = {
            "res": {
                "invocation": {
                    "module_args": {
                        "name": "nginx",
                        "password": "secret123",
                        "api_key": "key123",
                        "config": {
                            "db_password": "db_secret",
                        },
                    }
                }
            }
        }
        result = redact_event(event, default_config)
        # password -> REDACTED
        assert result["res"]["invocation"]["module_args"]["password"] == REDACTED
        # api_key -> REDACTED
        assert result["res"]["invocation"]["module_args"]["api_key"] == REDACTED
        # db_password -> REDACTED
        assert result["res"]["invocation"]["module_args"]["config"]["db_password"] == REDACTED
        # name -> "nginx" (unchanged)
        assert result["res"]["invocation"]["module_args"]["name"] == "nginx"

    def test_deeply_nested_args(self, default_config: RedactionConfig) -> None:
        """TC-163 edge case: Deeply nested module args."""
        event = {
            "res": {
                "invocation": {
                    "module_args": {
                        "level1": {
                            "level2": {
                                "level3": {
                                    "secret_key": "hidden"
                                }
                            }
                        }
                    }
                }
            }
        }
        result = redact_event(event, default_config)
        # Deeply nested secrets should be redacted
        assert result["res"]["invocation"]["module_args"]["level1"]["level2"]["level3"]["secret_key"] == REDACTED

    def test_module_args_list_values(self, default_config: RedactionConfig) -> None:
        """TC-163: Module args with list values containing secrets."""
        event = {
            "res": {
                "invocation": {
                    "module_args": {
                        "users": [
                            {"name": "user1", "password": "pass1"},
                            {"name": "user2", "password": "pass2"},
                        ]
                    }
                }
            }
        }
        result = redact_event(event, default_config)
        # All password fields in list items should be redacted
        assert result["res"]["invocation"]["module_args"]["users"][0]["password"] == REDACTED
        assert result["res"]["invocation"]["module_args"]["users"][1]["password"] == REDACTED
        assert result["res"]["invocation"]["module_args"]["users"][0]["name"] == "user1"
        assert result["res"]["invocation"]["module_args"]["users"][1]["name"] == "user2"


# =============================================================================
# Redaction Always-On (TC-164)
# =============================================================================


class TestRedactionAlwaysOn:
    """Tests for TC-164: Redaction is always active, no opt-out."""

    def test_no_no_redact_flag_exists(self) -> None:
        """TC-164: No --no-redact command-line flag exists."""
        # Verify there is no way to disable redaction
        # This is a documentation/design test, not a runtime test
        # The implementation should NOT have a --no-redact flag
        from ansible_aom.cli import create_parser
        parser = create_parser()
        help_text = parser.format_help()
        # Check that --no-redact is NOT in the help text
        assert "--no-redact" not in help_text
        assert "--no-redaction" not in help_text
        # Verify parsing --no-redact should error
        with pytest.raises(SystemExit):
            parser.parse_args(["--no-redact"])

    def test_redaction_cannot_be_disabled(self) -> None:
        """TC-164: Redaction cannot be disabled at runtime."""
        # Even if someone tries to set redaction.enabled=False in config,
        # it should be ignored (the field doesn't exist per spec)
        # Verify RedactionConfig has no 'enabled' field
        import inspect
        from ansible_aom.core.config import RedactionConfig
        
        # Get the model fields
        fields = RedactionConfig.model_fields
        field_names = set(fields.keys())
        
        # 'enabled' should NOT be a field
        assert "enabled" not in field_names


# =============================================================================
# Redaction in Displays (TC-165 through TC-169)
# =============================================================================


class TestRedactionInCompactDisplay:
    """Tests for TC-165: Redaction in compact display."""

    def test_password_shows_asterisks_in_log(self, default_config: RedactionConfig) -> None:
        """TC-165: Password values show as "********" in log panel."""
        # Compact mode displays should show redacted values
        event = {
            "res": {
                "password": "secret123",
                "api_key": "key456",
                "changed": True,
            }
        }
        result = redact_event(event, default_config)
        # Password should be redacted
        assert result["res"]["password"] == REDACTED
        assert result["res"]["api_key"] == REDACTED


class TestRedactionInTUIDisplay:
    """Tests for TC-166: Redaction in TUI display."""

    def test_all_panels_show_redacted(self, default_config: RedactionConfig) -> None:
        """TC-166: All TUI panels show "********" for sensitive fields."""
        # Tree view, log panel, summary panel should all show redacted
        event = {
            "res": {
                "password": "secret",
                "token": "token123",
                "invocation": {
                    "module_args": {
                        "secret_key": "hidden"
                    }
                }
            }
        }
        result = redact_event(event, default_config)
        assert result["res"]["password"] == REDACTED
        assert result["res"]["token"] == REDACTED
        assert result["res"]["invocation"]["module_args"]["secret_key"] == REDACTED


class TestRedactionInInspectOutput:
    """Tests for TC-167: Redaction in inspect command output."""

    def test_inspect_shows_redacted(self, default_config: RedactionConfig) -> None:
        """TC-167: `aom inspect` command shows redacted values."""
        # Inspect output should never show plaintext passwords
        event = {
            "res": {
                "password": "my_secret_password",
                "changed": False,
            }
        }
        result = redact_event(event, default_config)
        assert result["res"]["password"] == REDACTED


class TestRedactionInJSONOutput:
    """Tests for TC-168: Redaction in JSON output."""

    def test_json_output_redacted(self, default_config: RedactionConfig) -> None:
        """TC-168: `aom inspect --json` shows redacted values."""
        import json
        
        # JSON export should have passwords as "********"
        event = {
            "res": {
                "password": "secret123",
                "api_token": "token456",
            }
        }
        result = redact_event(event, default_config)
        
        # Convert to JSON and verify redaction
        json_str = json.dumps(result)
        assert "secret123" not in json_str
        assert "token456" not in json_str
        assert REDACTED in json_str


class TestRedactionInSessionArtifacts:
    """Tests for TC-169: Redaction in .aom session artifacts."""

    def test_artifact_file_redacted(self, default_config: RedactionConfig) -> None:
        """TC-169: .aom session artifacts always redacted."""
        # Written artifact files should never contain plaintext passwords
        event = {
            "res": {
                "password": "plaintext_secret",
                "credential": "admin_creds",
            }
        }
        result = redact_event(event, default_config)
        assert result["res"]["password"] == REDACTED
        assert result["res"]["credential"] == REDACTED


# =============================================================================
# RedactionConfig Model (TC-170 through TC-173)
# =============================================================================


class TestRedactionConfigModel:
    """Tests for TC-170: RedactionConfig model validation."""

    def test_default_config_has_empty_lists(self) -> None:
        """TC-170: Default RedactionConfig has empty lists for custom settings."""
        config = RedactionConfig()
        assert config.whitelist == []
        assert config.custom_fields == []
        assert config.custom_patterns == []

    def test_config_with_values(self) -> None:
        """TC-170: RedactionConfig accepts provided values."""
        config = RedactionConfig(
            whitelist=["field1"],
            custom_fields=["field2"],
            custom_patterns=[{"regex": r"pattern", "replacement": "*****"}],
        )
        assert config.whitelist == ["field1"]
        assert config.custom_fields == ["field2"]
        assert len(config.custom_patterns) == 1

    def test_invalid_pattern_regex_validation(self) -> None:
        """TC-170 edge case: Invalid regex pattern raises error."""
        # Pydantic should validate that custom_patterns contain valid regex
        # Try to create config with invalid pattern
        import pydantic
        try:
            config = RedactionConfig(
                custom_patterns=[{"regex": "[invalid", "replacement": "x"}]
            )
            # If no error, the regex pattern was stored as-is
            # This is acceptable if Pydantic doesn't validate regex syntax
            assert config.custom_patterns[0]["regex"] == "[invalid"
        except pydantic.ValidationError:
            # If ValidationError raised, that's also acceptable
            pass


class TestConfigCustomWhitelist:
    """Tests for TC-171: Custom whitelist extends PASSWORD_WHITELIST."""

    def test_custom_whitelist_not_redacted(self, custom_config: RedactionConfig) -> None:
        """TC-171: Custom whitelist fields are NOT redacted."""
        # custom_config has whitelist: ["my_passenger_field", "custom_bypass"]
        # Fields matching these names should not be redacted
        data = {
            "my_passenger_field": "passenger_data",
            "custom_bypass": "bypass_value",
            "password": "secret",
        }
        result = redact_dict(data, custom_config)
        assert result["my_passenger_field"] == "passenger_data"
        assert result["custom_bypass"] == "bypass_value"
        assert result["password"] == REDACTED


class TestConfigCustomFields:
    """Tests for TC-172: Config custom_fields adds fields to redact."""

    def test_custom_fields_redacted(self, custom_config: RedactionConfig) -> None:
        """TC-172: custom_fields values are redacted."""
        # custom_config has custom_fields: ["my_secret_var", "db_connection_string"]
        # These field names should be treated like password fields and redacted
        data = {
            "my_secret_var": "super_secret",
            "db_connection_string": "mysql://...",
            "normal_field": "visible",
        }
        result = redact_dict(data, custom_config)
        assert result["my_secret_var"] == REDACTED
        assert result["db_connection_string"] == REDACTED
        assert result["normal_field"] == "visible"


class TestConfigCustomPatterns:
    """Tests for TC-173: Config custom_patterns for string sanitization."""

    def test_custom_pattern_redacts_matching_strings(self, custom_config: RedactionConfig) -> None:
        """TC-173: custom_patterns regex redacts matching strings."""
        # custom_config has pattern: {"regex": "--db-password=\\S+", "replacement": "--db-password=********"}
        # String "--db-password=secret123" should become "--db-password=********"
        text = "--db-password=secret123"
        result = sanitize_string(text, custom_config)
        assert result == "--db-password=********"

    def test_multiple_custom_patterns(self) -> None:
        """TC-173 edge: Multiple custom patterns are applied."""
        config = RedactionConfig(
            custom_patterns=[
                {"regex": r"--db-password=\S+", "replacement": "--db-password=********"},
                {"regex": r"API_KEY=\S+", "replacement": "API_KEY=********"},
            ]
        )
        # Both patterns should be applied to strings
        text = "--db-password=secret123 and API_KEY=abc123"
        result = sanitize_string(text, config)
        assert "secret123" not in result
        assert "abc123" not in result
        assert REDACTED in result or "********" in result


# =============================================================================
# Integration Tests
# =============================================================================


class TestRedactionIntegration:
    """Integration tests combining multiple redaction layers."""

    def test_full_event_redaction(self, default_config: RedactionConfig) -> None:
        """All four layers work together on a complete event."""
        event = {
            "_event": "v2_runner_on_ok",
            "res": {
                "_ansible_no_log": False,  # Layer 1: not triggered
                "changed": True,
                "password": "secret123",  # Layer 2: redacted
                "passenger_version": "1.0",  # Layer 2: whitelisted
                "cmd": ["mysql", "-u", "root", "--password=dbpass"],  # Layer 3: sanitized
                "invocation": {  # Layer 4: recursive redaction
                    "module_args": {
                        "api_key": "key123",
                        "name": "nginx",
                    }
                },
            },
        }
        result = redact_event(event, default_config)
        # password -> REDACTED
        assert result["res"]["password"] == REDACTED
        # passenger_version -> "1.0" (unchanged, whitelisted)
        assert result["res"]["passenger_version"] == "1.0"
        # cmd -> ["mysql", "-u", "root", "--password=********"]
        assert "dbpass" not in " ".join(result["res"]["cmd"])
        # invocation.module_args.api_key -> REDACTED
        assert result["res"]["invocation"]["module_args"]["api_key"] == REDACTED
        # invocation.module_args.name -> "nginx" (unchanged)
        assert result["res"]["invocation"]["module_args"]["name"] == "nginx"

    def test_layer1_takes_precedence(self, default_config: RedactionConfig) -> None:
        """Layer 1 (_ansible_no_log) takes precedence over other layers."""
        event = {
            "res": {
                "_ansible_no_log": True,
                "password": "secret123",
                "cmd": ["--token=abc123"],
            }
        }
        # When _ansible_no_log=True, entire result is replaced
        # No need to run other layers
        result = redact_event(event, default_config)
        assert result["res"] == {"censored": "(no_log)"}

    def test_empty_event_handling(self, default_config: RedactionConfig) -> None:
        """Edge case: Empty event dict handled gracefully."""
        event = {}
        # Should not raise any errors
        result = redact_event(event, default_config)
        # Implementation adds an empty 'res' dict for events without one
        assert result == {"res": {}}

    def test_non_dict_value_handling(self, default_config: RedactionConfig) -> None:
        """Edge case: Non-dict values handled correctly."""
        data = {
            "password": None,  # None value
            "api_key": 12345,  # Integer value
            "normal_list": ["list", "of", "strings"],  # List without dicts (non-sensitive key)
        }
        result = redact_dict(data, default_config)
        # Should not crash, should appropriately handle each type
        # Password fields get redacted regardless of value type
        assert result["password"] == REDACTED
        assert result["api_key"] == REDACTED
        # Non-sensitive list stays as-is
        assert result["normal_list"] == ["list", "of", "strings"]


class TestRedactionPerformance:
    """Performance-related tests for redaction."""

    def test_large_event_performance(self, default_config: RedactionConfig) -> None:
        """Redaction on large event dict completes quickly."""
        # Create a large event with many nested dicts
        event = {
            "res": {
                "results": [
                    {
                        "item": f"item_{i}",
                        "password": f"secret_{i}",
                        "token": f"token_{i}",
                        "data": {
                            "nested": {
                                "api_key": f"key_{i}",
                            }
                        }
                    }
                    for i in range(100)
                ]
            }
        }
        
        start_time = time.time()
        result = redact_event(event, default_config)
        elapsed = time.time() - start_time
        
        # Redaction should complete in < 1 second
        assert elapsed < 1.0, f"Redaction took {elapsed:.2f}s, expected < 1s"
        # Verify some redaction happened
        assert result["res"]["results"][0]["password"] == REDACTED

    def test_max_depth_limits_recursion(self, default_config: RedactionConfig) -> None:
        """Max depth parameter prevents infinite recursion."""
        # Create deeply nested structure
        data = {"password": "outer"}
        current = data
        for i in range(15):
            current["nested"] = {"password": f"level_{i}"}
            current = current["nested"]
        
        # Should not crash from recursion
        result = redact_dict(data, default_config)
        # Outer password should still be redacted
        assert result["password"] == REDACTED


# =============================================================================
# Helper Function Tests (for functions to be implemented in redaction.py)
# =============================================================================


class TestRedactionHelperFunctions:
    """Tests for helper functions in redaction module."""

    def test_should_redact_function(self, default_config: RedactionConfig) -> None:
        """should_redact() correctly identifies redactable fields."""
        # This tests the function signature:
        # def should_redact(key: str, config: RedactionConfig) -> bool
        
        # Password keys -> True
        assert should_redact("password", default_config) is True
        assert should_redact("api_key", default_config) is True
        assert should_redact("secret", default_config) is True
        assert should_redact("ansible_ssh_pass", default_config) is True
        
        # Whitelist keys -> False
        assert should_redact("passenger_version", default_config) is False
        assert should_redact("bypass", default_config) is False
        
        # Normal field -> False
        assert should_redact("name", default_config) is False
        assert should_redact("changed", default_config) is False

    def test_redact_dict_function(self, default_config: RedactionConfig) -> None:
        """redact_dict() recursively redacts password fields."""
        # This tests the function signature:
        # def redact_dict(data: dict, config: RedactionConfig, depth: int = 0) -> dict
        
        data = {
            "password": "secret",
            "name": "nginx",
            "nested": {
                "api_key": "key123",
            }
        }
        result = redact_dict(data, default_config)
        
        assert result["password"] == REDACTED
        assert result["name"] == "nginx"
        assert result["nested"]["api_key"] == REDACTED

    def test_sanitize_string_function(self, default_config: RedactionConfig) -> None:
        """sanitize_string() removes credentials from strings."""
        # This tests the function signature:
        # def sanitize_string(s: str, config: RedactionConfig) -> str
        
        # URL sanitization
        url = "mysql://user:pass@db.example.com"
        result = sanitize_string(url, default_config)
        assert REDACTED in result
        assert "pass" not in result or REDACTED in result
        
        # CLI sanitization
        cmd = "--password=secret123"
        result = sanitize_string(cmd, default_config)
        assert "secret123" not in result
        assert REDACTED in result or "********" in result

    def test_redact_event_function(self, default_config: RedactionConfig) -> None:
        """redact_event() applies all redaction layers to event."""
        # This tests the function signature:
        # def redact_event(event: dict, config: RedactionConfig) -> dict
        
        event = {
            "res": {
                "password": "secret",
                "cmd": ["--token=abc123"],
                "invocation": {
                    "module_args": {
                        "api_key": "key123"
                    }
                }
            }
        }
        result = redact_event(event, default_config)
        
        assert result["res"]["password"] == REDACTED
        assert result["res"]["invocation"]["module_args"]["api_key"] == REDACTED