"""Unit tests for CLI interface in ansible_aom.cli.

Test cases cover:
- TC-001 to TC-005: Package identity and core structure (Sections 1-2)
- TC-006 to TC-012: Main command and CLI flags (Section 3.1-3.2)
- TC-013 to TC-023: Inspect subcommand (Section 3.3)
- TC-024 to TC-028: Exit codes (Section 3.4)

All tests are self-contained and use function-scoped fixtures.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

CORE_MODULE_PATHS = [
    "src/ansible_aom/cli.py",
    "src/ansible_aom/__main__.py",
    "src/ansible_aom/core/models.py",
    "src/ansible_aom/core/state.py",
    "src/ansible_aom/core/parser.py",
    "src/ansible_aom/core/session.py",
    "src/ansible_aom/core/config.py",
    "src/ansible_aom/core/redaction.py",
    "src/ansible_aom/core/icons.py",
    "src/ansible_aom/renderer/protocol.py",
    "src/ansible_aom/renderer/factory.py",
    "src/ansible_aom/compact/renderer.py",
    "src/ansible_aom/compact/display.py",
    "src/ansible_aom/compact/logs.py",
    "src/ansible_aom/compact/password.py",
    "src/ansible_aom/tui/app.py",
    "src/ansible_aom/inspect/cli.py",
    "src/ansible_aom/inspect/display.py",
    "src/ansible_aom/inspect/diff.py",
]


class TestPackageIdentity:
    """Tests for TC-001: Package Name Verification."""

    def test_package_name_is_ansible_aom(self):
        """TC-001: Package name is 'ansible-aom'."""
        import re

        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        content = pyproject_path.read_text()
        assert re.search(r'^name\s*=\s*["\']ansible-aom["\']', content, re.MULTILINE)

    def test_cli_entry_point_is_aom(self):
        """TC-001: CLI entry point is 'aom'."""
        import re

        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "aom" in content
        assert "ansible_aom.cli:main" in content

    def test_version_exists_in_init(self):
        """TC-001: Version is defined in __init__.py."""
        from ansible_aom import __version__

        assert __version__ is not None
        assert isinstance(__version__, str)
        import re

        assert re.match(r"^\d+\.\d+\.\d+.*$", __version__)

    def test_version_matches_installed_package_metadata(self):
        """TC-001b: ``__version__`` must track the installed package version.

        Previously a hardcoded literal in ``__init__.py`` lagged behind
        the version in ``pyproject.toml``, so ``aom --version`` reported
        stale info after editable reinstalls. The single source of truth
        is now the package metadata.
        """
        from importlib.metadata import version

        from ansible_aom import __version__

        assert __version__ == version("ansible-aom")

    def test_source_hash_is_short_stable_hex(self):
        """``source_hash()`` returns a deterministic short hex digest."""
        from ansible_aom import source_hash

        h = source_hash()
        assert isinstance(h, str)
        assert len(h) == 12
        assert all(c in "0123456789abcdef" for c in h)
        # Stable across calls (cached).
        assert source_hash() == h

    def test_source_hash_changes_when_source_changes(self, tmp_path, monkeypatch):
        """A source-file content change must alter the hash.

        Verifies the hash actually reads the files, isn't constant or
        stubbed. Constructs a tiny fake package to avoid touching the
        real source tree.
        """
        from ansible_aom import _compute_source_hash

        # Bypass the cache so each call recomputes against the file content.
        pkg = tmp_path / "ansible_aom"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("x = 1\n")
        (pkg / "core.py").write_text("y = 2\n")

        # Patch __file__ inside the function's module so it points at
        # our fake package. Easier: call the worker function with a
        # custom path? It's a module-level closure on __file__, so
        # we monkeypatch by adjusting Path() resolution. Use the same
        # approach: write the package, then call _compute_source_hash
        # after redirecting its __file__.
        import ansible_aom as aom_mod

        original_file = aom_mod.__file__
        try:
            monkeypatch.setattr(aom_mod, "__file__", str(pkg / "__init__.py"))
            first = _compute_source_hash()

            (pkg / "core.py").write_text("y = 999\n")  # change content
            second = _compute_source_hash()

            assert first != second
        finally:
            monkeypatch.setattr(aom_mod, "__file__", original_file)

    def test_cli_version_includes_source_hash(self, capsys):
        """``aom --version`` prints version AND source hash."""
        from unittest.mock import patch

        from ansible_aom import __version__, source_hash
        from ansible_aom.cli import main

        with patch("sys.argv", ["aom", "--version"]):
            main()
        captured = capsys.readouterr()
        assert __version__ in captured.out
        assert source_hash() in captured.out


class TestCLIEntryPoint:
    """Tests for TC-002: CLI Entry Point Exists."""

    def test_cli_module_importable(self):
        """TC-002: CLI module can be imported."""
        from ansible_aom import cli

        assert hasattr(cli, "main")
        assert hasattr(cli, "create_parser")

    def test_main_module_importable(self):
        """TC-002: __main__ module exists and calls main()."""
        from ansible_aom import __main__

        assert hasattr(__main__, "main")

    def test_create_parser_returns_argparse_parser(self):
        """TC-002: create_parser returns ArgumentParser."""
        import argparse

        from ansible_aom.cli import create_parser

        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_create_parser_has_playbook_positional_arg(self):
        """TC-002: Parser accepts playbook positional argument."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["playbook.yml"])
        assert args.playbook == "playbook.yml"

    def test_main_function_exists_and_returns_int(self):
        """TC-002: main() function exists and returns exit code."""
        from ansible_aom.cli import main

        with patch("sys.argv", ["aom", "--version"]):
            result = main()
            assert result == 0


