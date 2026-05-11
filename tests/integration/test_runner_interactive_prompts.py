"""Integration tests for runner pause/vars_prompt handling (IP1, IP3).

These tests substitute a fake ansible-playbook that emits a prompt
without a trailing newline and then reads a line from stdin. The
runner must:

1. Detect the prompt via pattern matching.
2. Route through ``renderer.handle_interactive_prompt(prompt_text)``.
3. Forward the returned line via ``child.sendline(answer)``.
4. Let the fake process exit cleanly.

Proof that the answer reached the child: the fake writes whatever it
read from stdin into a tempfile the test then reads back.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch


def _fake_pause_prompt_command(
    prompt: str, captured_input_path: Path, exit_code: int = 0
) -> tuple[str, list[str]]:
    """Fake ansible-playbook: emit a prompt, read a line, write what it got to a file.

    The tempfile is the test's proof channel — pexpect's PTY echoes
    stdin which complicates parsing the runner's plaintext stream, so
    we route the assertion through the filesystem instead.
    """
    prompt_repr = repr(prompt)
    path_repr = repr(str(captured_input_path))
    code = textwrap.dedent(
        f"""
        import sys
        sys.stdout.write({prompt_repr})
        sys.stdout.flush()
        line = sys.stdin.readline().rstrip("\\r\\n")
        with open({path_repr}, "w") as f:
            f.write(line)
        sys.exit({exit_code})
        """
    )
    return sys.executable, ["-c", code]


class TestPausePromptDetected:
    """The classic ansible.builtin.pause prompt is caught and forwarded."""

    def test_pause_prompt_triggers_handle_interactive_prompt(self, tmp_path: Path) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        renderer.handle_interactive_prompt.return_value = "yes"
        captured = tmp_path / "captured.txt"
        cmd, args = _fake_pause_prompt_command(
            "[pause]\nDeploy to web1? Press Enter to continue or Ctrl+C to abort: ",
            captured,
        )

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook(
                "playbook.yml", [], renderer, timeout=0.2, session_dir=tmp_path
            )

        assert exit_code == 0
        renderer.handle_interactive_prompt.assert_called_once()
        called_with = renderer.handle_interactive_prompt.call_args.args[0]
        assert "Deploy to web1" in called_with
        assert "Press Enter" in called_with

    def test_pause_prompt_answer_forwarded_to_child(self, tmp_path: Path) -> None:
        """The renderer's returned answer must reach the child's stdin."""
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        renderer.handle_interactive_prompt.return_value = "yes"
        captured = tmp_path / "captured.txt"
        cmd, args = _fake_pause_prompt_command("[pause]\nPress Enter to continue: ", captured)

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], renderer, timeout=0.2, session_dir=tmp_path)

        assert captured.exists(), "fake never wrote the captured input file"
        assert captured.read_text() == "yes"


class TestVarsPromptDetected:
    """vars_prompt plain text uses a generic colon-terminated prompt."""

    def test_question_mark_prompt_is_caught(self, tmp_path: Path) -> None:
        """A trailing '?' is a strong enough signal on its own."""
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        renderer.handle_interactive_prompt.return_value = "production"
        captured = tmp_path / "captured.txt"
        cmd, args = _fake_pause_prompt_command("Which environment? ", captured)

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], renderer, timeout=0.2, session_dir=tmp_path)

        renderer.handle_interactive_prompt.assert_called_once()
        assert captured.exists()
        assert captured.read_text() == "production"

    def test_default_bracketed_format_is_caught(self, tmp_path: Path) -> None:
        """vars_prompt's default format is ``[name]: `` with no custom text."""
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        renderer.handle_interactive_prompt.return_value = "staging"
        captured = tmp_path / "captured.txt"
        cmd, args = _fake_pause_prompt_command("[deploy_env]: ", captured)

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], renderer, timeout=0.2, session_dir=tmp_path)

        renderer.handle_interactive_prompt.assert_called_once()
        assert captured.exists()
        assert captured.read_text() == "staging"


class TestConfirmationPromptDetected:
    """(yes/no) and [y/N] style prompts get the interactive treatment."""

    def test_yes_no_prompt_triggers_handler(self, tmp_path: Path) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        renderer.handle_interactive_prompt.return_value = "y"
        captured = tmp_path / "captured.txt"
        cmd, args = _fake_pause_prompt_command("Continue? (yes/no): ", captured)

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], renderer, timeout=0.2, session_dir=tmp_path)

        renderer.handle_interactive_prompt.assert_called_once()
        assert captured.exists()
        assert captured.read_text() == "y"


