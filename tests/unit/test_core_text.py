"""Unit tests for core/text.py — surrogate replacement for text that
leaves the lossless str domain (terminal display, sqlite TEXT)."""

from __future__ import annotations

from ansible_aom.core.text import replace_surrogates


def test_clean_text_passes_through_unchanged() -> None:
    assert replace_surrogates("normal text") == "normal text"
    assert replace_surrogates("with ☃ unicode ünï 🎉") == "with ☃ unicode ünï 🎉"
    assert replace_surrogates("") == ""


def test_lone_surrogates_become_question_marks() -> None:
    # Low surrogate, as produced by surrogateescape for an invalid byte.
    assert replace_surrogates(b"a\xffb".decode("utf-8", "surrogateescape")) == "a?b"
    # High surrogate (e.g. from a "\ud800" JSON escape).
    assert replace_surrogates("a\ud800b") == "a?b"
    assert replace_surrogates("é\udcc3\udcff") == "é??"


def test_result_is_utf8_encodable() -> None:
    replace_surrogates("x\udcffy\ud83d").encode("utf-8")
