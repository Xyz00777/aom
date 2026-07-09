# Status Bar Elements

> 27 nodes · cohesion 0.09

## Key Concepts

- **sanitize_string()** (17 connections) — `src/ansible_aom/core/redaction.py`
- **TestSanitizeStringLayer3Unchanged** (6 connections) — `tests/unit/test_redaction_layer4.py`
- **TestURLCredentialSanitization** (6 connections) — `tests/unit/test_redaction.py`
- **TestCLICredentialSanitization** (5 connections) — `tests/unit/test_redaction.py`
- **TestConfigCustomPatterns** (5 connections) — `tests/unit/test_redaction.py`
- **.test_cli_credentials_redacted()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_variant_formats()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_custom_pattern_redacts_matching_strings()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_multiple_custom_patterns()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_url_credentials_redacted()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_url_encoded_password()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_url_without_credentials_unchanged()** (4 connections) — `tests/unit/test_redaction.py`
- **.test_cli_password_sanitized()** (3 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_custom_patterns_applied_to_strings()** (3 connections) — `tests/unit/test_redaction_layer4.py`
- **.test_url_credentials_sanitized()** (3 connections) — `tests/unit/test_redaction_layer4.py`
- **Sanitize credentials in a single string (Layer 3).      Applies in order:     1.** (1 connections) — `src/ansible_aom/core/redaction.py`
- **URL/CLI string sanitization is independent of the key-match rewrite.** (1 connections) — `tests/unit/test_redaction_layer4.py`
- **Tests for TC-160: URL credential sanitization.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-160: URL credentials are sanitized.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-160 edge case: URL-encoded passwords.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-160 edge: URLs without credentials remain unchanged.** (1 connections) — `tests/unit/test_redaction.py`
- **Tests for TC-161: CLI argument credential sanitization.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-161: CLI credentials are sanitized.** (1 connections) — `tests/unit/test_redaction.py`
- **TC-161 edge case: Variant CLI formats.** (1 connections) — `tests/unit/test_redaction.py`
- **Tests for TC-173: Config custom_patterns for string sanitization.** (1 connections) — `tests/unit/test_redaction.py`
- *... and 2 more nodes in this community*

## Relationships

- [Warnings Display Config](Warnings_Display_Config.md) (7 shared connections)
- [Inspect TUI Widget Data](Inspect_TUI_Widget_Data.md) (5 shared connections)
- [Run State Summary Panel](Run_State_Summary_Panel.md) (4 shared connections)
- [Timestamp Timezone Formatting](Timestamp_Timezone_Formatting.md) (3 shared connections)
- [Summary Panel Widget](Summary_Panel_Widget.md) (2 shared connections)
- [Rerun Round Trip Tests](Rerun_Round_Trip_Tests.md) (1 shared connections)
- [TUI Tree View Tests](TUI_Tree_View_Tests.md) (1 shared connections)
- [Community 463](Community_463.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/redaction.py`
- `tests/unit/test_redaction.py`
- `tests/unit/test_redaction_layer4.py`

## Audit Trail

- EXTRACTED: 61 (69%)
- INFERRED: 27 (31%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*