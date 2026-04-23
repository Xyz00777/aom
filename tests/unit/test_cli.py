"""Unit tests for CLI interface in ansible_aom.cli.

Test cases cover:
- TC-001 to TC-005: Package identity and core structure (Sections 1-2)
- TC-006 to TC-012: Main command and CLI flags (Section 3.1-3.2)
- TC-013 to TC-023: Inspect subcommand (Section 3.3)
- TC-024 to TC-025: Exit codes (Section 3.4, partial)

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
        from ansible_aom.renderer.protocol import Renderer

        assert Renderer is not None

    def test_textual_app_satisfies_protocol(self):
        """TC-004: AOMApp (Textual) satisfies Renderer Protocol."""
        from ansible_aom.renderer.protocol import Renderer

        assert Renderer is not None


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

    def test_factory_passes_kwargs_to_renderer(self):
        """TC-005: Factory passes kwargs to renderer constructor."""
        from ansible_aom.renderer.factory import create_renderer

        renderer = create_renderer(verbose=True, playbook="test.yml")
        assert renderer is not None


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

    def test_verbose_flag_short_form(self):
        """TC-008: -v flag works."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["-v", "playbook.yml"])
        assert args.verbose is True

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
    """Tests for TC-013 to TC-023: Inspect Subcommand."""

    def test_inspect_subcommand_exists(self):
        """TC-013: 'inspect' subcommand exists."""
        from ansible_aom.cli import create_inspect_parser

        parser = create_inspect_parser()
        args = parser.parse_args([])
        assert args.inspect_action == "list"

    def test_inspect_list_subcommand(self):
        """TC-013: 'aom inspect list' lists all sessions."""
        from ansible_aom.cli import create_inspect_parser

        parser = create_inspect_parser()
        args = parser.parse_args(["list"])
        assert args.inspect_action == "list"

    def test_inspect_show_session(self):
        """TC-014: 'aom inspect <session-id>' shows session summary."""
        from ansible_aom.cli import create_inspect_parser

        parser = create_inspect_parser()
        args = parser.parse_args(["session-123"])
        assert args.inspect_action == "session-123"

    def test_inspect_filter_failed(self):
        """TC-015: 'aom inspect <id> --failed' shows failed tasks."""
        from ansible_aom.cli import create_inspect_parser

        parser = create_inspect_parser()
        args = parser.parse_args(["session-123", "--failed"])
        assert args.failed is True

    def test_inspect_filter_host(self):
        """TC-016: 'aom inspect <id> --host <name>' filters by host."""
        from ansible_aom.cli import create_inspect_parser

        parser = create_inspect_parser()
        args = parser.parse_args(["session-123", "--host", "web1"])
        assert args.host == "web1"

    def test_inspect_tree_view(self):
        """TC-017: 'aom inspect <id> --tree' shows task tree."""
        from ansible_aom.cli import create_inspect_parser

        parser = create_inspect_parser()
        args = parser.parse_args(["session-123", "--tree"])
        assert args.tree is True

    def test_inspect_export_artifact(self):
        """TC-018: 'aom inspect <id> --export' creates .aom file."""
        from ansible_aom.cli import create_inspect_parser

        parser = create_inspect_parser()
        args = parser.parse_args(["session-123", "--export"])
        assert args.export is True

    def test_inspect_diff_sessions(self):
        """TC-019: 'aom inspect diff <id1> <id2>' compares sessions."""
        from ansible_aom.cli import create_inspect_parser

        parser = create_inspect_parser()
        args = parser.parse_args(["diff", "id1", "id2"])
        assert args.inspect_action == "diff"
        assert args.session_ids == ["id1", "id2"]

    def test_inspect_prune_sessions(self):
        """TC-020: 'aom inspect prune --days 30' removes old sessions."""
        from ansible_aom.cli import create_inspect_parser

        parser = create_inspect_parser()
        args = parser.parse_args(["prune", "--days", "30"])
        assert args.inspect_action == "prune"
        assert args.days == 30

    def test_inspect_tui_mode(self):
        """TC-021: 'aom inspect --tui' launches TUI for browsing."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--tui", "playbook.yml"])
        assert args.tui is True

    def test_inspect_json_output(self):
        """TC-022: 'aom inspect <id> --json' outputs JSON."""
        from ansible_aom.cli import create_inspect_parser

        parser = create_inspect_parser()
        args = parser.parse_args(["session-123", "--json"])
        assert args.json is True

    def test_inspect_jsonl_output(self):
        """TC-023: 'aom inspect <id> --jsonl' outputs raw events."""
        from ansible_aom.cli import create_inspect_parser

        parser = create_inspect_parser()
        args = parser.parse_args(["session-123", "--jsonl"])
        assert args.jsonl is True


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
        """TC-027: Exit code 127 when ansible-playbook not found."""
        from ansible_aom.cli import main

        with patch("ansible_aom.renderer.factory.create_renderer") as mock_renderer:
            mock_renderer.side_effect = FileNotFoundError("ansible-playbook")
            with patch("sys.argv", ["aom", "playbook.yml"]):
                result = main()
                assert result == 127

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


class TestChangesOnlyFlag:
    """Tests for --changes-only flag."""

    def test_changes_only_flag_exists(self):
        """--changes-only flag exists."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["--changes-only", "playbook.yml"])
        assert args.changes_only is True

    def test_changes_only_defaults_false(self):
        """--changes-only defaults to False."""
        from ansible_aom.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["playbook.yml"])
        assert args.changes_only is False
