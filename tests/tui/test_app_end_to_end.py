"""End-to-end tests for AOMApp wired to the pexpect runner (roadmap #9).

The TUI previously couldn't actually display anything: `cli.py` called
`run_playbook(playbook, args, aom_app)` which ran the pexpect loop
synchronously and never started Textual's own event loop. This module
covers the new architecture where:

- AOMApp accepts playbook/args (so cli.py can build it once)
- on_mount() kicks off the runner in a Textual worker thread
- Renderer Protocol methods (start / update_state / handle_completion /
  add_warning / print_log) mutate a RunState the widgets read from
- Widget refreshes are scheduled via call_from_thread so the worker
  never touches Textual state directly

Pilot drives a real Textual app in an asyncio test, with the runner
substituted by a fake that emits canned events.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ansible_aom.core.models import RunState
from ansible_aom.tui.app import AOMApp


class TestAOMAppConstruction:
    """AOMApp must accept playbook+args in its constructor."""

    def test_app_accepts_playbook_and_args(self) -> None:
        app = AOMApp(playbook="site.yml", ansible_args=["-v"])
        assert app.playbook == "site.yml"
        assert app.ansible_args == ["-v"]

    def test_app_defaults_when_no_args(self) -> None:
        """Construction without args keeps old behaviour (no-arg tests still pass)."""
        app = AOMApp()
        assert app.playbook is None
        assert app.ansible_args == []


class TestRunStateOwnership:
    """AOMApp must own a RunState so widgets can read mutated state."""

    def test_app_has_runstate_after_start(self) -> None:
        app = AOMApp()
        app.start("site.yml", ["-v"])
        assert isinstance(app.run_state, RunState)
        assert app.run_state.playbook == "site.yml"

    def test_update_state_routes_event_to_runstate(self) -> None:
        app = AOMApp()
        app.start("site.yml", [])
        app.update_state(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-11T10:00:00Z",
                "play": {"id": "p1", "name": "Setup"},
            }
        )
        assert "p1" in app.run_state.plays
        assert app.run_state.plays["p1"].name == "Setup"

    def test_handle_completion_stores_exit_code_and_state(self) -> None:
        app = AOMApp()
        app.start("site.yml", [])
        app.handle_completion(2, "failed")
        assert app.exit_code == 2
        assert app.final_state == "failed"

    def test_set_definitions_stored_on_app(self) -> None:
        from ansible_aom.core.models import PlayDefinition

        app = AOMApp()
        app.start("site.yml", [])
        defs = [PlayDefinition(id="1", name="P", hosts="all")]
        app.set_definitions(defs)
        assert app.run_state.definitions == defs


class TestWarningsAndLogsRoutedToState:
    """add_warning / print_log must accumulate so widgets can show them."""

    def test_add_warning_increments_counter(self) -> None:
        app = AOMApp()
        app.start("site.yml", [])
        app.add_warning("[WARNING]: missing role 'x'")
        app.add_warning("[DEPRECATION WARNING]: foo", is_deprecation=True)
        assert app.warnings_count == 1
        assert app.deprecations_count == 1

    def test_print_log_appends_line(self) -> None:
        app = AOMApp()
        app.start("site.yml", [])
        app.print_log("TASK [Install nginx] ***")
        app.print_log("ok: [web1]")
        assert app.log_lines[-2:] == [
            "TASK [Install nginx] ***",
            "ok: [web1]",
        ]


class TestAOMAppInteractivePromptDuringRun:
    """The worker thread can invoke handle_interactive_prompt safely.

    Pilot mounts the real app; we patch ``input`` so the test doesn't
    actually wait on stdin. The point is to verify the worker can call
    ``app.handle_interactive_prompt(...)`` and get back a value without
    deadlocking the Textual event loop.
    """

    @pytest.mark.asyncio
    async def test_handle_interactive_prompt_returns_answer_from_worker(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from threading import Event

        prompt_done = Event()
        captured_answer: list[str] = []

        def fake_run_playbook(
            playbook: str,
            ansible_args: list[str],
            renderer: object,
            timeout: float = 0.5,
            session_dir: Path | None = None,
            record: bool = True,
        ) -> int:
            renderer.start(playbook, ansible_args)  # type: ignore[attr-defined]
            answer = renderer.handle_interactive_prompt("Deploy? Press Enter: ")  # type: ignore[attr-defined]
            captured_answer.append(answer)
            prompt_done.set()
            renderer.handle_completion(0, "completed")  # type: ignore[attr-defined]
            return 0

        monkeypatch.setattr("ansible_aom.ansible.runner.run_playbook", fake_run_playbook)
        # Patch input() globally — the worker thread will call it.
        monkeypatch.setattr("builtins.input", lambda *_: "yes")

        app = AOMApp(playbook="site.yml", ansible_args=[], session_dir=tmp_path)

        # `self.suspend()` blocks waiting for a terminal handoff that
        # never happens inside `run_test()`. Replace it with an inert
        # context manager so the prompt path can complete.
        class _NoopSuspend:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

        monkeypatch.setattr(app, "suspend", lambda: _NoopSuspend())

        async with app.run_test() as pilot:
            for _ in range(50):
                if prompt_done.is_set():
                    break
                await pilot.pause(0.02)
            assert prompt_done.is_set(), "interactive prompt never completed"

        assert captured_answer == ["yes"]
        assert app.exit_code == 0


class TestWorkerKickoff:
    """on_mount must arrange for the runner to execute in a worker thread.

    We don't want to actually run pexpect in this test — patch
    `run_playbook` to a recording stub and assert it's invoked with the
    app as renderer once the worker fires.
    """

    @pytest.mark.asyncio
    async def test_worker_invokes_run_playbook(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from threading import Event

        called = Event()
        captured: dict[str, object] = {}

        def fake_run_playbook(
            playbook: str,
            ansible_args: list[str],
            renderer: object,
            timeout: float = 0.5,
            session_dir: Path | None = None,
            record: bool = True,
        ) -> int:
            captured["playbook"] = playbook
            captured["ansible_args"] = list(ansible_args)
            captured["renderer_is_app"] = renderer is app
            captured["session_dir"] = session_dir
            called.set()
            # Simulate a single event going through the renderer surface.
            renderer.start(playbook, ansible_args)  # type: ignore[attr-defined]
            renderer.handle_completion(0, "completed")  # type: ignore[attr-defined]
            return 0

        monkeypatch.setattr("ansible_aom.ansible.runner.run_playbook", fake_run_playbook)

        app = AOMApp(playbook="site.yml", ansible_args=["-v"], session_dir=tmp_path)

        async with app.run_test() as pilot:
            # Pump the event loop until the worker has dispatched.
            for _ in range(50):
                if called.is_set():
                    break
                await pilot.pause(0.02)
            assert called.is_set(), "run_playbook worker never fired"
            # Let any post-completion call_from_thread updates drain.
            await pilot.pause(0.05)

        assert captured["playbook"] == "site.yml"
        assert captured["ansible_args"] == ["-v"]
        assert captured["renderer_is_app"] is True
        assert captured["session_dir"] == tmp_path
        assert app.exit_code == 0
        assert app.final_state == "completed"
