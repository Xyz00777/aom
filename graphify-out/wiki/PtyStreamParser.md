# PtyStreamParser

> God node · 280 connections · `src/ansible_aom/core/parser.py`

**Community:** [[PTY Stream Parser]]

## Connections by Relation

### calls
- [[run_playbook()]] `EXTRACTED`
- [[.test_v2_playbook_on_stats_event()]] `EXTRACTED`
- [[.test_v2_runner_on_failed_event()]] `EXTRACTED`
- [[.test_v2_runner_on_ok_event()]] `EXTRACTED`
- [[.test_multi_host_mixed_fixture()]] `EXTRACTED`
- [[.test_playbook_failed_fixture()]] `EXTRACTED`
- [[.test_single_task_ok_fixture()]] `EXTRACTED`
- [[test_feed_without_diag_does_not_crash()]] `EXTRACTED`
- [[.test_v2_playbook_on_start_event()]] `EXTRACTED`
- [[.test_replacement_char_in_plaintext_line_is_recorded_not_crashed()]] `INFERRED`
- [[.test_plaintext_line_notes_pty_bytes()]] `EXTRACTED`
- [[.test_malformed_jsonl_does_not_crash()]] `INFERRED`
- [[.test_valid_json_following_malformed_still_parsed()]] `INFERRED`
- [[.test_password_patterns_defined()]] `INFERRED`
- [[.test_password_prompt_detected_patterns()]] `INFERRED`
- [[.test_become_password_prompt_detected()]] `EXTRACTED`
- [[.test_clear_password_prompt()]] `EXTRACTED`
- [[.test_ssh_password_prompt_detected()]] `EXTRACTED`
- [[.test_vault_password_prompt_detected()]] `EXTRACTED`
- [[.test_execution_to_post_run_on_stats_event()]] `EXTRACTED`

### contains
- [[parser.py]] `EXTRACTED`

### method
- [[.feed_line()]] `EXTRACTED`
- [[._handle_plaintext()]] `EXTRACTED`
- [[.drain_warnings()]] `EXTRACTED`
- [[._is_json()]] `EXTRACTED`
- [[._is_jsonl_start_event()]] `EXTRACTED`
- [[._is_jsonl_stats_event()]] `EXTRACTED`
- [[._parse_and_return()]] `EXTRACTED`
- [[.clear_password_prompt()]] `EXTRACTED`
- [[._handle_recap_output()]] `EXTRACTED`
- [[._parse_json()]] `EXTRACTED`
- [[.warnings()]] `EXTRACTED`
- [[.__init__()]] `EXTRACTED`
- [[.pending_password_prompt()]] `EXTRACTED`
- [[.plaintext_lines()]] `EXTRACTED`
- [[.recap_lines()]] `EXTRACTED`

### rationale_for
- [[3-phase parser for ansible-playbook PTY output.]] `EXTRACTED`

### references
- [[parse_jsonl_output()]] `EXTRACTED`
- [[_feed()]] `EXTRACTED`
- [[_drive()]] `EXTRACTED`
- [[_flush_pending()]] `EXTRACTED`
- [[_parser_in_execution_phase()]] `EXTRACTED`
- [[_execution_parser()]] `EXTRACTED`
- [[_execution_parser()]] `EXTRACTED`

### uses
- [[PlayDefinition]] `INFERRED`
- [[RoleGroupDefinition]] `INFERRED`
- [[WarningType]] `INFERRED`
- [[WarningEntry]] `INFERRED`
- [[IncludeCacheEntry]] `INFERRED`
- [[TestJsonLineStreamBasics]] `INFERRED`
- [[TestListTasksEdgeCases]] `INFERRED`
- [[TestListTasksParser]] `INFERRED`
- [[TestPtyStreamParserPhases]] `INFERRED`
- [[TestTaskMatching]] `INFERRED`
- [[TestListHostsEdgeCases]] `INFERRED`
- [[TestRoleGrouping]] `INFERRED`
- [[TestListHostsParser]] `INFERRED`
- [[TestTaskDefinition]] `INFERRED`
- [[TestJsonLineStreamCarryBuffer]] `INFERRED`
- [[TestRunStateUnknownEvent]] `INFERRED`
- [[_SessionSink]] `INFERRED`
- [[TestPlayDefinition]] `INFERRED`
- [[TestPtyStreamParserJsonlEvents]] `INFERRED`
- [[TestWarningDetectionThroughAnsiPrefix]] `INFERRED`

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*