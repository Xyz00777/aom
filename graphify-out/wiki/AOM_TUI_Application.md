# AOM TUI Application

> 93 nodes · cohesion 0.03

## Key Concepts

- **WarningEntry** (84 connections) — `src/ansible_aom/core/models.py`
- **TestWarningEntry** (19 connections) — `tests/unit/test_models.py`
- **TestWarningEntryDataclass** (16 connections) — `tests/unit/test_warnings.py`
- **TestFilterPanelWarningCheckboxes** (15 connections) — `tests/tui/test_panels.py`
- **TestWarningClassification** (13 connections) — `tests/unit/test_warnings.py`
- **TestPtyStreamParserWarningsList** (12 connections) — `tests/unit/test_warnings.py`
- **TestWarningEntrySourceField** (11 connections) — `tests/unit/test_warnings.py`
- **test_warnings.py** (10 connections) — `tests/unit/test_warnings.py`
- **TestWarningEntryTimestamp** (10 connections) — `tests/unit/test_warnings.py`
- **.test_warnings_list_contains_warning_entry_objects()** (4 connections) — `tests/unit/test_warnings.py`
- **.drain_warnings()** (3 connections) — `src/ansible_aom/core/parser.py`
- **.test_warning_only_entries_shown()** (3 connections) — `tests/tui/test_panels.py`
- **.warnings_list()** (3 connections) — `tests/tui/test_panels.py`
- **.test_warning_entry_all_fields()** (3 connections) — `tests/unit/test_models.py`
- **.test_warning_entry_default_source_is_empty()** (3 connections) — `tests/unit/test_models.py`
- **.test_warning_entry_deprecation_type()** (3 connections) — `tests/unit/test_models.py`
- **.test_warning_entry_empty_message()** (3 connections) — `tests/unit/test_models.py`
- **.test_warning_entry_is_dataclass()** (3 connections) — `tests/unit/test_models.py`
- **.test_warning_entry_none_timestamp()** (3 connections) — `tests/unit/test_models.py`
- **.test_warning_entry_required_fields()** (3 connections) — `tests/unit/test_models.py`
- **.test_warning_entry_warning_type()** (3 connections) — `tests/unit/test_models.py`
- **.test_multiple_warnings_preserve_order()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_warnings_list_empty_initially()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_warnings_property_returns_list()** (3 connections) — `tests/unit/test_warnings.py`
- **.test_deprecated_feature_classification()** (3 connections) — `tests/unit/test_warnings.py`
- *... and 68 more nodes in this community*

## Relationships

- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (29 shared connections)
- [Run State Completion Recap](Run_State_Completion_Recap.md) (20 shared connections)
- [Run State Summary Panel](Run_State_Summary_Panel.md) (16 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (12 shared connections)
- [Compact Renderer Implementation](Compact_Renderer_Implementation.md) (8 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (6 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (3 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (2 shared connections)
- [Per-Task Overhead Analysis](Per-Task_Overhead_Analysis.md) (2 shared connections)
- [Password Timeout](Password_Timeout.md) (2 shared connections)
- [Three-Pane Inspect App](Three-Pane_Inspect_App.md) (1 shared connections)
- [Secret Redaction Configuration](Secret_Redaction_Configuration.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/models.py`
- `src/ansible_aom/core/parser.py`
- `tests/tui/test_panels.py`
- `tests/unit/test_models.py`
- `tests/unit/test_warnings.py`

## Audit Trail

- EXTRACTED: 188 (54%)
- INFERRED: 158 (46%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*