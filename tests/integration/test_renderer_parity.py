"""Cross-renderer parity invariant.

Feed the same recorded JSONL stream through the two renderers
(CompactRenderer and JsonRenderer) and assert their final ``RunState``
projections are identical via ``core.parity.reduce_state_for_parity``.

The point is not to test rendering output — that's covered by
snapshot tests — but to assert that the *state* every renderer
keeps after consuming the same events agrees on host counts, task
totals, exit code, and play count. A divergence here means one
renderer is silently dropping or double-counting events.

The reducer lives in ``core/parity.py`` rather than in this test
file because the logic is pure (no I/O, dataclass projection only)
and the same shape is useful for any non-test consumer that wants
a structural summary of a run.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.parity import reduce_state_for_parity
from ansible_aom.formats.json import JsonRenderer

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"

# Each fixture is a recorded ``events.jsonl`` we can replay through
# any renderer. Picked to span: a single-task happy path, a
# multi-host run with every status (ok / changed / failed / skipped
# / unreachable), and a single-task failure.
PARITY_FIXTURES: tuple[str, ...] = (
    "single_task_ok.jsonl",
    "multi_host_mixed.jsonl",
    "playbook_failed.jsonl",
)


def _load_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _drive_compact(events: list[dict]) -> dict:
    """Drive a CompactRenderer through every event and reduce the final state."""
    renderer = CompactRenderer(is_tty=False)
    renderer.start("test.yml", [])
    renderer.set_definitions([])
    for event in events:
        renderer.update_state(event)
    renderer.handle_completion(0, "completed")
    # Capture the state BEFORE stop(): CompactRenderer.stop() clears
    # ``_state`` as part of its display teardown.
    assert renderer._state is not None
    reduced = reduce_state_for_parity(renderer._state)
    renderer.stop()
    return reduced


def _drive_json(events: list[dict], capsys: pytest.CaptureFixture[str]) -> dict:
    """Drive a JsonRenderer through every event and reduce its RunState.

    The renderer's ``handle_completion`` prints to stdout; ``capsys``
    swallows that — we only care about the in-memory state here.
    """
    renderer = JsonRenderer()
    renderer.start("test.yml", [])
    renderer.set_definitions([])
    for event in events:
        renderer.update_state(event)
    renderer.handle_completion(0, "completed")
    capsys.readouterr()  # discard the printed JSON summary
    renderer.stop()
    assert renderer._state is not None
    return reduce_state_for_parity(renderer._state)


@pytest.mark.parametrize("fixture_name", PARITY_FIXTURES)
def test_all_renderers_agree_on_reduced_state(
    fixture_name: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """For each fixture, both renderers must reduce to the same dict."""
    events = _load_events(FIXTURES_DIR / fixture_name)
    assert events, f"fixture {fixture_name} is empty"

    compact_view = _drive_compact(events)
    json_view = _drive_json(events, capsys)

    assert compact_view == json_view, (
        f"compact vs json disagreed on {fixture_name}:\n"
        f"  compact: {compact_view}\n  json:    {json_view}"
    )


def test_reduced_state_shape_is_stable() -> None:
    """Sanity check the shape on a known-good fixture.

    Locks in the keys other consumers (parity, future inspect views)
    depend on, so a refactor that drops a key fails loudly here
    instead of silently changing the contract.
    """
    events = _load_events(FIXTURES_DIR / "single_task_ok.jsonl")
    view = _drive_compact(events)

    assert set(view) == {"hosts", "totals", "exit_code", "n_plays", "n_tasks"}
    assert set(view["totals"]) == {
        "ok",
        "changed",
        "failed",
        "unreachable",
        "skipped",
        "rescued",
        "ignored",
    }
    for host_counts in view["hosts"].values():
        assert set(host_counts) == set(view["totals"])