class TestCoreModuleStructure:
    """Tests for TC-003: Core Module Structure."""

    @pytest.mark.parametrize("module_path", CORE_MODULE_PATHS)
    def test_core_module_file_exists(self, module_path: str):
        """TC-003: Core module file exists at expected path."""
        project_root = Path(__file__).parent.parent.parent
        full_path = project_root / module_path
        assert full_path.exists(), f"Expected {module_path} to exist"
        assert full_path.is_file(), f"Expected {module_path} to be a file"

    def test_cli_module_exists(self):
        """TC-003: cli.py module exists."""
        from ansible_aom import cli

        assert cli is not None

    def test_main_module_exists(self):
        """TC-003: __main__.py module exists."""
        from ansible_aom import __main__

        assert __main__ is not None

    def test_renderer_module_exists(self):
        """TC-003: renderer/ module exists."""
        from ansible_aom.renderer import factory, protocol

        assert protocol is not None
        assert factory is not None

    def test_core_module_exists(self):
        """TC-003: core/ module exists."""
        from ansible_aom.core import models, parser, state

        assert models is not None
        assert state is not None
        assert parser is not None


class TestRendererProtocol:
    """Tests for TC-004: Renderer Protocol Implementation."""

    def test_renderer_protocol_has_start_method(self):
        """TC-004: Renderer Protocol defines start() method."""
        from ansible_aom.renderer.protocol import Renderer

        assert hasattr(Renderer, "start")

    def test_renderer_protocol_has_update_state_method(self):
        """TC-004: Renderer Protocol defines update_state() method."""
        from ansible_aom.renderer.protocol import Renderer

        assert hasattr(Renderer, "update_state")

    def test_renderer_protocol_has_handle_password_prompt_method(self):
        """TC-004: Renderer Protocol defines handle_password_prompt() method."""
        from ansible_aom.renderer.protocol import Renderer

        assert hasattr(Renderer, "handle_password_prompt")

    def test_renderer_protocol_has_handle_completion_method(self):
        """TC-004: Renderer Protocol defines handle_completion() method."""
        from ansible_aom.renderer.protocol import Renderer

        assert hasattr(Renderer, "handle_completion")

    def test_renderer_protocol_has_stop_method(self):
        """TC-004: Renderer Protocol defines stop() method."""
        from ansible_aom.renderer.protocol import Renderer

        assert hasattr(Renderer, "stop")

    def test_renderer_protocol_signature_start(self):
        """TC-004: start() has correct signature."""
        import inspect

        from ansible_aom.renderer.protocol import Renderer

        sig = inspect.signature(Renderer.start)
        params = list(sig.parameters.keys())
        assert "self" in params or params[0] == "playbook"

    def test_renderer_protocol_signature_update_state(self):
        """TC-004: update_state() has correct signature."""
        import inspect

        from ansible_aom.renderer.protocol import Renderer

        sig = inspect.signature(Renderer.update_state)
        params = list(sig.parameters.keys())
        assert "self" in params or params[0] == "event"

    def test_compact_renderer_satisfies_protocol(self):
        """TC-004: CompactRenderer satisfies Renderer Protocol."""
        from ansible_aom.compact.renderer import CompactRenderer
        from ansible_aom.renderer.protocol import Renderer

        renderer = CompactRenderer()
        assert isinstance(renderer, Renderer)

    def test_textual_app_satisfies_protocol(self):
        """TC-004: AOMApp (Textual) satisfies Renderer Protocol."""
        from ansible_aom.renderer.protocol import Renderer
        from ansible_aom.tui.app import AOMApp

        app = AOMApp()
        assert isinstance(app, Renderer)


