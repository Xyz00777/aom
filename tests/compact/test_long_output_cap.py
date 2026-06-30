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


def test_one_megabyte_failed_msg_truncated(capsys):
    """R2 spec literal: 1 MB msg is logged with the truncation marker.

    A host returning the contents of ``/var/log/messages`` via
    ``register`` + ``debug`` can hand AOM a multi-MB JSONL event. The
    full payload still lands in events.jsonl; the live log just
    truncates so the renderer keeps moving. This test pins the spec's
    literal 1 MB scenario (not just 2x the cap) so a future
    constant-rename or ``_truncate_msg`` regression can't slip past
    CI on small inputs.
    """
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    one_mb_msg = "z" * 1_000_000
    renderer._emit_event_log(
        {
            "_event": "v2_runner_on_failed",
            "hosts": {"web1": {"msg": one_mb_msg, "failed": True}},
        }
    )

    out = capsys.readouterr().out
    assert "…(truncated" in out
    # The 1 MB payload must NOT appear verbatim — that's the bug we're
    # preventing. (Rich would happily print it; it would just stall
    # the render thread doing so.)
    assert one_mb_msg not in out
    # Head still visible so the user gets actionable context.
    assert "z" * 100 in out


def test_item_failed_msg_truncated_above_cap(capsys):
    """Per-item ``v2_runner_item_on_failed`` messages are also capped.

    A looped task (e.g. ``with_items`` over a large file list) that
    fails on one item would otherwise print that item's full msg on
    the per-item ``failed:`` line. Same 4 KB cap applies.
    """
    renderer = CompactRenderer(is_tty=False)
    renderer.start("site.yml", [])

    huge_msg = "q" * (_MSG_DISPLAY_CAP * 2)
    renderer._emit_event_log(
        {
            "_event": "v2_runner_item_on_failed",
            "hosts": {"web1": {"msg": huge_msg, "failed": True}},
        }
    )

    out = capsys.readouterr().out
    assert "…(truncated" in out
    assert huge_msg not in out
