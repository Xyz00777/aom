# Loop Item Stream Tests

> 42 nodes · cohesion 0.05

## Key Concepts

- **diagnostics.py** (38 connections) — `src/ansible_aom/core/diagnostics.py`
- **install_from_env()** (9 connections) — `src/ansible_aom/core/diagnostics.py`
- **build_diagnostics_record()** (5 connections) — `src/ansible_aom/core/diagnostics.py`
- **RendererStats** (5 connections) — `src/ansible_aom/core/diagnostics.py`
- **get_profiler()** (4 connections) — `src/ansible_aom/core/diagnostics.py`
- **render_storm_warning()** (4 connections) — `src/ansible_aom/core/diagnostics.py`
- **dump_profile()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **_is_truthy()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **_parse_watchdog()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **record_tracemalloc_peak()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **set_psutil_disabled()** (3 connections) — `src/ansible_aom/core/diagnostics.py`
- **Profile** (2 connections)
- **_psutil_disabled_reason()** (2 connections) — `src/ansible_aom/ansible/runner.py`
- **get_lifecycle_marks()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **psutil_disabled_reason()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **_reset_for_testing()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **set_last_renderer_stats()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **set_session_recording_disabled()** (2 connections) — `src/ansible_aom/core/diagnostics.py`
- **get_last_renderer_stats()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **get_tracemalloc_peak_kb()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **is_profile()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **is_tracemalloc()** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- **Any** (1 connections)
- **Path** (1 connections)
- **Opt-in diagnostics / observability layer for AOM.  Pure module — reads ``os.envi** (1 connections) — `src/ansible_aom/core/diagnostics.py`
- *... and 17 more nodes in this community*

## Relationships

- [Tree Block Animation](Tree_Block_Animation.md) (4 shared connections)
- [Renderer Protocol Tests](Renderer_Protocol_Tests.md) (4 shared connections)
- [First Ctrl-C Cancellation](First_Ctrl-C_Cancellation.md) (3 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (2 shared connections)
- [Status Bar Widget](Status_Bar_Widget.md) (2 shared connections)
- [Rerun Subcommand Module](Rerun_Subcommand_Module.md) (2 shared connections)
- [Replay Determinism Tests](Replay_Determinism_Tests.md) (2 shared connections)
- [Warning Classification Tests](Warning_Classification_Tests.md) (1 shared connections)
- [Frame Parameter Handling](Frame_Parameter_Handling.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [State Machine Happy Path](State_Machine_Happy_Path.md) (1 shared connections)
- [Replay Frame Signatures](Replay_Frame_Signatures.md) (1 shared connections)

## Source Files

- `src/ansible_aom/ansible/runner.py`
- `src/ansible_aom/core/diagnostics.py`

## Audit Trail

- EXTRACTED: 116 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*