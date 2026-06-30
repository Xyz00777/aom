# Config Loading Screen

> 10 nodes · cohesion 0.22

## Key Concepts

- **load_config()** (8 connections) — `src/ansible_aom/core/config.py`
- **SettingsScreen** (6 connections) — `src/ansible_aom/tui/screens/settings.py`
- **.compose()** (4 connections) — `src/ansible_aom/tui/screens/settings.py`
- **._build_display_lines()** (3 connections) — `src/ansible_aom/tui/screens/settings.py`
- **.test_load_config_returns_app_config()** (3 connections) — `tests/unit/test_config.py`
- **Screen** (2 connections)
- **.action_dismiss()** (2 connections) — `src/ansible_aom/tui/screens/settings.py`
- **Load configuration from YAML file or use defaults.      Args:         config_pat** (1 connections) — `src/ansible_aom/core/config.py`
- **settings.py** (1 connections) — `src/ansible_aom/tui/screens/settings.py`
- **load_config returns AppConfig instance.** (1 connections) — `tests/unit/test_config.py`

## Relationships

- [[App Configuration Settings]] (3 shared connections)
- [[Compact Display Module Layout]] (1 shared connections)
- [[Status Bar Warning Panels]] (1 shared connections)
- [[Secret Redaction Configuration]] (1 shared connections)
- [[Warnings Display Config]] (1 shared connections)
- [[Main TUI Screen]] (1 shared connections)
- [[Playbook Event Parsing]] (1 shared connections)
- [[Inspect TUI Widget Data]] (1 shared connections)
- [[App Config Model Tests]] (1 shared connections)

## Source Files

- `src/ansible_aom/core/config.py`
- `src/ansible_aom/tui/screens/settings.py`
- `tests/unit/test_config.py`

## Audit Trail

- EXTRACTED: 26 (84%)
- INFERRED: 5 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*