"""R2: cap long msg output so a runaway host doesn't stall the renderer.

A task that does ``register: result`` + ``debug: var=result`` on a host
that returns megabytes of stdout will hand AOM a single multi-MB JSONL
event. The full payload still lands in events.jsonl for inspect-time
replay; the live log is just truncated so the renderer keeps moving.
"""

from __future__ import annotations

from ansible_aom.compact.renderer import _MSG_DISPLAY_CAP, CompactRenderer


def test_failed_msg_truncated_above_cap(capsys):
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    huge_msg = "x" * (_MSG_DISPLAY_CAP * 2)
    renderer._emit_event_log(
        {
            "_event": "v2_runner_on_failed",
            "hosts": {"web1": {"msg": huge_msg, "failed": True}},
        }
    )

    out = capsys.readouterr().out
    # Truncation marker present
    assert "…(truncated" in out
    # Original full string NOT present
    assert huge_msg not in out
    # Prefix of msg still visible — first 100 chars at least
    assert "x" * 100 in out


def test_short_msg_not_truncated(capsys):
    """Sub-cap messages must be passed through unchanged."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    small_msg = "boom"
    renderer._emit_event_log(
        {
            "_event": "v2_runner_on_failed",
            "hosts": {"web1": {"msg": small_msg, "failed": True}},
        }
    )

    out = capsys.readouterr().out
    assert "boom" in out
    assert "truncated" not in out


def test_unreachable_msg_truncated_above_cap(capsys):
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    huge_msg = "y" * (_MSG_DISPLAY_CAP * 2)
    renderer._emit_event_log(
        {
            "_event": "v2_runner_on_unreachable",
            "hosts": {"web1": {"msg": huge_msg, "unreachable": True}},
        }
    )

    out = capsys.readouterr().out
    assert "…(truncated" in out
    assert huge_msg not in out
