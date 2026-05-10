"""Tests for the pre-flight orchestrator (--list-tasks + --list-hosts)."""

from __future__ import annotations

from ansible_aom.core.parser import PreParseResult


def test_preparseresult_has_definitions_and_errors_fields():
    """PreParseResult exposes assembled definitions plus an errors list."""
    result = PreParseResult(plays=[], play_hosts=[], definitions=[], errors=[])
    assert result.definitions == []
    assert result.errors == []


def test_preparseresult_definitions_and_errors_default_to_empty():
    """The new fields are optional with empty defaults so old call sites still work."""
    result = PreParseResult(plays=[], play_hosts=[])
    assert result.definitions == []
    assert result.errors == []
