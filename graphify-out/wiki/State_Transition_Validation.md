# State Transition Validation

> 11 nodes · cohesion 0.25

## Key Concepts

- **detect_duplicate_playbook()** (8 connections) — `src/ansible_aom/cli.py`
- **test_cli_duplicate_playbook.py** (7 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **test_detect_duplicate_playbook_distinguishes_different_files()** (3 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **test_detect_duplicate_playbook_handles_path_normalisation()** (3 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **test_detect_duplicate_playbook_finds_exact_repeat()** (2 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **test_detect_duplicate_playbook_handles_empty_args()** (2 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **test_detect_duplicate_playbook_returns_false_when_no_repeat()** (2 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **True if `playbook` appears (path-normalised) in `ansible_args`.      Catches the** (1 connections) — `src/ansible_aom/cli.py`
- **Tests for duplicate-playbook argument detection.  When the user types `aom site.** (1 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **Multiple distinct .yml files are a legitimate ansible-playbook invocation.** (1 connections) — `tests/unit/test_cli_duplicate_playbook.py`
- **./site.yml and site.yml refer to the same file — flag the duplicate.** (1 connections) — `tests/unit/test_cli_duplicate_playbook.py`

## Relationships

- [ansible_aom/cli.py](ansible_aom-cli.py.md) (2 shared connections)
- [load_session](load_session.md) (1 shared connections)

## Source Files

- `src/ansible_aom/cli.py`
- `tests/unit/test_cli_duplicate_playbook.py`

## Audit Trail

- EXTRACTED: 31 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*