# Template Name Regression

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestAOMAppInteractivePrompt** (8 connections) — `tests/unit/test_interactive_prompt.py`
- **test_interactive_prompt.py** (4 connections) — `tests/unit/test_interactive_prompt.py`
- **.test_writes_prompt_to_stdout_not_input_arg()** (2 connections) — `tests/unit/test_interactive_prompt.py`
- **Tests for handle_interactive_prompt (IP1, IP4).  ansible.builtin.pause and vars_** (1 connections) — `tests/unit/test_interactive_prompt.py`
- **AOMApp must implement handle_interactive_prompt via suspend + input.** (1 connections) — `tests/unit/test_interactive_prompt.py`
- **Same readline-routes-prompt-to-stderr bug applies to the TUI path.** (1 connections) — `tests/unit/test_interactive_prompt.py`
- **.test_keyboard_interrupt_propagates_so_run_can_abort()** (1 connections) — `tests/unit/test_interactive_prompt.py`
- **.test_method_exists()** (1 connections) — `tests/unit/test_interactive_prompt.py`
- **.test_returns_empty_on_eof()** (1 connections) — `tests/unit/test_interactive_prompt.py`
- **.test_suspends_then_reads_input()** (1 connections) — `tests/unit/test_interactive_prompt.py`

## Relationships

- [App Configuration Settings](App_Configuration_Settings.md) (2 shared connections)
- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (1 shared connections)

## Source Files

- `tests/unit/test_interactive_prompt.py`

## Audit Trail

- EXTRACTED: 20 (95%)
- INFERRED: 1 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*