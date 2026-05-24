## 2026-04-24 Implementation Order Decisions

### Execution Order (dependency-based)
1. compact/password.py - standalone, no deps beyond core
2. compact/logs.py - standalone, depends on core.state.MAX_LOG_LINES
3. compact/display.py - depends on logs
4. compact/renderer.py - depends on display, password, core models
5. tui/app.py - standalone Renderer protocol impl
6. tui/screens/main.py - depends on widgets
7. tui/widgets/task_tree.py - depends on core models
8. tui/widgets/log_panel.py - standalone
9. tui/widgets/status_bar.py - depends on core.config
10. tui/widgets/summary_panel.py - depends on core icons
11. tui/widgets/debug_panel.py - standalone
12. tui/screens/help.py, settings.py, inspect.py, rerun.py - lighter screens

### Parallelization
- Group A (no cross-deps): compact/password.py, compact/logs.py, tui/app.py
- Group B (after A): compact/display.py, tui/widgets/* (5 widgets can be parallel)
- Group C (after B): compact/renderer.py, tui/screens/* (5 screens can be parallel)

## 2026-05-24 — Post-Implementation Bugfix Decisions

### Cross-play completion scope: same-play only
Completed plays must NOT be force-completed by a different play's task
start. Iterate `self.plays.values()` but only force-transition hosts
where `p.play_id == play.play_id`. Cross-play host stealing would corrupt
host totals in the final summary.

### Tree play selection: three-tier sticky fallback
The tree must not flicker between plays during task-gap windows
(play 1 done, play 2 not started yet). Three tiers: fresh running play →
last frame's sticky → last play with tasks. The sticky tier prevents
oscillation without needing to track completion timestamps.

### Upcoming plays: empty runtime.tasks ≠ completed
A play with zero `runtime.tasks` might be upcoming, not completed.
Use `runtime.tasks is not None` (always true) to exclude upcoming
plays from the skip-completed guard. The actual check for "skip"
is: play has tasks AND no running items across all plays.

### Strategy detection: flip on runner_on_start
The JSONL callback from `ansible.posix` only emits `v2_runner_on_start`
when NOT in lockstep mode (`if self._is_lockstep: return`). Therefore
receiving this event is definitive proof of "free" strategy. Flip
`detected_strategy` from "linear" to "free" unconditionally.