class TestRealAnsiblePauseFormat:
    """Simulate exactly what ansible.builtin.pause emits in production.

    ansible decorates the pause prompt with:
    - An ANSI SGR-coloured ``[<task name>]`` header on its own line
    - The user's ``prompt:`` text below, also coloured, ending with
      ``:`` then a SGR reset and no trailing newline.

    Reproduces the user's reported bug:
    ``prompt: "Deploy to {{ inventory_hostname }} ({{ env_domain }})?
    Press Enter to continue or Ctrl+C to abort"``.
    """

    def test_full_real_ansible_pause_round_trip(self, tmp_path: Path) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        renderer.handle_interactive_prompt.return_value = ""  # user pressed Enter
        captured = tmp_path / "captured.txt"

        # Mimics the bytes ansible-playbook actually writes when stdout
        # is a TTY (which it is under pexpect): SGR around the
        # bracketed task header AND around the prompt body, no
        # trailing newline.
        coloured_prompt = (
            "\x1b[1;35m[Confirm deployment]\x1b[0m\n"
            "\x1b[1;35mDeploy to web1 (example.com)?"
            " Press Enter to continue or Ctrl+C to abort:\x1b[0m"
        )
        cmd, args = _fake_pause_prompt_command(coloured_prompt, captured)

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook(
                "playbook.yml", [], renderer, timeout=0.2, session_dir=tmp_path
            )

        assert exit_code == 0
        renderer.handle_interactive_prompt.assert_called_once()
        # The fake captured an empty string — the runner forwarded our
        # "user pressed Enter" through sendline.
        assert captured.exists()
        assert captured.read_text() == ""

    def test_custom_pause_prompt_without_press_enter_phrasing(self, tmp_path: Path) -> None:
        """Even when the prompt text doesn't include 'Press Enter',
        the bracketed task-name header identifies it."""
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        renderer.handle_interactive_prompt.return_value = "go"
        captured = tmp_path / "captured.txt"
        # No `Press Enter`, no `(yes/no)`, just a custom prompt — but
        # the bracketed header + trailing colon is enough.
        prompt = "[Confirm rollback]\nReally proceed: "
        cmd, args = _fake_pause_prompt_command(prompt, captured)

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], renderer, timeout=0.2, session_dir=tmp_path)

        renderer.handle_interactive_prompt.assert_called_once()
        assert captured.exists()
        assert captured.read_text() == "go"


class TestNewlineTerminatedPromptPath:
    """The variant the user actually hit in production.

    ``ansible.builtin.pause`` emits its prompt with a trailing ``\\r\\n``
    even though it's waiting on stdin. pexpect's newline matcher
    consumes the line, ``child.buffer`` is empty when TIMEOUT fires,
    and the prompt sits in the parser's consumed-plaintext history.
    The runner must catch that via ``prior_plaintext``.
    """

    def _fake_newline_terminated_prompt(
        self, prompt_with_newline: str, captured_input_path: Path
    ) -> tuple[str, list[str]]:
        """Fake that writes a NEWLINE-terminated prompt, then reads."""
        prompt_repr = repr(prompt_with_newline)
        path_repr = repr(str(captured_input_path))
        code = textwrap.dedent(
            f"""
            import sys
            sys.stdout.write({prompt_repr})
            sys.stdout.flush()
            line = sys.stdin.readline().rstrip("\\r\\n")
            with open({path_repr}, "w") as f:
                f.write(line)
            sys.exit(0)
            """
        )
        return sys.executable, ["-c", code]

    def test_real_ansible_pause_newline_terminated_round_trip(self, tmp_path: Path) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        renderer.handle_interactive_prompt.return_value = ""  # Enter
        captured = tmp_path / "captured.txt"

        # Real bytes ansible-playbook writes for the user's playbook:
        # [Task name]\r\n + prompt body ending in `:\r\n`. Both lines
        # are newline-terminated so pexpect consumes them cleanly and
        # the unread buffer is empty when the child blocks on stdin.
        prompt = (
            "[Confirm deployment]\r\n"
            "Deploy to epistree (epistree.com)?"
            " Press Enter to continue or Ctrl+C to abort:\r\n"
        )
        cmd, args = self._fake_newline_terminated_prompt(prompt, captured)

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            exit_code = run_playbook(
                "playbook.yml", [], renderer, timeout=0.2, session_dir=tmp_path
            )

        assert exit_code == 0
        renderer.handle_interactive_prompt.assert_called_once()
        assert captured.exists()
        assert captured.read_text() == ""

    def test_newline_terminated_vars_prompt_round_trip(self, tmp_path: Path) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        renderer.handle_interactive_prompt.return_value = "staging"
        captured = tmp_path / "captured.txt"

        prompt = "[deploy_env]: \r\n"
        cmd, args = self._fake_newline_terminated_prompt(prompt, captured)

        with patch("ansible_aom.runner._build_command", return_value=(cmd, args)):
            run_playbook("playbook.yml", [], renderer, timeout=0.2, session_dir=tmp_path)

        renderer.handle_interactive_prompt.assert_called_once()
        assert captured.read_text() == "staging"


class TestNoPromptNoSpuriousInteractiveCall:
    """A normal run with no prompts must NOT call handle_interactive_prompt."""

    def test_normal_jsonl_run_does_not_call_interactive_prompt(self) -> None:
        from ansible_aom.runner import run_playbook

        renderer = MagicMock()
        # Fake emits two JSONL events terminated by newlines — no stall.
        code = (
            "import sys, json; "
            "sys.stdout.write(json.dumps({'_event':'v2_playbook_on_start','_timestamp':'x'})+'\\n'); "
            "sys.stdout.write(json.dumps({'_event':'v2_playbook_on_stats','_timestamp':'x'})+'\\n'); "
            "sys.stdout.flush(); sys.exit(0)"
        )
        cmd = (sys.executable, ["-c", code])

        with patch("ansible_aom.runner._build_command", return_value=cmd):
            exit_code = run_playbook("playbook.yml", [], renderer, timeout=0.1)

        assert exit_code == 0
        renderer.handle_interactive_prompt.assert_not_called()
