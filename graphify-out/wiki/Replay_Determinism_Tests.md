# Replay Determinism Tests

> 42 nodes · cohesion 0.08

## Key Concepts

- **Path** (15 connections)
- **test_runner_interactive_prompts.py** (10 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **_fake_pause_prompt_command()** (10 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **TestNewlineTerminatedPromptPath** (5 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **._fake_newline_terminated_prompt()** (5 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_pause_prompt_answer_forwarded_to_child()** (5 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_custom_pause_prompt_without_press_enter_phrasing()** (5 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_default_bracketed_format_is_caught()** (5 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_question_mark_prompt_is_caught()** (5 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_yes_no_prompt_triggers_handler()** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **TestKeyboardInterruptDuringPromptAborts** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **._fake_pause_with_capture()** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_ctrl_c_at_prompt_returns_130_not_zero()** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **TestMultilineBlockPromptColonOnOwnLine** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_colon_on_own_line_block_round_trip()** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_newline_terminated_vars_prompt_round_trip()** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_real_ansible_pause_newline_terminated_round_trip()** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **TestPausePromptDetected** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_pause_prompt_triggers_handle_interactive_prompt()** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **TestRealAnsiblePauseFormat** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_full_real_ansible_pause_round_trip()** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **TestVarsPromptDetected** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **TestConfirmationPromptDetected** (3 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **._fake_block_prompt()** (3 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **TestNoPromptNoSpuriousInteractiveCall** (3 connections) — `tests/integration/test_runner_interactive_prompts.py`
- *... and 17 more nodes in this community*

## Relationships

- [Tree Block Animation](Tree_Block_Animation.md) (12 shared connections)

## Source Files

- `tests/integration/test_runner_interactive_prompts.py`

## Audit Trail

- EXTRACTED: 132 (92%)
- INFERRED: 12 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*