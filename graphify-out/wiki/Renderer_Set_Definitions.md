# Renderer Set Definitions

> 21 nodes · cohesion 0.13

## Key Concepts

- **format.py** (24 connections) — `src/ansible_aom/compact/format.py`
- **_wrap()** (17 connections) — `src/ansible_aom/compact/format.py`
- **collect_tags()** (9 connections) — `src/ansible_aom/compact/format.py`
- **_count_tasks()** (8 connections) — `src/ansible_aom/compact/format.py`
- **format_status_bar()** (8 connections) — `src/ansible_aom/compact/format.py`
- **_count_role_group_tasks()** (5 connections) — `src/ansible_aom/compact/format.py`
- **_count_cell()** (4 connections) — `src/ansible_aom/compact/format.py`
- **_format_count_cells()** (4 connections) — `src/ansible_aom/compact/format.py`
- **format_host_summary()** (4 connections) — `src/ansible_aom/compact/format.py`
- **._build_status_suffix()** (4 connections) — `src/ansible_aom/compact/renderer.py`
- **_collect_role_group_tags()** (3 connections) — `src/ansible_aom/compact/format.py`
- **Pure formatters for the compact renderer.  Every public function here takes doma** (1 connections) — `src/ansible_aom/compact/format.py`
- **Format the status bar for compact mode display.      Args:         playbook: Pat** (1 connections) — `src/ansible_aom/compact/format.py`
- **Render non-zero status count cells.      Order: ok, changed, skipped, failed, un** (1 connections) — `src/ansible_aom/compact/format.py`
- **Format a host summary line with status icons.      Only includes non-zero counts** (1 connections) — `src/ansible_aom/compact/format.py`
- **Right-align ``value`` in a fixed-width cell; dim zero values.      A literal zer** (1 connections) — `src/ansible_aom/compact/format.py`
- **``text`` wrapped in an SGR sequence, or plain ``text`` if not colorising.** (1 connections) — `src/ansible_aom/compact/format.py`
- **Recursively count leaf tasks inside a ``RoleGroupDefinition``.      ``RoleGroupD** (1 connections) — `src/ansible_aom/compact/format.py`
- **Count leaf TaskDefinitions in a play, expanding any RoleGroupDefinition.      Dy** (1 connections) — `src/ansible_aom/compact/format.py`
- **Unique tags across every leaf TaskDefinition, alphabetically sorted.      Used f** (1 connections) — `src/ansible_aom/compact/format.py`
- **Build the trailing ``(N failed, M ok)`` status summary.          Walks the most** (1 connections) — `src/ansible_aom/compact/renderer.py`

## Relationships

- [CLI Argument Parser](CLI_Argument_Parser.md) (7 shared connections)
- [TUI Keybindings Config](TUI_Keybindings_Config.md) (6 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (6 shared connections)
- [RunState Property Invariants](RunState_Property_Invariants.md) (4 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (4 shared connections)
- [Inspect Debug Diagnostics](Inspect_Debug_Diagnostics.md) (2 shared connections)
- [Replay Frame Signatures](Replay_Frame_Signatures.md) (2 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (2 shared connections)
- [Pause Prompt Heuristic](Pause_Prompt_Heuristic.md) (2 shared connections)
- [Host Overview Table](Host_Overview_Table.md) (2 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (2 shared connections)
- [Four-Layer Redaction System](Four-Layer_Redaction_System.md) (1 shared connections)

## Source Files

- `src/ansible_aom/compact/format.py`
- `src/ansible_aom/compact/renderer.py`

## Audit Trail

- EXTRACTED: 81 (81%)
- INFERRED: 19 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*