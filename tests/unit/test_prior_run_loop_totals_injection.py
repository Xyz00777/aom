"""``set_prior_run`` injects a prior run's loop totals into the RunState.

The tree projection reads ``RunState.loop_totals`` to render ``N/total``.
The runner hands the renderer a ``PriorRun`` via ``set_prior_run``; each
renderer copies its ``loop_totals`` onto its own RunState so the live tree
can resolve totals per host.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.session.history import PriorRun


def _prior_with_totals() -> PriorRun:
    return PriorRun(
        session_id="aaa",
        duration_seconds=60.0,
        task_count=1,
        host_count=1,
        end_time=datetime.now(timezone.utc),
        loop_totals={"site.yml:5": {"web1": 12}},
    )


class TestCompactInjection:
    def test_set_prior_run_copies_loop_totals_into_state(self):
        r = CompactRenderer(is_tty=False)
        r.start("site.yml", [])
        r.set_prior_run(_prior_with_totals())
        assert r._state is not None
        assert r._state.loop_totals == {"site.yml:5": {"web1": 12}}

    def test_set_prior_run_none_leaves_empty_totals(self):
        r = CompactRenderer(is_tty=False)
        r.start("site.yml", [])
        r.set_prior_run(None)
        assert r._state is not None
        assert r._state.loop_totals == {}


class TestTuiInjection:
    def test_set_prior_run_copies_loop_totals_into_run_state(self):
        from ansible_aom.tui.app import AOMApp

        app = AOMApp(playbook="site.yml")
        app.start("site.yml", [])
        app.set_prior_run(_prior_with_totals())
        assert app.run_state.loop_totals == {"site.yml:5": {"web1": 12}}
