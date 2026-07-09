# Execution State Transitions

> 62 nodes · cohesion 0.03

## Key Concepts

- **test_pty_stream.py** (16 connections) — `tests/unit/test_pty_stream.py`
- **TestCompactModePasswordPassThrough** (10 connections) — `tests/unit/test_pty_stream.py`
- **TestMixedStreamHandling** (10 connections) — `tests/unit/test_pty_stream.py`
- **TestPasswordPromptHandling** (10 connections) — `tests/unit/test_pty_stream.py`
- **TestPatternRegexes** (8 connections) — `tests/unit/test_pty_stream.py`
- **TestPhaseStateMachine** (8 connections) — `tests/unit/test_pty_stream.py`
- **TestRendererProtocolPasswordHandling** (8 connections) — `tests/unit/test_pty_stream.py`
- **.test_clear_password_prompt_allows_next_detection()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_exact_text_stored()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_multiple_types()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_not_json_event()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_sets_pending_state()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_invalid_json_returns_empty()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_jsonl_and_plaintext_interleaved()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_jsonl_returns_events()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_plaintext_before_jsonl_start()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_plaintext_returns_stderr_line()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_multiple_password_prompts_replaced()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_cleared_after_handling()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_in_recap_phase()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_pending_state()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_password_prompt_preserved_across_phases()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_cannot_go_backwards_from_execution()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_phase_properties_immutability()** (3 connections) — `tests/unit/test_pty_stream.py`
- **.test_phase_transition_order()** (3 connections) — `tests/unit/test_pty_stream.py`
- *... and 37 more nodes in this community*

## Relationships

- [Run State Completion Recap](Run_State_Completion_Recap.md) (34 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (7 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (6 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `tests/unit/test_pty_stream.py`

## Audit Trail

- EXTRACTED: 131 (77%)
- INFERRED: 39 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*