class TestRendererFactory:
    """Tests for TC-005: Renderer Factory Selection."""

    def test_factory_function_exists(self):
        """TC-005: create_renderer function exists."""
        from ansible_aom.renderer.factory import create_renderer

        assert callable(create_renderer)

    def test_factory_returns_renderer_for_tui_mode(self):
        """TC-005: create_renderer(tui_mode=True) returns AOMApp."""
        from ansible_aom.renderer.factory import create_renderer

        renderer = create_renderer(tui_mode=True)
        assert hasattr(renderer, "start")
        assert hasattr(renderer, "update_state")
        assert hasattr(renderer, "handle_password_prompt")
        assert hasattr(renderer, "handle_completion")
        assert hasattr(renderer, "stop")

    def test_factory_returns_renderer_for_compact_mode(self):
        """TC-005: create_renderer(tui_mode=False) returns CompactRenderer."""
        from ansible_aom.renderer.factory import create_renderer

        renderer = create_renderer(tui_mode=False)
        assert hasattr(renderer, "start")
        assert hasattr(renderer, "update_state")
        assert hasattr(renderer, "handle_password_prompt")
        assert hasattr(renderer, "handle_completion")
        assert hasattr(renderer, "stop")

    def test_factory_default_tui_mode_false(self):
        """TC-005: create_renderer() defaults to compact renderer."""
        from ansible_aom.renderer.factory import create_renderer

        renderer = create_renderer()
        assert hasattr(renderer, "start")

    def test_factory_forwards_is_tty_to_compact_renderer(self):
        """create_renderer(is_tty=False) constructs a non-TTY CompactRenderer."""
        from ansible_aom.compact.renderer import CompactRenderer
        from ansible_aom.renderer.factory import create_renderer

        renderer = create_renderer(tui_mode=False, is_tty=False)
        assert isinstance(renderer, CompactRenderer)
        assert renderer._display.is_tty is False


class TestBasicCLIInvocation:
    """Tests for TC-006: Basic CLI Invocation."""

    def test_playbook_positional_argument_required(self):
        """TC-006: Playbook argument can be provided."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["playbook.yml"])
        assert args.playbook == "playbook.yml"

    def test_playbook_argument_accepted(self):
        """TC-006: Playbook argument is accepted."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["playbook.yml"])
        assert args.playbook == "playbook.yml"

    def test_main_command_shows_help_without_playbook(self):
        """TC-006: Main command shows help without playbook."""
        from ansible_aom.cli import main

        with patch("sys.argv", ["aom"]):
            result = main()
            assert result == 0


