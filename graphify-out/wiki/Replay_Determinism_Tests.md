# Replay Determinism Tests

> 71 nodes · cohesion 0.05

## Key Concepts

- **run_playbook()** (85 connections) — `src/ansible_aom/ansible/runner.py`
- **Path** (17 connections)
- **test_runner_interactive_prompts.py** (11 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **_fake_pause_prompt_command()** (10 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **_fake_ansible_command()** (8 connections) — `tests/integration/test_runner.py`
- **test_runner.py** (7 connections) — `tests/integration/test_runner.py`
- **TestRunnerPreflight** (6 connections) — `tests/integration/test_runner.py`
- **TestNewlineTerminatedPromptPath** (5 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **._fake_newline_terminated_prompt()** (5 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_pause_prompt_answer_forwarded_to_child()** (5 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_custom_pause_prompt_without_press_enter_phrasing()** (5 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_default_bracketed_format_is_caught()** (5 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_question_mark_prompt_is_caught()** (5 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **TestRunnerHappyPath** (5 connections) — `tests/integration/test_runner.py`
- **.test_yes_no_prompt_triggers_handler()** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **TestKeyboardInterruptDuringPromptAborts** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **._fake_pause_with_capture()** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_ctrl_c_at_prompt_returns_130_not_zero()** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **TestMultilineBlockPromptColonOnOwnLine** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_colon_on_own_line_block_round_trip()** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_newline_terminated_vars_prompt_round_trip()** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_real_ansible_pause_newline_terminated_round_trip()** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **TestNoPromptNoSpuriousInteractiveCall** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **TestPausePromptDetected** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- **.test_pause_prompt_triggers_handle_interactive_prompt()** (4 connections) — `tests/integration/test_runner_interactive_prompts.py`
- *... and 46 more nodes in this community*

## Relationships

- [Tree Block Animation](Tree_Block_Animation.md) (12 shared connections)
- [Status Color Mapping](Status_Color_Mapping.md) (8 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (6 shared connections)
- [Task Tree Navigation](Task_Tree_Navigation.md) (4 shared connections)
- [Renderer Protocol Tests](Renderer_Protocol_Tests.md) (3 shared connections)
- [Host Overview Table](Host_Overview_Table.md) (3 shared connections)
- [Host Collection Helpers](Host_Collection_Helpers.md) (3 shared connections)
- [Loop Item Stream Tests](Loop_Item_Stream_Tests.md) (2 shared connections)
- [JSON Renderer](JSON_Renderer.md) (2 shared connections)
- [Interactive Prompt Tests](Interactive_Prompt_Tests.md) (2 shared connections)
- [Rerun Subcommand Module](Rerun_Subcommand_Module.md) (2 shared connections)
- [.test_record_false_does_not_touch_default_state_dir](test_record_false_does_not_touch_default_state_dir.md) (2 shared connections)

## Source Files

- `src/ansible_aom/ansible/runner.py`
- `tests/integration/test_runner.py`
- `tests/integration/test_runner_interactive_prompts.py`

## Audit Trail

- EXTRACTED: 227 (72%)
- INFERRED: 88 (28%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*