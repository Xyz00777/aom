# TestNoRedactFlag

> 14 nodes · cohesion 0.14

## Key Concepts

- **TestNoRedactFlag** (17 connections) — `tests/unit/test_cli.py`
- **.test_no_redact_defaults_false()** (2 connections) — `tests/unit/test_cli.py`
- **.test_no_redact_does_not_leak_to_ansible_args()** (2 connections) — `tests/unit/test_cli.py`
- **.test_no_redact_help_text_warns_dangerous()** (2 connections) — `tests/unit/test_cli.py`
- **.test_no_redact_long_form()** (2 connections) — `tests/unit/test_cli.py`
- **.test_no_redact_non_tty_with_yes_proceeds()** (2 connections) — `tests/unit/test_cli.py`
- **.test_no_redact_non_tty_without_yes_refuses_with_exit_2()** (2 connections) — `tests/unit/test_cli.py`
- **.test_no_redact_tty_with_no_answer_returns_2()** (2 connections) — `tests/unit/test_cli.py`
- **.test_no_redact_tty_with_yes_proceeds_without_prompt()** (2 connections) — `tests/unit/test_cli.py`
- **Task 5.2: --no-redact disables redaction (with safety gates; see QC-003).** (1 connections) — `tests/unit/test_cli.py`
- **QC-003: --no-redact in non-TTY mode without --yes refuses with exit 2.** (1 connections) — `tests/unit/test_cli.py`
- **QC-003: --no-redact --yes in non-TTY mode proceeds (CI escape hatch).** (1 connections) — `tests/unit/test_cli.py`
- **TTY + --yes → skip the prompt, proceed.** (1 connections) — `tests/unit/test_cli.py`
- **TTY + no --yes + user answers 'n' → refuse with exit 2.** (1 connections) — `tests/unit/test_cli.py`

## Relationships

- [HostRunState](HostRunState.md) (6 shared connections)
- [create_parser](create_parser.md) (4 shared connections)
- [CompactRenderer](CompactRenderer.md) (1 shared connections)
- [RunState](RunState.md) (1 shared connections)

## Source Files

- `tests/unit/test_cli.py`

## Audit Trail

- EXTRACTED: 27 (71%)
- INFERRED: 11 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*