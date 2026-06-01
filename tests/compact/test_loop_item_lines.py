"""Tests for per-item loop rendering in the streaming log.

The ``ansible.posix.jsonl`` callback emits no per-item events; instead
a looped task's aggregate ``v2_runner_on_ok`` / ``v2_runner_on_failed``
event carries a ``results`` array under ``hosts[host]``, one entry per
loop item. To match ansible's default callback the streaming log expands
that array into one line per item per host:

    changed: [localhost] => (item=apple)
    ok: [localhost] => (item=banana)
    failed: [localhost] => (item=b) => <msg>
    skipping: [localhost] => (item=y)

and suppresses the single aggregate ``ok:``/``changed:``/``fatal:`` line
that a non-looped task would get (ansible does the same).
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.compact.renderer import (
    _CYAN,
    _GREEN,
    _RED,
    _YELLOW,
    CompactRenderer,
)


def _task_start(name: str = "T", uuid: str = "u", ts: str = "2026-05-11T10:00:00Z") -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": ts,
        "task": {"id": uuid, "name": name},
        "play": {"id": "p1"},
    }


def _item(label: str, *, changed=False, failed=False, skipped=False, msg=None) -> dict:
    raw: dict = {"_ansible_item_label": label, "item": label, "changed": changed}
    if failed:
        raw["failed"] = True
    if skipped:
        raw["skipped"] = True
    if msg is not None:
        raw["msg"] = msg
    return raw


def _loop_ok(host: str, items: list[dict], uuid: str = "u", changed: bool = False) -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-05-11T10:00:01Z",
        "task": {"id": uuid},
        "hosts": {host: {"changed": changed, "results": items}},
    }


def _loop_failed(host: str, items: list[dict], uuid: str = "u") -> dict:
    return {
        "_event": "v2_runner_on_failed",
        "_timestamp": "2026-05-11T10:00:01Z",
        "task": {"id": uuid},
        "hosts": {host: {"changed": True, "failed": True, "results": items}},
    }


def _stats(ts: str = "2026-05-11T10:00:02Z") -> dict:
    return {"_event": "v2_playbook_on_stats", "_timestamp": ts, "stats": {}}


def _renderer(colorize: bool = False) -> CompactRenderer:
    r = CompactRenderer(is_tty=False)
    r.start("test.yml", [])
    r._colorize = colorize
    r._display = MagicMock()
    return r


def _logged(r: CompactRenderer) -> list[str]:
    return [c.args[0] for c in r._display.print_log.call_args_list]


def _all_text(r: CompactRenderer) -> str:
    return "\n".join(_logged(r))


class TestOkChangedLoop:
    def test_one_line_per_item_with_label(self):
        r = _renderer()
        r._emit_event_log(_task_start("Echo each fruit", "u1"))
        r._emit_event_log(
            _loop_ok(
                "localhost",
                [
                    _item("apple", changed=True),
                    _item("banana", changed=False),
                    _item("cherry", changed=True),
                ],
                "u1",
                changed=True,
            )
        )
        text = _all_text(r)
        assert "changed: [localhost] => (item=apple)" in text
        assert "ok: [localhost] => (item=banana)" in text
        assert "changed: [localhost] => (item=cherry)" in text

    def test_no_bare_aggregate_host_line(self):
        r = _renderer()
        r._emit_event_log(_task_start("Echo each fruit", "u1"))
        r._emit_event_log(
            _loop_ok("localhost", [_item("apple", changed=True)], "u1", changed=True)
        )
        # The aggregate per-host line a non-looped task would emit must
        # NOT appear — only the per-item line carries the status.
        assert "changed: [localhost]\n" not in _all_text(r) + "\n"
        for line in _logged(r):
            assert line.strip() != "changed: [localhost]"
            assert line.strip() != "ok: [localhost]"

    def test_item_colors_match_status(self):
        r = _renderer(colorize=True)
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(
            _loop_ok(
                "localhost",
                [_item("apple", changed=True), _item("banana", changed=False)],
                "u1",
                changed=True,
            )
        )
        logged = _logged(r)
        assert any(_YELLOW in ln and "item=apple" in ln for ln in logged)
        assert any(_GREEN in ln and "item=banana" in ln for ln in logged)


class TestFailedLoop:
    def test_failed_item_uses_failed_prefix(self):
        r = _renderer()
        r._emit_event_log(_task_start("Maybe fail", "u1"))
        r._emit_event_log(
            _loop_failed(
                "localhost",
                [
                    _item("a", changed=True),
                    _item("b", changed=True, failed=True, msg="non-zero return code"),
                    _item("c", changed=True),
                ],
                "u1",
            )
        )
        text = _all_text(r)
        assert "changed: [localhost] => (item=a)" in text
        assert "failed: [localhost] => (item=b)" in text
        assert "non-zero return code" in text
        assert "changed: [localhost] => (item=c)" in text

    def test_no_aggregate_fatal_line_for_loop(self):
        r = _renderer()
        r._emit_event_log(_task_start("Maybe fail", "u1"))
        r._emit_event_log(
            _loop_failed(
                "localhost",
                [_item("b", changed=True, failed=True, msg="boom")],
                "u1",
            )
        )
        for line in _logged(r):
            assert "FAILED!" not in line
            assert "fatal: [localhost]" not in line

    def test_failed_item_is_red(self):
        r = _renderer(colorize=True)
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(
            _loop_failed("localhost", [_item("b", failed=True, msg="boom")], "u1")
        )
        assert any(_RED in ln and "item=b" in ln for ln in _logged(r))


class TestSkippedItem:
    def test_skipped_item_renders_inline(self):
        r = _renderer()
        r._emit_event_log(_task_start("Skip some", "u1"))
        r._emit_event_log(
            _loop_ok(
                "localhost",
                [_item("x", changed=False), _item("y", skipped=True)],
                "u1",
            )
        )
        text = _all_text(r)
        assert "ok: [localhost] => (item=x)" in text
        assert "skipping: [localhost] => (item=y)" in text

    def test_skipped_item_is_cyan(self):
        r = _renderer(colorize=True)
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(
            _loop_ok("localhost", [_item("y", skipped=True)], "u1")
        )
        assert any(_CYAN in ln and "item=y" in ln for ln in _logged(r))


class TestNonLoopUnaffected:
    def test_plain_task_still_emits_aggregate_line(self):
        r = _renderer()
        r._emit_event_log(_task_start("Plain", "u1"))
        r._emit_event_log(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-05-11T10:00:01Z",
                "task": {"id": "u1"},
                "hosts": {"web1": {"changed": True}},
            }
        )
        assert any(line.strip().startswith("changed: [web1]") for line in _logged(r))
