# AOMApp

> God node · 181 connections · `src/ansible_aom/tui/app.py`

**Community:** [Session Recording Tests](Session_Recording_Tests.md)

## Connections by Relation

### calls
- create_renderer() `INFERRED`
- .test_update_from_state_drops_completed_tasks() `INFERRED`
- .test_update_from_state_keeps_running_task_visible() `INFERRED`
- .test_update_from_state_shows_ok_icon_after_completion() `INFERRED`
- .test_three_task_starts_appear_in_tree() `INFERRED`
- .test_tick_refreshes_widgets_after_event() `INFERRED`
- .test_handles_empty_host_set() `INFERRED`
- .test_shows_failed_hosts() `INFERRED`
- .test_shows_planned_command() `INFERRED`
- .test_shows_unreachable_hosts() `INFERRED`
- .test_update_from_state_populates_tree_from_definitions() `INFERRED`
- .test_cancel_returns_false() `INFERRED`
- .test_confirm_returns_true() `INFERRED`
- _run_tui() `INFERRED`
- _drive_tui() `INFERRED`
- .test_handle_interactive_prompt_returns_answer_from_worker() `INFERRED`
- .test_worker_invokes_run_playbook() `INFERRED`
- .test_add_warning_from_worker_lands_on_status_bar() `INFERRED`
- .test_completion_nonzero_marks_title_with_cross() `INFERRED`
- .test_completion_zero_marks_title_with_check() `INFERRED`

### contains
- app.py `EXTRACTED`

### indirect_call
- test_factory_tui_mode_still_wins_over_format() `INFERRED`

### method
- .__init__() `EXTRACTED`
- ._safe_call_from_thread() `EXTRACTED`
- ._refresh_widgets() `EXTRACTED`
- .action_quit() `EXTRACTED`
- .action_rerun_with_modified_args() `EXTRACTED`
- .action_rerun_with_same_args() `EXTRACTED`
- .action_show_help() `EXTRACTED`
- .action_show_settings() `EXTRACTED`
- .action_toggle_debug() `EXTRACTED`
- .add_warning() `EXTRACTED`
- .handle_completion() `EXTRACTED`
- .on_mount() `EXTRACTED`
- .print_log() `EXTRACTED`
- ._run_playbook_worker() `EXTRACTED`
- .run_state() `EXTRACTED`
- .start() `EXTRACTED`
- .update_state() `EXTRACTED`
- .handle_interactive_prompt() `EXTRACTED`
- .handle_password_prompt() `EXTRACTED`
- .note_pty_bytes() `EXTRACTED`

### rationale_for
- Textual-based TUI renderer satisfying the Renderer Protocol.      See SPECIFICAT `EXTRACTED`

### uses
- [RunState](RunState.md) `INFERRED`
- JsonlEvent `INFERRED`
- [MainScreen](MainScreen.md) `INFERRED`
- TestHideStateFlag `INFERRED`
- [RerunDialog](RerunDialog.md) `INFERRED`
- TestPasswordPromptPTYIntegration `INFERRED`
- KeyContext `INFERRED`
- HelpOverlay `INFERRED`
- TestRendererProtocol `INFERRED`
- TestHideStateCompactPlumbing `INFERRED`
- TestNoRedactFlag `INFERRED`
- TestRendererFactory `INFERRED`
- TestFormatFlag `INFERRED`
- TestPackageIdentity `INFERRED`
- TestDirtyCounter `INFERRED`
- TestYesFlag `INFERRED`
- TestMainScreenTreeIntegration `INFERRED`
- TestCLIEntryPoint `INFERRED`
- TestConfigPathFlag `INFERRED`
- TestCoreModuleStructure `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*