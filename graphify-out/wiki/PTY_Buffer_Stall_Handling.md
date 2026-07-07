# PTY Buffer Stall Handling

> 50 nodes · cohesion 0.07

## Key Concepts

- **_handle_timeout_branch()** (27 connections) — `src/ansible_aom/ansible/runner.py`
- **_FakeSink** (21 connections) — `tests/unit/test_runner_stall_flush.py`
- **_FakeChild** (20 connections) — `tests/unit/test_runner_stall_flush.py`
- **test_runner_stall_flush.py** (10 connections) — `tests/unit/test_runner_stall_flush.py`
- **_fire_prompt()** (8 connections) — `src/ansible_aom/ansible/runner.py`
- **_peek_unread()** (6 connections) — `src/ansible_aom/ansible/runner.py`
- **TestStallFlushDoesNotBlock** (6 connections) — `tests/unit/test_runner_stall_flush.py`
- **_consume_unread()** (5 connections) — `src/ansible_aom/ansible/runner.py`
- **.test_renderer_crash_sends_empty_line_to_avoid_hang()** (5 connections) — `tests/unit/test_runner_stall_flush.py`
- **TestMultilinePauseBlock** (5 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_no_block_and_bare_colon_prior_does_not_fire()** (5 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_prior_non_prompt_does_not_fire()** (5 connections) — `tests/unit/test_runner_stall_flush.py`
- **TestSentinelPreventsRefiring** (5 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_negative_stall_count_with_prior_prompt_still_skips()** (5 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_prompt_path_emits_visible_breadcrumb()** (5 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_quiet_child_just_ticks()** (5 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_hint_only_fires_once()** (5 connections) — `tests/unit/test_runner_stall_flush.py`
- **TestHighConfidencePromptPath** (4 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_known_prompt_drains_buffer_and_calls_handler()** (4 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_reconstructed_block_fires_prompt()** (4 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_sentinel_blocks_reconstructed_block_refiring()** (4 connections) — `tests/unit/test_runner_stall_flush.py`
- **TestPriorPlaintextPromptPath** (4 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_prior_prompt_with_empty_buffer_fires()** (4 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_negative_stall_count_skips_prompt_path()** (4 connections) — `tests/unit/test_runner_stall_flush.py`
- **.test_at_threshold_flushes_buffer_as_log()** (4 connections) — `tests/unit/test_runner_stall_flush.py`
- *... and 25 more nodes in this community*

## Relationships

- [[Runner Session Recording]] (12 shared connections)
- [[Renderer Event Protocol]] (2 shared connections)
- [[Pause Prompt Heuristic]] (1 shared connections)

## Source Files

- `src/ansible_aom/ansible/runner.py`
- `tests/unit/test_runner_stall_flush.py`

## Audit Trail

- EXTRACTED: 185 (85%)
- INFERRED: 32 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*