# PtyStreamParser

> God node · 338 connections · `src/ansible_aom/core/parser.py`

**Community:** [PtyStreamParser](PtyStreamParser.md)

## Connections by Relation

### calls
- run_playbook() `EXTRACTED`
- .test_watchdog_emits_warning_and_returns_when_no_eof() `EXTRACTED`
- .test_watchdog_emits_warning_via_logger() `EXTRACTED`
- .test_watchdog_path_calls_expect() `EXTRACTED`
- .test_clean_eof_after_stats_no_warning() `EXTRACTED`
- .test_pre_stats_timeout_does_not_trigger_watchdog() `EXTRACTED`
- test_drive_feeds_each_event_when_pexpect_returns_multi_event_blob() `INFERRED`
- test_post_stats_watchdog_drops_to_quiet_after_end_time() `EXTRACTED`
- test_pre_end_time_uses_full_watchdog() `EXTRACTED`
- test_feed_without_diag_does_not_crash() `EXTRACTED`
- .test_v2_playbook_on_stats_event() `EXTRACTED`
- .test_v2_runner_on_failed_event() `EXTRACTED`
- .test_v2_runner_on_ok_event() `EXTRACTED`
- .test_multi_host_mixed_fixture() `EXTRACTED`
- .test_playbook_failed_fixture() `EXTRACTED`
- .test_single_task_ok_fixture() `EXTRACTED`
- .test_plaintext_line_notes_pty_bytes() `EXTRACTED`
- .test_v2_playbook_on_start_event() `EXTRACTED`
- .test_replacement_char_in_plaintext_line_is_recorded_not_crashed() `EXTRACTED`
- test_recap_lines_capped_at_max_log_lines() `EXTRACTED`

### contains
- parser.py `EXTRACTED`

### imports
- [runner.py](runner.py.md) `EXTRACTED`

### method
- .feed_line() `EXTRACTED`
- ._handle_plaintext() `EXTRACTED`
- ._parse_and_return() `EXTRACTED`
- .drain_warnings() `EXTRACTED`
- ._handle_connection_event() `EXTRACTED`
- ._is_json() `EXTRACTED`
- ._is_jsonl_start_event() `EXTRACTED`
- ._is_jsonl_stats_event() `EXTRACTED`
- ._parse_json() `EXTRACTED`
- ._resolve_connection() `EXTRACTED`
- .clear_password_prompt() `EXTRACTED`
- ._handle_recap_output() `EXTRACTED`
- .latest_output_is_plaintext() `EXTRACTED`
- .warnings() `EXTRACTED`
- .__init__() `EXTRACTED`
- .pending_password_prompt() `EXTRACTED`
- .plaintext_lines() `EXTRACTED`
- .recap_lines() `EXTRACTED`

### rationale_for
- 3-phase parser for ansible-playbook PTY output. `EXTRACTED`

### references
- parse_jsonl_output() `EXTRACTED`
- _drive() `EXTRACTED`
- _feed() `EXTRACTED`
- _flush_pending() `EXTRACTED`
- _drive_short() `EXTRACTED`
- _parser_in_execution_phase() `EXTRACTED`
- _build_parser_in_post_run_recap() `EXTRACTED`
- _execution_parser() `EXTRACTED`
- _execution_parser() `EXTRACTED`

### uses
- [PlayDefinition](PlayDefinition.md) `INFERRED`
- [RoleGroupDefinition](RoleGroupDefinition.md) `INFERRED`
- [WarningType](WarningType.md) `INFERRED`
- [WarningEntry](WarningEntry.md) `INFERRED`
- JsonlEvent `INFERRED`
- [IncludeCacheEntry](IncludeCacheEntry.md) `INFERRED`
- TestPtyStreamParserStderrLineEmission `INFERRED`
- TestJsonLineStreamBasics `INFERRED`
- TestListTasksEdgeCases `INFERRED`
- TestListTasksParser `INFERRED`
- [TestPtyStreamParserPhases](TestPtyStreamParserPhases.md) `INFERRED`
- TestListHostsEdgeCases `INFERRED`
- _SessionSink `INFERRED`
- [TestRoleGrouping](TestRoleGrouping.md) `INFERRED`
- TestJsonLineStreamCarryBuffer `INFERRED`
- TestListHostsParser `INFERRED`
- TestRunStateUnknownEvent `INFERRED`
- _NullSink `INFERRED`
- TestMultiLineWarningContinuation `INFERRED`
- TestPtyStreamParserJsonlEvents `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*