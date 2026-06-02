"""Live per-item loop streaming in the compact log.

With the bundled ``aom_jsonl`` callback, a loop emits one
``v2_runner_item_on_*`` event per item *as it completes*, then the
aggregate ``v2_runner_on_ok``/``v2_runner_on_failed`` still lands at the
end carrying the full ``results[]`` array.

The streaming log renders each item event immediately, and must NOT
re-expand the aggregate's ``results[]`` for items it already streamed
(otherwise every item prints twice). When no item events streamed (plain
``ansible.posix.jsonl`` fallback), the aggregate expansion still runs —
preserving today's behavior.
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


def _task_start(name: str = "T", uuid: str = "u1", ts: str = "2026-05-11T10:00:00Z") -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": ts,
        "task": {"id": uuid, "name": name},
        "play": {"id": "p1"},
    }


def _item_event(
    event: str,
    host: str,
    label: str,
    *,
    changed: bool = False,
    failed: bool = False,
    skipped: bool = False,
    msg: str | None = None,
    uuid: str = "u1",
    ts: str = "2026-05-11T10:00:01Z",
) -> dict:
    raw: dict = {"_ansible_item_label": label, "item": label, "changed": changed}
    if failed:
        raw["failed"] = True
    if skipped:
        raw["skipped"] = True
    if msg is not None:
        raw["msg"] = msg
    return {
        "_event": event,
        "_timestamp": ts,
        "task": {"id": uuid},
        "hosts": {host: raw},
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


def _loop_ok(host: str, items: list[dict], uuid: str = "u1", changed: bool = False) -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-05-11T10:00:02Z",
        "task": {"id": uuid},
        "hosts": {host: {"changed": changed, "results": items}},
    }


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


class TestItemEventRendersImmediately:
    def test_ok_item_streams_one_line(self):
        r = _renderer()
        r._emit_event_log(_task_start("Echo", "u1"))
        r._emit_event_log(_item_event("v2_runner_item_on_ok", "localhost", "apple"))
        assert "ok: [localhost] => (item=apple)" in _all_text(r)

    def test_changed_item_streams_one_line(self):
        r = _renderer()
        r._emit_event_log(_task_start("Echo", "u1"))
        r._emit_event_log(_item_event("v2_runner_item_on_ok", "localhost", "banana", changed=True))
        assert "changed: [localhost] => (item=banana)" in _all_text(r)

    def test_failed_item_streams_with_msg(self):
        r = _renderer()
        r._emit_event_log(_task_start("Echo", "u1"))
        r._emit_event_log(
            _item_event("v2_runner_item_on_failed", "localhost", "b", failed=True, msg="boom")
        )
        text = _all_text(r)
        assert "failed: [localhost] => (item=b)" in text
        assert "boom" in text

    def test_skipped_item_streams_one_line(self):
        r = _renderer()
        r._emit_event_log(_task_start("Echo", "u1"))
        r._emit_event_log(_item_event("v2_runner_item_on_skipped", "localhost", "y", skipped=True))
        assert "skipping: [localhost] => (item=y)" in _all_text(r)

    def test_item_colors_match_status(self):
        r = _renderer(colorize=True)
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_item_event("v2_runner_item_on_ok", "localhost", "apple", changed=True))
        r._emit_event_log(_item_event("v2_runner_item_on_ok", "localhost", "banana"))
        r._emit_event_log(
            _item_event("v2_runner_item_on_failed", "localhost", "c", failed=True, msg="x")
        )
        r._emit_event_log(_item_event("v2_runner_item_on_skipped", "localhost", "d", skipped=True))
        logged = _logged(r)
        assert any(_YELLOW in ln and "item=apple" in ln for ln in logged)
        assert any(_GREEN in ln and "item=banana" in ln for ln in logged)
        assert any(_RED in ln and "item=c" in ln for ln in logged)
        assert any(_CYAN in ln and "item=d" in ln for ln in logged)


class TestDedupAgainstAggregate:
    def test_streamed_items_not_duplicated_by_aggregate(self):
        r = _renderer()
        r._emit_event_log(_task_start("Echo", "u1"))
        items = [
            _item("apple", changed=True),
            _item("banana"),
            _item("cherry", changed=True),
        ]
        # Stream each item as it completes.
        for raw in items:
            r._emit_event_log(
                _item_event(
                    "v2_runner_item_on_ok",
                    "localhost",
                    raw["_ansible_item_label"],
                    changed=raw["changed"],
                )
            )
        # Then the aggregate lands with the full results[] array.
        r._emit_event_log(_loop_ok("localhost", items, "u1", changed=True))

        text = _all_text(r)
        assert text.count("item=apple") == 1
        assert text.count("item=banana") == 1
        assert text.count("item=cherry") == 1

    def test_aggregate_still_expands_without_streamed_items(self):
        # Plain ansible.posix.jsonl fallback: no item events ever streamed,
        # so the aggregate's results[] must still expand (today's behavior).
        r = _renderer()
        r._emit_event_log(_task_start("Echo", "u1"))
        r._emit_event_log(
            _loop_ok("localhost", [_item("apple", changed=True), _item("banana")], "u1")
        )
        text = _all_text(r)
        assert "changed: [localhost] => (item=apple)" in text
        assert "ok: [localhost] => (item=banana)" in text


class TestItemEventsAreKnown:
    def test_item_events_not_counted_unknown(self):
        r = _renderer()
        r.update_state(_task_start("Echo", "u1"))
        r.update_state(_item_event("v2_runner_item_on_ok", "localhost", "apple"))
        r.update_state(_item_event("v2_runner_item_on_failed", "localhost", "b", failed=True))
        r.update_state(_item_event("v2_runner_item_on_skipped", "localhost", "c", skipped=True))
        assert r._state is not None
        assert "v2_runner_item_on_ok" not in r._state.unknown_events
        assert "v2_runner_item_on_failed" not in r._state.unknown_events
        assert "v2_runner_item_on_skipped" not in r._state.unknown_events
