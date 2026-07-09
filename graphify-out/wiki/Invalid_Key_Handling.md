# Invalid Key Handling

> 12 nodes · cohesion 0.17

## Key Concepts

- **TestFormatFlag** (17 connections) — `tests/unit/test_cli.py`
- **.test_format_flag_does_not_appear_in_ansible_args()** (3 connections) — `tests/unit/test_cli.py`
- **.test_main_dispatches_json_renderer_when_format_json()** (3 connections) — `tests/unit/test_cli.py`
- **.test_format_flag_accepts_compact_explicit()** (2 connections) — `tests/unit/test_cli.py`
- **.test_format_flag_accepts_json()** (2 connections) — `tests/unit/test_cli.py`
- **.test_format_flag_defaults_to_compact()** (2 connections) — `tests/unit/test_cli.py`
- **.test_format_flag_rejects_unknown_value()** (2 connections) — `tests/unit/test_cli.py`
- **.test_main_rejects_tui_plus_json_format()** (2 connections) — `tests/unit/test_cli.py`
- **Tests for F6: --format {compact,json} flag.** (1 connections) — `tests/unit/test_cli.py`
- **--format is consumed by argparse, not forwarded to ansible-playbook.** (1 connections) — `tests/unit/test_cli.py`
- **`aom --tui --format json playbook.yml` exits 2 with a usage error.** (1 connections) — `tests/unit/test_cli.py`
- **`aom --format json playbook.yml` constructs a JsonRenderer.** (1 connections) — `tests/unit/test_cli.py`

## Relationships

- [PTY Stream Parser](PTY_Stream_Parser.md) (5 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (4 shared connections)
- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (2 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)
- [Compact Renderer Integration Tests](Compact_Renderer_Integration_Tests.md) (1 shared connections)
- [Status Bar Warning Panels](Status_Bar_Warning_Panels.md) (1 shared connections)
- [Session Recording Tests](Session_Recording_Tests.md) (1 shared connections)

## Source Files

- `tests/unit/test_cli.py`

## Audit Trail

- EXTRACTED: 23 (62%)
- INFERRED: 14 (38%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*