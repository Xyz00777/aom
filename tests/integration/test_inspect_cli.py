"""Integration tests for the rebuilt `aom inspect` CLI."""

import shutil
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures" / "sessions"

_ALIASES = {
    "clean_run": "019e4000-0000-7000-8000-000000000001",
    "failed_loop": "019e4520-fa64-7000-a627-000000000002",
    "multi_host": "019e4100-0000-7000-8000-000000000003",
}


@pytest.fixture
def state_dir(tmp_path: Path) -> Path:
    state = tmp_path / "sessions"
    state.mkdir()
    for name, sid in _ALIASES.items():
        shutil.copytree(FIXTURES / sid, state / sid)
    return state


def test_text_mode_dumps_latest_session(state_dir: Path, capsys):
    from ansible_aom.inspect.cli import main

    exit_code = main(["--text", "--state-dir", str(state_dir)])
    assert exit_code == 0
    captured = capsys.readouterr()
    # failed_loop is the latest; should be the one rendered.
    assert "019e4520" in captured.out
    assert "One or more items failed" in captured.out


def test_text_mode_with_empty_state_returns_zero_and_message(tmp_path: Path, capsys):
    state = tmp_path / "sessions"
    state.mkdir()
    from ansible_aom.inspect.cli import main

    exit_code = main(["--text", "--state-dir", str(state)])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "No sessions" in out


def test_no_arg_invocation_falls_back_to_text_when_non_tty(state_dir: Path, capsys):
    from ansible_aom.inspect.cli import main

    # When stdout is not a TTY (capsys redirects), the no-arg invocation
    # auto-falls-back to text mode rather than launching the TUI.
    exit_code = main(["--state-dir", str(state_dir)])
    assert exit_code == 0
    assert "019e4520" in capsys.readouterr().out


def test_prune_subcommand(state_dir: Path, capsys):
    from ansible_aom.inspect.cli import main

    # All fixture sessions are well within 10000 days, so this is a no-op cleanup.
    exit_code = main(["--state-dir", str(state_dir), "prune", "--days", "10000"])
    assert exit_code == 0
    assert "Pruned" in capsys.readouterr().out


def test_old_list_subcommand_is_gone(state_dir: Path):
    from ansible_aom.inspect.cli import main

    # `list` used to be a subcommand; it is now removed.
    with pytest.raises(SystemExit):
        main(["--state-dir", str(state_dir), "list"])


def test_old_show_subcommand_is_gone(state_dir: Path):
    from ansible_aom.inspect.cli import main

    with pytest.raises(SystemExit):
        main(["--state-dir", str(state_dir), "show", "019e4520"])


def test_old_diff_subcommand_is_gone(state_dir: Path):
    from ansible_aom.inspect.cli import main

    with pytest.raises(SystemExit):
        main(["--state-dir", str(state_dir), "diff", "id1", "id2"])


def test_text_mode_with_play_flag(state_dir: Path, capsys):
    from ansible_aom.inspect.cli import main

    exit_code = main(["--text", "--state-dir", str(state_dir), "--play", "web"])
    assert exit_code == 0
    captured = capsys.readouterr()
    # Play scoping appears in the Verbose header if there are stderr events.
    # Even without stderr events, the session still renders.
    assert "019e4520" in captured.out


def test_text_mode_with_task_flag(state_dir: Path, capsys):
    from ansible_aom.inspect.cli import main

    exit_code = main(["--text", "--state-dir", str(state_dir), "--task", "some task"])
    assert exit_code == 0
    captured = capsys.readouterr()
    # Task scoping appears in the Verbose header if there are stderr events.
    assert "019e4520" in captured.out


def test_text_mode_with_play_and_task_flags(state_dir: Path, capsys):
    from ansible_aom.inspect.cli import main

    exit_code = main(
        [
            "--text",
            "--state-dir",
            str(state_dir),
            "--play",
            "web",
            "--task",
            "some task",
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "019e4520" in captured.out


def test_inspect_changes_cli(state_dir: Path, capsys):
    from ansible_aom.inspect.cli import main

    exit_code = main(["--changes", "--state-dir", str(state_dir)])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Changed Tasks" in out


def test_inspect_changes_json_cli(state_dir: Path, capsys):
    import json

    from ansible_aom.inspect.cli import main

    exit_code = main(["--changes", "--json", "--state-dir", str(state_dir)])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert "total_changes" in payload
    assert "changes" in payload


def test_inspect_warnings_cli(state_dir: Path, capsys):
    from ansible_aom.inspect.cli import main

    exit_code = main(["--warnings", "--state-dir", str(state_dir)])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Warnings & Deprecations" in out


def test_inspect_warnings_json_cli(state_dir: Path, capsys):
    import json

    from ansible_aom.inspect.cli import main

    exit_code = main(["--warnings", "--json", "--state-dir", str(state_dir)])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert "total_warnings" in payload
    assert "warnings" in payload


def test_text_mode_with_explicit_older_session(state_dir: Path, capsys):
    from ansible_aom.inspect.cli import main

    clean_run = _ALIASES["clean_run"]
    exit_code = main(["--text", "--state-dir", str(state_dir), "--session", clean_run])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert clean_run in out
    assert _ALIASES["failed_loop"] not in out


def test_text_mode_with_unknown_session_errors(state_dir: Path, capsys):
    from ansible_aom.inspect.cli import main

    exit_code = main(["--text", "--state-dir", str(state_dir), "--session", "nope"])
    assert exit_code != 0
    captured = capsys.readouterr()
    assert "Session not found: nope" in captured.err
    assert _ALIASES["failed_loop"] not in captured.out


class _FakeInspectApp:
    launched_with: list[str | None] = []

    def __init__(self, *, state_dir: Path, initial_session_id: str | None = None) -> None:
        self.initial_session_id = initial_session_id

    def run(self) -> None:
        _FakeInspectApp.launched_with.append(self.initial_session_id)


@pytest.fixture
def fake_tui(monkeypatch):
    import ansible_aom.inspect.cli as cli
    import ansible_aom.tui.screens.inspect as inspect_screen

    _FakeInspectApp.launched_with = []
    monkeypatch.setattr(cli, "_stdout_is_tty", lambda: True)
    monkeypatch.setattr(cli, "prewarm_parallel_pool", lambda: None)
    monkeypatch.setattr(inspect_screen, "InspectApp", _FakeInspectApp)
    return _FakeInspectApp.launched_with


def test_tui_opens_latest_session_by_default(state_dir: Path, fake_tui):
    from ansible_aom.inspect.cli import main

    assert main(["--state-dir", str(state_dir)]) == 0
    assert fake_tui == [_ALIASES["failed_loop"]]


def test_tui_opens_explicit_session(state_dir: Path, fake_tui):
    from ansible_aom.inspect.cli import main

    clean_run = _ALIASES["clean_run"]
    assert main(["--state-dir", str(state_dir), "--session", clean_run]) == 0
    assert fake_tui == [clean_run]


def test_tui_with_unknown_session_errors_without_launching(state_dir: Path, fake_tui, capsys):
    from ansible_aom.inspect.cli import main

    assert main(["--state-dir", str(state_dir), "--session", "nope"]) != 0
    assert fake_tui == []
    assert "Session not found: nope" in capsys.readouterr().err