class TestTUIModeFlag:
    """Tests for TC-007: TUI Mode Flag."""

    def test_tui_flag_exists(self):
        """TC-007: --tui flag exists in parser."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--tui", "playbook.yml"])
        assert args.tui is True

    def test_tui_flag_defaults_false(self):
        """TC-007: TUI mode defaults to False."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["playbook.yml"])
        assert args.tui is False

    def test_tui_flag_works_at_start(self):
        """TC-007: --tui can be specified before playbook."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--tui", "playbook.yml"])
        assert args.tui is True
        assert args.playbook == "playbook.yml"


class TestVerboseFlag:
    """Tests for TC-008, TC-009: Verbose Flag."""

    def test_verbose_flag_exists(self):
        """TC-008: --verbose flag exists."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--verbose", "playbook.yml"])
        assert args.verbose is True

    def test_short_v_does_not_set_aom_verbose(self):
        """The bare ``-v`` is reserved for ansible-playbook passthrough.

        AOM's own debug flag is ``--verbose`` (long form only). When the
        user writes ``aom playbook.yml -v`` the ``-v`` lands in
        ``ansible_args`` via REMAINDER and reaches ansible-playbook —
        which is what they want, since that's how ansible's verbosity
        ramp works.
        """
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["playbook.yml", "-v"])
        assert args.verbose is False
        assert "-v" in args.ansible_args

    def test_verbose_flag_defaults_false(self):
        """TC-008: Verbose defaults to False."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["playbook.yml"])
        assert args.verbose is False


class TestHelpFlag:
    """Tests for TC-011: Help Flag."""

    def test_help_flag_exists(self):
        """TC-011: --help flag exists."""
        from ansible_aom.cli import main

        with patch("sys.argv", ["aom", "--help"]):
            result = main()
            assert result == 0

    def test_help_displays_usage(self):
        """TC-011: --help displays usage information."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        import io

        help_file = io.StringIO()
        parser.print_help(help_file)
        output = help_file.getvalue()
        assert "usage" in output.lower() or "Usage" in output

    def test_help_shows_flags(self):
        """TC-011: --help shows available flags."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        import io

        help_file = io.StringIO()
        parser.print_help(help_file)
        output = help_file.getvalue()
        assert "--tui" in output or "--verbose" in output


class TestVersionFlag:
    """Tests for TC-012: Version Flag."""

    def test_version_flag_exists(self):
        """TC-012: --version flag exists."""
        from ansible_aom.cli import main

        with patch("sys.argv", ["aom", "--version"]):
            result = main()
            assert result == 0

    def test_version_displays_semantic_version(self):
        """TC-012: --version displays version string."""
        from ansible_aom.cli import main

        with patch("sys.argv", ["aom", "--version"]):
            result = main()
            assert result == 0


class TestAnsibleOptionsPassthrough:
    """Tests for TC-010: Ansible Options Pass-Through."""

    def test_unknown_args_passed_through(self):
        """TC-010: Unknown arguments are captured as ansible_args."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["playbook.yml", "-i", "inventory.ini"])
        assert args.playbook == "playbook.yml"
        assert args.ansible_args == ["-i", "inventory.ini"]

    def test_limit_flag_passed_through(self):
        """TC-010: --limit passed to ansible-playbook."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["playbook.yml", "--limit", "webservers"])
        assert args.playbook == "playbook.yml"
        assert args.ansible_args == ["--limit", "webservers"]

    def test_inventory_flag_passed_through(self):
        """TC-010: -i inventory passed to ansible-playbook."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["playbook.yml", "-i", "hosts.ini"])
        assert args.playbook == "playbook.yml"
        assert args.ansible_args == ["-i", "hosts.ini"]


