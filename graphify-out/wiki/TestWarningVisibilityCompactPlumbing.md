# TestWarningVisibilityCompactPlumbing

> 19 nodes · cohesion 0.18

## Key Concepts

- **TestWarningVisibilityCompactPlumbing** (13 connections) — `tests/unit/test_cli.py`
- **Path** (10 connections)
- **._write_live_config()** (7 connections) — `tests/unit/test_cli.py`
- **MonkeyPatch** (5 connections)
- **.test_cli_no_failed_hint_overrides_enabled_config()** (5 connections) — `tests/unit/test_cli.py`
- **.test_config_disables_failed_hint()** (5 connections) — `tests/unit/test_cli.py`
- **.test_cli_hide_deprecations_overrides_enabled_config()** (4 connections) — `tests/unit/test_cli.py`
- **.test_cli_hide_warnings_overrides_enabled_config()** (4 connections) — `tests/unit/test_cli.py`
- **.test_config_disables_warning_visibility()** (4 connections) — `tests/unit/test_cli.py`
- **.test_core_module_file_exists()** (3 connections) — `tests/unit/test_cli.py`
- **.test_cli_entry_point_is_aom()** (3 connections) — `tests/unit/test_cli.py`
- **.test_package_name_is_ansible_aom()** (3 connections) — `tests/unit/test_cli.py`
- **._write_live_config()** (2 connections) — `tests/unit/test_cli.py`
- **[live] show_failed_hint: false should disable compact hints.** (1 connections) — `tests/unit/test_cli.py`
- **--no-failed-hint still wins when config enables hints.** (1 connections) — `tests/unit/test_cli.py`
- **--hide-warnings / --hide-deprecations propagate into compact mode.** (1 connections) — `tests/unit/test_cli.py`
- **TC-003: Core module file exists at expected path.** (1 connections) — `tests/unit/test_cli.py`
- **TC-001: Package name is 'ansible-aom'.** (1 connections) — `tests/unit/test_cli.py`
- **TC-001: CLI entry point is 'aom'.** (1 connections) — `tests/unit/test_cli.py`

## Relationships

- [HostRunState](HostRunState.md) (8 shared connections)
- [TestHideStateCompactPlumbing](TestHideStateCompactPlumbing.md) (3 shared connections)
- [TestCoreModuleStructure](TestCoreModuleStructure.md) (1 shared connections)
- [CompactRenderer](CompactRenderer.md) (1 shared connections)
- [RunState](RunState.md) (1 shared connections)

## Source Files

- `tests/unit/test_cli.py`

## Audit Trail

- EXTRACTED: 67 (91%)
- INFERRED: 7 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*