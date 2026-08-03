# Status Bar Color Tests

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestInspectSubcommand** (13 connections) — `tests/unit/test_cli.py`
- **.test_inspect_dispatches_to_inspect_main_with_remaining_argv()** (2 connections) — `tests/unit/test_cli.py`
- **.test_inspect_forwards_prune_subcommand()** (2 connections) — `tests/unit/test_cli.py`
- **.test_inspect_forwards_text_flag()** (2 connections) — `tests/unit/test_cli.py`
- **.test_inspect_propagates_exit_code()** (2 connections) — `tests/unit/test_cli.py`
- **Tests for TC-013 to TC-023: Inspect Subcommand dispatch.      The top-level CLI** (1 connections) — `tests/unit/test_cli.py`
- **No-arg `aom inspect` forwards an empty argv to inspect.cli.main.** (1 connections) — `tests/unit/test_cli.py`
- **`aom inspect --text` forwards `['--text']` to inspect.cli.main.** (1 connections) — `tests/unit/test_cli.py`
- **`aom inspect prune --days 30` forwards args verbatim.** (1 connections) — `tests/unit/test_cli.py`
- **Exit code from inspect.cli.main flows back through the dispatcher.** (1 connections) — `tests/unit/test_cli.py`

## Relationships

- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (4 shared connections)
- [App Configuration Settings](App_Configuration_Settings.md) (1 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (1 shared connections)
- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (1 shared connections)

## Source Files

- `tests/unit/test_cli.py`

## Audit Trail

- EXTRACTED: 19 (73%)
- INFERRED: 7 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*