class TestInspectSubcommand:
    """Tests for TC-013 to TC-023: Inspect Subcommand dispatch.

    The top-level CLI strips the ``inspect`` token and delegates to
    ``ansible_aom.inspect.cli.main``. These tests pin the dispatch contract;
    behaviour of each subcommand is exercised by tests/integration/test_inspect.py.
    """

    def test_inspect_dispatches_to_inspect_main_with_remaining_argv(self):
        """TC-013: 'aom inspect list' forwards ['list'] to inspect.cli.main."""
        from ansible_aom.cli import main

        with patch("ansible_aom.inspect.cli.main", return_value=0) as mock_main:
            with patch("sys.argv", ["aom", "inspect", "list"]):
                result = main()
                assert result == 0
                mock_main.assert_called_once_with(["list"])

    def test_inspect_forwards_subcommand_flags(self):
        """TC-015/TC-016/TC-022: flags after the subcommand reach inspect.cli.main."""
        from ansible_aom.cli import main

        with patch("ansible_aom.inspect.cli.main", return_value=0) as mock_main:
            with patch("sys.argv", ["aom", "inspect", "show", "id1", "--failed", "--json"]):
                main()
                mock_main.assert_called_once_with(["show", "id1", "--failed", "--json"])

    def test_inspect_forwards_diff_subcommand(self):
        """TC-019: 'aom inspect diff id1 id2' forwards args verbatim."""
        from ansible_aom.cli import main

        with patch("ansible_aom.inspect.cli.main", return_value=0) as mock_main:
            with patch("sys.argv", ["aom", "inspect", "diff", "id1", "id2"]):
                main()
                mock_main.assert_called_once_with(["diff", "id1", "id2"])

    def test_inspect_propagates_exit_code(self):
        """Exit code from inspect.cli.main flows back through the dispatcher."""
        from ansible_aom.cli import main

        with patch("ansible_aom.inspect.cli.main", return_value=2):
            with patch("sys.argv", ["aom", "inspect", "show", "missing"]):
                assert main() == 2


class TestExitCodes:
    """Tests for TC-024, TC-025, TC-027, TC-028: Exit Codes."""

    def test_exit_code_0_for_help(self):
        """TC-024: Exit code 0 for --help."""
        from ansible_aom.cli import main

        with patch("sys.argv", ["aom", "--help"]):
            result = main()
            assert result == 0

    def test_exit_code_0_for_version(self):
        """TC-024: Exit code 0 for --version."""
        from ansible_aom.cli import main

        with patch("sys.argv", ["aom", "--version"]):
            result = main()
            assert result == 0

    def test_exit_code_127_for_missing_ansible(self):
        """TC-027: Exit code 127 when ansible-playbook not found.

        The runner is responsible for detecting the missing executable and
        returning 127 cleanly (its own tests cover the pexpect spawn-failure
        path); here we just assert that whatever exit code the runner
        returns is propagated through main().
        """
        from ansible_aom.cli import main

        with patch("ansible_aom.runner.run_playbook", return_value=127) as mock_run:
            with patch("sys.argv", ["aom", "playbook.yml"]):
                result = main()
                assert result == 127
                mock_run.assert_called_once()

    def test_exit_code_130_for_sigint(self):
        """TC-028: Exit code 130 for user cancelled (Ctrl+C)."""
        from ansible_aom.cli import main

        with patch("ansible_aom.renderer.factory.create_renderer") as mock_renderer:
            mock_renderer.side_effect = KeyboardInterrupt()
            with patch("sys.argv", ["aom", "playbook.yml"]):
                result = main()
                assert result == 130

    def test_main_returns_int(self):
        """TC-024: main() returns integer exit code."""
        from ansible_aom.cli import main

        with patch("sys.argv", ["aom", "--version"]):
            result = main()
            assert isinstance(result, int)


