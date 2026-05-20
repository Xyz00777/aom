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
