# Config Loading Screen

> 8 nodes · cohesion 0.22

## Key Concepts

- **SettingsScreen** (9 connections) — `src/ansible_aom/tui/screens/settings.py`
- **load_config()** (8 connections) — `src/ansible_aom/core/config.py`
- **.compose()** (7 connections) — `src/ansible_aom/tui/screens/settings.py`
- **._build_display_lines()** (4 connections) — `src/ansible_aom/tui/screens/settings.py`
- **.action_dismiss()** (3 connections) — `src/ansible_aom/tui/screens/settings.py`
- **.test_load_config_returns_app_config()** (3 connections) — `tests/unit/test_config.py`
- **settings.py** (1 connections) — `src/ansible_aom/tui/screens/settings.py`
- **load_config returns AppConfig instance.** (1 connections) — `tests/unit/test_config.py`

## Relationships

- [[App Configuration Settings]] (3 shared connections)
- [[Compact Display Module Layout]] (1 shared connections)
- [[Status Bar Warning Panels]] (1 shared connections)
- [[Secret Redaction Configuration]] (1 shared connections)
- [[Warnings Display Config]] (1 shared connections)
- [[AOM TUI Application]] (1 shared connections)
- [[Playbook Event Parsing]] (1 shared connections)
- [[Inspect TUI Widget Data]] (1 shared connections)
- [[App Config Model Tests]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/config.py`
- `src/ansible_aom/tui/screens/settings.py`
- `tests/unit/test_config.py`

## Audit Trail

- EXTRACTED: 26 (72%)
- INFERRED: 10 (28%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*