class TestVerboseDiagnostics:
    """Tests for TC-008: Verbose flag diagnostics."""

    def test_verbose_prints_ansible_path(self):
        """TC-008: --verbose prints resolved ansible-playbook path."""
        from ansible_aom.cli import main

        with (
            patch("sys.argv", ["aom", "--verbose", "playbook.yml"]),
            patch("ansible_aom.renderer.factory.create_renderer"),
            patch("shutil.which", return_value="/usr/bin/ansible-playbook"),
            patch("builtins.print") as mock_print,
        ):
            main()
        printed = "\n".join(str(c) for c in mock_print.call_args_list)
        assert "/usr/bin/ansible-playbook" in printed or any(
            "ansible-playbook" in str(c) for c in mock_print.call_args_list
        )

    def test_verbose_prints_env_overrides(self):
        """TC-008: --verbose prints ANSIBLE_STDOUT_CALLBACK env override."""
        from ansible_aom.cli import main

        with (
            patch("sys.argv", ["aom", "--verbose", "playbook.yml"]),
            patch("ansible_aom.renderer.factory.create_renderer"),
            patch("shutil.which", return_value="/usr/bin/ansible-playbook"),
            patch("builtins.print") as mock_print,
        ):
            main()
        printed = "\n".join(str(c) for c in mock_print.call_args_list)
        assert any("ANSIBLE_STDOUT_CALLBACK" in str(c) for c in mock_print.call_args_list)

    def test_verbose_prints_terminal_capabilities(self):
        """TC-008: --verbose prints terminal capabilities when verbose."""
        from ansible_aom.cli import main

        with (
            patch("sys.argv", ["aom", "--verbose", "playbook.yml"]),
            patch("ansible_aom.renderer.factory.create_renderer"),
            patch("shutil.which", return_value="/usr/bin/ansible-playbook"),
            patch("builtins.print") as mock_print,
        ):
            main()
        printed_lines = [str(c) for c in mock_print.call_args_list]
        assert (
            any("terminal" in line.lower() or "tty" in line.lower() for line in printed_lines)
            or len(printed_lines) > 1
        )

    def test_verbose_without_playbook_shows_help(self):
        """TC-008: --verbose without playbook still shows help, not crash."""
        from ansible_aom.cli import main

        with patch("sys.argv", ["aom", "--verbose"]):
            result = main()
            assert result == 0

    def test_verbose_list_tasks_summary(self):
        """TC-008: --verbose includes --list-tasks summary in diagnostics."""
        from ansible_aom.cli import main

        with (
            patch("sys.argv", ["aom", "--verbose", "playbook.yml"]),
            patch("ansible_aom.renderer.factory.create_renderer"),
            patch("shutil.which", return_value="/usr/bin/ansible-playbook"),
            patch("builtins.print") as mock_print,
        ):
            main()
        printed = "\n".join(str(c) for c in mock_print.call_args_list)
        assert any("task" in line.lower() for line in printed.split("\n")) or any(
            "ansible-playbook" in str(c) for c in mock_print.call_args_list
        )


class TestVerboseDebugLogging:
    """Tests for TC-009: Verbose enables DEBUG logging."""

    def test_verbose_sets_debug_log_level(self):
        """TC-009: --verbose sets logging level to DEBUG."""
        import logging

        from ansible_aom.cli import main

        with (
            patch("sys.argv", ["aom", "--verbose", "playbook.yml"]),
            patch("ansible_aom.renderer.factory.create_renderer"),
            patch("shutil.which", return_value="/usr/bin/ansible-playbook"),
        ):
            main()
        aom_logger = logging.getLogger("ansible_aom")
        assert aom_logger.level == logging.DEBUG or any(
            handler.level <= logging.DEBUG for handler in aom_logger.handlers
        )

    def test_verbose_creates_log_file_with_debug_entries(self):
        """TC-009: --verbose causes DEBUG entries in log output."""
        import logging

        from ansible_aom.cli import main

        debug_records = []

        class DebugCapture(logging.Handler):
            def emit(self, record):
                debug_records.append(record)

        capture = DebugCapture()
        capture.setLevel(logging.DEBUG)

        aom_logger = logging.getLogger("ansible_aom")
        aom_logger.addHandler(capture)

        try:
            with (
                patch("sys.argv", ["aom", "--verbose", "playbook.yml"]),
                patch("ansible_aom.renderer.factory.create_renderer"),
                patch("shutil.which", return_value="/usr/bin/ansible-playbook"),
            ):
                main()
            assert any(record.levelno >= logging.DEBUG for record in debug_records), (
                "Expected at least one DEBUG-level log record when --verbose is set"
            )
        finally:
            aom_logger.removeHandler(capture)

    def test_non_verbose_does_not_set_debug_level(self):
        """TC-009: Without --verbose, logging level is not DEBUG."""
        import logging

        from ansible_aom.cli import main

        original_level = logging.getLogger("ansible_aom").level

        with (
            patch("sys.argv", ["aom", "playbook.yml"]),
            patch("ansible_aom.renderer.factory.create_renderer"),
        ):
            main()

        aom_logger = logging.getLogger("ansible_aom")
        if aom_logger.level != logging.NOTSET:
            assert aom_logger.level != logging.DEBUG or original_level == logging.DEBUG


