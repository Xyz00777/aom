"""Table-driven red-team fixture test for the QC-002 redaction rewrite.

This file loads ``tests/fixtures/redaction_bypass.jsonl`` and runs each row
through the redaction pipeline. Each row contains:

- ``case_id`` — stable identifier (e.g. ``RT-001``) used in the test name.
- ``category`` — group: ``exact_match_redact``, ``user_regex_redact``,
  ``false_positive_no_redact``, ``value_substring_no_redact``,
  ``whitelist_no_redact``, ``custom_fields_redact``, ``nested_redact``,
  ``whitelist_custom``.
- ``input`` — partial event dict passed to ``redact_event``.
- ``expected`` — what the redaction should produce.
- ``config`` — overrides applied to the default ``RedactionConfig``.

A failure in any row points to a redaction regression in that category. The
fixture is a deliberately adversarial corpus: real secrets, key look-alikes
(``secretary``, ``tokener``), value-substring traps, and whitelisted fields.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ansible_aom.core.config import RedactionConfig
from ansible_aom.core.redaction import REDACTED, redact_event

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "redaction_bypass.jsonl"


def _load_fixture() -> list[dict[str, Any]]:
    """Load and parse the red-team JSONL fixture."""
    cases: list[dict[str, Any]] = []
    with FIXTURE_PATH.open() as fh:
        for line_no, raw in enumerate(fh, start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise AssertionError(
                    f"Invalid JSON in red-team fixture at line {line_no}: {exc}"
                ) from exc
            cases.append(row)
    return cases


def _build_config(row: dict[str, Any]) -> RedactionConfig:
    """Build a RedactionConfig from the row's ``config`` field."""
    cfg = row.get("config") or {}
    return RedactionConfig(
        whitelist=list(cfg.get("whitelist", [])),
        custom_fields=list(cfg.get("custom_fields", [])),
        custom_key_patterns=list(cfg.get("custom_key_patterns", [])),
        custom_patterns=list(cfg.get("custom_patterns", [])),
    )


@pytest.fixture(scope="module")
def redteam_cases() -> list[dict[str, Any]]:
    """Module-scoped fixture: parse the JSONL once for the whole module."""
    return _load_fixture()


def _id_from_row(row: dict[str, Any]) -> str:
    return f"{row.get('case_id', '?')}[{row.get('category', '?')}]"


@pytest.mark.parametrize("row", _load_fixture(), ids=_id_from_row)
def test_redaction_redteam_row(row: dict[str, Any]) -> None:
    """Each fixture row is a full redaction contract test."""
    cfg = _build_config(row)
    input_event: dict[str, Any] = row["input"]
    expected: dict[str, Any] = row["expected"]

    actual = redact_event(input_event, cfg)
    assert actual == expected, (
        f"Case {row.get('case_id')} ({row.get('category')}) failed: "
        f"input={input_event!r}, expected={expected!r}, actual={actual!r}"
    )


def test_fixture_has_at_least_30_rows(redteam_cases: list[dict[str, Any]]) -> None:
    """Sanity: the red-team corpus must be a real corpus, not a stub."""
    assert len(redteam_cases) >= 30, f"Expected >= 30 red-team cases, got {len(redteam_cases)}"


def test_fixture_covers_required_categories(redteam_cases: list[dict[str, Any]]) -> None:
    """Sanity: the corpus must include at least the four QC-002 categories.

    - exact_match_redact: positive cases
    - false_positive_no_redact: bypass-class cases (the heart of the fix)
    - user_regex_redact: Layer 2 (user extension)
    - value_substring_no_redact: explicit value-bypass prevention
    """
    categories = {row.get("category") for row in redteam_cases}
    required = {
        "exact_match_redact",
        "false_positive_no_redact",
        "user_regex_redact",
        "value_substring_no_redact",
    }
    missing = required - categories
    assert not missing, f"Red-team fixture missing required categories: {missing}"


def test_fixture_does_not_leak_plaintext_secrets(
    redteam_cases: list[dict[str, Any]],
) -> None:
    """Defense-in-depth: every SHOULD_REDACT row must end with the literal
    ``REDACTED`` placeholder at the secret's value position. Catches a
    regression where exact-match keys are silently bypassed."""
    secret_values = {
        "hunter2",
        "v4ult",
        "sk_live_abc123",
        "p4ss",
        "openssh-pw",
        "p@ssw0rd",
        "ya29.a0AfH6SMB...",
        "GOCSPX-abc123",
        "AKIAIOSFODNN7EXAMPLE",
        "1//0gXXX",
        "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "ghp_abcdefghijklmnopqrstuvwxyz",
        "deep-secret",
        "t1",
        "t2",
        "hello",
        "postgres://...",
    }
    for row in redteam_cases:
        if row.get("category") not in {
            "exact_match_redact",
            "user_regex_redact",
            "custom_fields_redact",
            "nested_redact",
        }:
            continue
        cfg = _build_config(row)
        actual = redact_event(row["input"], cfg)
        out_str = json.dumps(actual)
        for secret in secret_values:
            if secret in str(row["input"]):
                assert secret not in out_str, (
                    f"Case {row.get('case_id')}: plaintext secret {secret!r} "
                    f"leaked into output {out_str!r}"
                )
        assert REDACTED in out_str, (
            f"Case {row.get('case_id')}: expected REDACTED placeholder in output, got {out_str!r}"
        )


def test_fixture_iter() -> None:
    """Sanity: the fixture loads as a list (ad-hoc debugging entry point)."""
    cases = _load_fixture()
    assert isinstance(cases, list)
    assert all(isinstance(c, dict) for c in cases)
