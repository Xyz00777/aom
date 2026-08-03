# Compact Renderer Integration Tests

> 58 nodes · cohesion 0.04

## Key Concepts

- **Display** (92 connections) — `src/ansible_aom/compact/display.py`
- **TestDegradedModeEntry** (9 connections) — `tests/compact/test_small_terminal.py`
- **TestDegradedModeFallthrough** (7 connections) — `tests/compact/test_small_terminal.py`
- **TestReEnableOnResize** (7 connections) — `tests/compact/test_small_terminal.py`
- **TestNonTtyUnaffected** (4 connections) — `tests/compact/test_log_flush_batching.py`
- **.test_sighup_saves_session()** (4 connections) — `tests/integration/test_compact_renderer.py`
- **.test_terminal_cleanup_on_exit()** (4 connections) — `tests/integration/test_compact_renderer.py`
- **.test_force_size_at_threshold_does_not_degrade()** (3 connections) — `tests/compact/test_small_terminal.py`
- **.test_non_tty_is_never_degraded()** (3 connections) — `tests/compact/test_small_terminal.py`
- **.test_stop_in_degraded_mode_is_a_noop()** (3 connections) — `tests/compact/test_small_terminal.py`
- **.test_update_without_force_size_falls_back_to_real_terminal()** (3 connections) — `tests/compact/test_small_terminal.py`
- **.test_display_has_print_log_method()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_display_has_start_method()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_display_has_stop_method()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_display_has_update_method()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_non_tty_display_print_log_uses_stdout()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_non_tty_display_start_is_noop()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_non_tty_display_update_is_noop()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_non_tty_line_per_status()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_non_tty_no_continuous_elapsed_time()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_throttled_refresh_rate_max_four_per_second()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.__init__()** (2 connections) — `src/ansible_aom/compact/display.py`
- **.start()** (2 connections) — `src/ansible_aom/compact/display.py`
- **.test_non_tty_print_log_stays_immediate_and_plain()** (2 connections) — `tests/compact/test_log_flush_batching.py`
- **.test_force_size_below_threshold_enters_degraded_mode()** (2 connections) — `tests/compact/test_small_terminal.py`
- *... and 33 more nodes in this community*

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (26 shared connections)
- [Ctrl-C Race Handling](Ctrl-C_Race_Handling.md) (7 shared connections)
- [Config Loading Screen](Config_Loading_Screen.md) (7 shared connections)
- [Frame Parameter Handling](Frame_Parameter_Handling.md) (7 shared connections)
- [Per-Task Timing Tests](Per-Task_Timing_Tests.md) (6 shared connections)
- [Ansible Runner Subprocess](Ansible_Runner_Subprocess.md) (5 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (4 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (3 shared connections)
- [Action Keybindings Lookup](Action_Keybindings_Lookup.md) (3 shared connections)
- [Monochrome Terminal Fallback](Monochrome_Terminal_Fallback.md) (2 shared connections)
- [Completion State Labels](Completion_State_Labels.md) (2 shared connections)
- [Password Pattern Detection](Password_Pattern_Detection.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/display.py`
- `tests/compact/test_log_flush_batching.py`
- `tests/compact/test_small_terminal.py`
- `tests/integration/test_compact_renderer.py`

## Audit Trail

- EXTRACTED: 150 (68%)
- INFERRED: 69 (32%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*