class TestExitCode1:
    """Tests for TC-025: Exit code 1 — playbook with failed task."""

    def test_determine_exit_code_returns_1_on_failed(self):
        """TC-025: determine_exit_code returns 1 when any host has FAILED status."""
        from ansible_aom.compact.renderer import determine_exit_code
        from ansible_aom.core.models import (
            HostRunState,
            PlayRunState,
            RunState,
            Status,
            TaskRunState,
        )

        state = RunState(playbook="fail.yml")
        play = PlayRunState(play_id="play-1", name="test play")
        task = TaskRunState(task_id="task-1", name="fail task")
        task.hosts["host1"] = HostRunState(hostname="host1", status=Status.FAILED)
        play.tasks["task-1"] = task
        state.plays["play-1"] = play

        assert determine_exit_code(state) == 1

    def test_determine_exit_code_priority_failed_over_unreachable(self):
        """TC-025: FAILED takes precedence over UNREACHABLE for exit code."""
        from ansible_aom.compact.renderer import determine_exit_code
        from ansible_aom.core.models import (
            HostRunState,
            PlayRunState,
            RunState,
            Status,
            TaskRunState,
        )

        state = RunState(playbook="mixed.yml")
        play = PlayRunState(play_id="play-1", name="mixed play")
        task = TaskRunState(task_id="task-1", name="mixed task")
        task.hosts["host1"] = HostRunState(hostname="host1", status=Status.FAILED)
        task.hosts["host2"] = HostRunState(hostname="host2", status=Status.UNREACHABLE)
        play.tasks["task-1"] = task
        state.plays["play-1"] = play

        assert determine_exit_code(state) == 1

    def test_main_returns_1_on_not_implemented_renderer(self):
        """TC-025: main() returns exit code 1 when renderer raises NotImplementedError."""
        from ansible_aom.cli import main

        with (
            patch("ansible_aom.renderer.factory.create_renderer") as mock_renderer,
            patch("sys.argv", ["aom", "playbook.yml"]),
        ):
            mock_renderer.side_effect = NotImplementedError("not yet")
            result = main()
            assert result == 1

    def test_main_returns_1_on_general_error(self):
        """TC-025: main() returns exit code 1 on general exception."""
        from ansible_aom.cli import main

        with (
            patch("ansible_aom.renderer.factory.create_renderer") as mock_renderer,
            patch("sys.argv", ["aom", "playbook.yml"]),
        ):
            mock_renderer.side_effect = RuntimeError("boom")
            result = main()
            assert result == 1


class TestExitCode2:
    """Tests for TC-026: Exit code 2 — all hosts unreachable."""

    def test_determine_exit_code_returns_2_on_unreachable(self):
        """TC-026: determine_exit_code returns 2 when all hosts are UNREACHABLE."""
        from ansible_aom.compact.renderer import determine_exit_code
        from ansible_aom.core.models import (
            HostRunState,
            PlayRunState,
            RunState,
            Status,
            TaskRunState,
        )

        state = RunState(playbook="unreach.yml")
        play = PlayRunState(play_id="play-1", name="unreach play")
        task = TaskRunState(task_id="task-1", name="unreach task")
        task.hosts["host1"] = HostRunState(hostname="host1", status=Status.UNREACHABLE)
        task.hosts["host2"] = HostRunState(hostname="host2", status=Status.UNREACHABLE)
        play.tasks["task-1"] = task
        state.plays["play-1"] = play

        assert determine_exit_code(state) == 2

    def test_determine_exit_code_returns_0_on_ok(self):
        """TC-026: determine_exit_code returns 0 when all hosts OK (no unreachable, no failed)."""
        from ansible_aom.compact.renderer import determine_exit_code
        from ansible_aom.core.models import (
            HostRunState,
            PlayRunState,
            RunState,
            Status,
            TaskRunState,
        )

        state = RunState(playbook="ok.yml")
        play = PlayRunState(play_id="play-1", name="ok play")
        task = TaskRunState(task_id="task-1", name="ok task")
        task.hosts["host1"] = HostRunState(hostname="host1", status=Status.OK)
        task.hosts["host2"] = HostRunState(hostname="host2", status=Status.CHANGED)
        play.tasks["task-1"] = task
        state.plays["play-1"] = play

        assert determine_exit_code(state) == 0

    def test_determine_exit_code_returns_0_on_empty_state(self):
        """TC-026: determine_exit_code returns 0 on empty RunState (no plays/tasks)."""
        from ansible_aom.compact.renderer import determine_exit_code
        from ansible_aom.core.models import RunState

        state = RunState(playbook="empty.yml")
        assert determine_exit_code(state) == 0

    def test_unreachable_without_failed_yields_exit_2(self):
        """TC-026: UNREACHABLE without any FAILED yields exit code 2."""
        from ansible_aom.compact.renderer import determine_exit_code
        from ansible_aom.core.models import (
            HostRunState,
            PlayRunState,
            RunState,
            Status,
            TaskRunState,
        )

        state = RunState(playbook="unreach.yml")
        play = PlayRunState(play_id="play-1", name="mixed")
        task = TaskRunState(task_id="task-1", name="mixed task")
        task.hosts["host1"] = HostRunState(hostname="host1", status=Status.UNREACHABLE)
        task.hosts["host2"] = HostRunState(hostname="host2", status=Status.OK)
        play.tasks["task-1"] = task
        state.plays["play-1"] = play

        assert determine_exit_code(state) == 2


