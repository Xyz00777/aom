# Renderer ETA Wiring

> 23 nodes · cohesion 0.09

## Key Concepts

- **TestLooksLikePrompt** (14 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_log_line_containing_bracketed_word_is_not_a_prompt()** (2 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_no_terminator_is_not_a_prompt()** (2 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_prior_plaintext_header_catches_split_chunks()** (2 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_prior_plaintext_non_header_does_not_catch()** (2 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_real_ansible_pause_no_press_enter_phrasing_still_caught()** (2 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_real_ansible_pause_with_ansi_codes_is_caught()** (2 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_real_ansible_pause_with_plain_colon_and_header()** (2 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_trailing_colon_without_marker_is_NOT_a_prompt()** (2 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_vars_prompt_default_format_is_caught()** (2 connections) — `tests/unit/test_runner_stall_flush.py`
- **Header + bare colon (no markers, no question mark) is still a prompt.** (1 connections) — `tests/unit/test_runner_stall_flush.py`
- **When the header was consumed earlier and only the prompt tail         sits in th** (1 connections) — `tests/unit/test_runner_stall_flush.py`
- **An ordinary log line as the prior plaintext is not a signal.** (1 connections) — `tests/unit/test_runner_stall_flush.py`
- **The heuristic used to gate the blocking-input path.** (1 connections) — `tests/unit/test_runner_stall_flush.py`
- **Pure ``something:`` is too risky — many debug tasks end in colon.** (1 connections) — `tests/unit/test_runner_stall_flush.py`
- **No colon, no question mark → don't treat as prompt.** (1 connections) — `tests/unit/test_runner_stall_flush.py`
- **ansible vars_prompt without custom text uses ``[name]: ``.** (1 connections) — `tests/unit/test_runner_stall_flush.py`
- **Defensive: don't false-positive on log lines mentioning [INFO].** (1 connections) — `tests/unit/test_runner_stall_flush.py`
- **Real ansible colorises pause output — buffer ends in ``\\x1b[0m``.          With** (1 connections) — `tests/unit/test_runner_stall_flush.py`
- **A custom pause prompt without the canonical phrasing.          The user-provided** (1 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_empty_buffer_is_not_a_prompt()** (1 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_known_marker_with_colon_is_prompt()** (1 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_question_mark_alone_is_a_prompt()** (1 connections) — `tests/unit/test_runner_stall_flush.py`

## Relationships

- [CLI Main Entry Point](CLI_Main_Entry_Point.md) (1 shared connections)

## Source Files

- `tests/unit/test_runner_stall_flush.py`

## Audit Trail

- EXTRACTED: 45 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*