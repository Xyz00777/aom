"""Pure schema for the per-host prompt control channel."""

from __future__ import annotations

from ansible_aom.core.prompt_channel import (
    ENV_VAR,
    FIFO_SUFFIX,
    REQUEST_SUFFIX,
    PromptRequest,
    decode_request,
    encode_request,
    is_abort,
)


def test_env_var_and_suffixes_are_stable():
    assert ENV_VAR == "AOM_PROMPT_CONTROL_DIR"
    assert REQUEST_SUFFIX == ".req"
    assert FIFO_SUFFIX == ".fifo"


def test_request_round_trips():
    req = PromptRequest(id="abc", host="web1", prompt="Deploy web1? ", created=1.5)
    decoded = decode_request(encode_request(req))
    assert decoded == req


def test_decode_tolerates_missing_created():
    decoded = decode_request('{"id": "x", "host": "h", "prompt": "p"}')
    assert decoded.id == "x" and decoded.host == "h" and decoded.prompt == "p"
    assert decoded.created == 0.0


def test_is_abort_recognizes_negatives_case_insensitively():
    for word in ("no", "No", "NO", "abort", "cancel", "n"):
        assert is_abort(word) is True


def test_is_abort_false_for_continue_and_empty():
    for word in ("", "yes", "y", "ok", "  ", "go ahead"):
        assert is_abort(word) is False