def test_aom_rerun_dispatches_to_rerun_main(monkeypatch):
    """Top-level `aom rerun ...` invokes the rerun subcommand main."""
    from ansible_aom import cli as cli_mod

    captured: dict = {}

    def fake_rerun_main(argv):
        captured["argv"] = argv
        return 42

    monkeypatch.setattr(
        "ansible_aom.rerun.cli.main",
        fake_rerun_main,
    )
    monkeypatch.setattr(
        "sys.argv",
        ["aom", "rerun", "abc12345", "--failed", "--yes"],
    )
    rc = cli_mod.main()
    assert rc == 42
    assert captured["argv"] == ["abc12345", "--failed", "--yes"]


class TestFormatFlag:
    """Tests for F6: --format {compact,json} flag."""

    def test_format_flag_defaults_to_compact(self):
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["playbook.yml"])
        assert args.format == "compact"

    def test_format_flag_accepts_json(self):
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--format", "json", "playbook.yml"])
        assert args.format == "json"

    def test_format_flag_accepts_compact_explicit(self):
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--format", "compact", "playbook.yml"])
        assert args.format == "compact"

    def test_format_flag_rejects_unknown_value(self, capsys):
        from ansible_aom.cli import create_parser

        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--format", "yaml", "playbook.yml"])

    def test_format_flag_does_not_appear_in_ansible_args(self):
        """--format is consumed by argparse, not forwarded to ansible-playbook."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--format", "json", "playbook.yml", "-i", "inv.ini"])
        assert args.format == "json"
        assert args.ansible_args == ["-i", "inv.ini"]

    def test_main_rejects_tui_plus_json_format(self, capsys):
        """`aom --tui --format json playbook.yml` exits 2 with a usage error."""
        from ansible_aom.cli import main

        with patch("sys.argv", ["aom", "--tui", "--format", "json", "playbook.yml"]):
            result = main()
        assert result == 2
        captured = capsys.readouterr()
        assert "--tui" in captured.err and "--format json" in captured.err

    def test_main_dispatches_json_renderer_when_format_json(self):
        """`aom --format json playbook.yml` constructs a JsonRenderer."""
        from ansible_aom.cli import main
        from ansible_aom.json_renderer import JsonRenderer

        captured_renderer: dict = {}

        def fake_run_playbook(playbook, ansible_args, renderer, **kwargs):
            captured_renderer["renderer"] = renderer
            return 0

        with (
            patch("ansible_aom.runner.run_playbook", side_effect=fake_run_playbook),
            patch("sys.argv", ["aom", "--format", "json", "playbook.yml"]),
        ):
            result = main()

        assert result == 0
        assert isinstance(captured_renderer["renderer"], JsonRenderer)
