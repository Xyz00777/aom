"""Status bar per-status tally segment (ok/changed/skipped/failed).

After the ``X/Y tasks`` segment the bar shows a live outcome tally
using the same glyphs as ``aom inspect``: ``●`` ok, ``◆`` changed,
``○`` skipped, ``✖`` failed, ``⊝`` unreachable. ok and changed are
always shown once any result has landed; skipped/failed/unreachable
appear only when non-zero so a clean run stays quiet.
"""

from __future__ import annotations

from ansible_aom.compact.format import format_status_bar
from ansible_aom.core.inspect_model import StatusCounts


def _bar(counts: StatusCounts | None, **kw) -> str:
    base = dict(
        playbook="site.yml",
        hosts_completed=1,
        hosts_total=1,
        warnings=0,
        deprecations=0,
        elapsed_seconds=10,
        tasks_completed=111,
        tasks_total=111,
        task_counts=counts,
    )
    base.update(kw)
    return format_status_bar(**base)


def test_tally_shows_ok_changed_and_nonzero_failed() -> None:
    result = _bar(StatusCounts(ok=108, changed=2, failed=1))
    assert "●108" in result
    assert "◆2" in result
    assert "✖1" in result
    # skipped is zero -> its glyph is suppressed
    assert "○" not in result
    # unreachable is zero -> its glyph is suppressed
    assert "⊝" not in result


def test_tally_shows_ok_and_changed_even_when_zero() -> None:
    result = _bar(StatusCounts(ok=5, changed=0))
    assert "●5" in result
    assert "◆0" in result


def test_tally_suppressed_when_no_results() -> None:
    # Empty tally and no liveness -> no ● anywhere in the bar.
    result = _bar(StatusCounts())
    assert "●" not in result
    assert "◆" not in result


def test_tally_absent_for_legacy_callers() -> None:
    # Callers that don't pass task_counts get the old bar unchanged.
    result = _bar(None)
    assert "●" not in result
    assert "◆" not in result


def test_tally_unreachable_shown_when_present() -> None:
    result = _bar(StatusCounts(ok=3, unreachable=2))
    assert "⊝2" in result


def test_tally_ascii_mode_uses_ascii_glyphs() -> None:
    result = _bar(StatusCounts(ok=4, changed=1, failed=2), ascii_mode=True)
    assert "*4" in result
    assert "+1" in result
    assert "X2" in result


def test_renderer_status_bar_reflects_outcome_tally(monkeypatch) -> None:
    """Wire-up: renderer feeds live per-status counts into the bar."""
    from ansible_aom.compact.renderer import CompactRenderer
    from ansible_aom.core.models import PlayDefinition

    captured: list[str] = []

    class FakeDisplay:
        def start(self):
            pass

        def stop(self):
            pass

        def update(self, text: str) -> None:
            captured.append(text)

        def print_log(self, message: str) -> None:
            pass

        def flush_logs(self) -> None:
            pass

    renderer = CompactRenderer(is_tty=True)
    monkeypatch.setattr(renderer, "_display", FakeDisplay())
    renderer.start("site.yml", [])
    renderer.set_definitions(
        [
            PlayDefinition(
                id="1",
                name="web",
                hosts="webservers",
                resolved_hosts=["w1"],
                tasks=[],
            )
        ]
    )
    renderer.update_state(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-05-11T10:00:00Z",
            "play": {"id": "1", "name": "web"},
        }
    )
    renderer.update_state(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-11T10:00:01Z",
            "task": {"id": "t1", "name": "a"},
            "play": {"id": "1"},
        }
    )
    renderer.update_state(
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-05-11T10:00:02Z",
            "task": {"id": "t1"},
            "play": {"id": "1"},
            "hosts": {"w1": {"changed": True}},
        }
    )
    renderer._last_panel_compute_time = 0.0
    renderer.tick()

    assert any("◆1" in frame for frame in captured), captured
