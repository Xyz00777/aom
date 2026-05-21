"""CLI entry point for AOM.

This module provides the main command-line interface for AOM.
See SPECIFICATION.md Section 3 for command interface details.
"""

import argparse
import logging
import os
import shutil
import sys

import argcomplete

from ansible_aom import __version__

# Files we'll auto-discover as inventory when the user doesn't pass -i.
# Order is preference order — `inventory.ini` wins over `hosts` because
# the former is more specific to ansible's conventions.
_DEFAULT_INVENTORY_NAMES = (
    "inventory.ini",
    "inventory.yml",
    "inventory.yaml",
    "inventory",
    "hosts.ini",
    "hosts.yml",
    "hosts.yaml",
    "hosts",
)

# All flags ansible-playbook accepts for specifying inventory; if the user
# already supplied any of these we leave their args alone.
_INVENTORY_FLAGS = ("-i", "--inventory", "--inventory-file")


def detect_default_inventory() -> str | None:
    """Return the first conventional inventory file found in CWD, or None."""
    for name in _DEFAULT_INVENTORY_NAMES:
        if os.path.isfile(name):
            return name
    return None


def detect_duplicate_playbook(playbook: str, ansible_args: list[str]) -> bool:
    """True if `playbook` appears (path-normalised) in `ansible_args`.

    Catches the easy typo where the user types
    `aom site.yml -i inv.ini site.yml` — the trailing copy lands in
    ansible_args via argparse REMAINDER, ansible-playbook then dies
    with an unhelpful argparse error. Surfacing it earlier saves the
    user a confused moment.
    """
    target = os.path.normpath(playbook)
    return any(os.path.normpath(arg) == target for arg in ansible_args)


def merge_limit_args(ansible_args: list[str]) -> list[str]:
    """Collapse repeated ``-l`` / ``--limit`` flags into a single comma-joined one.

    ansible-playbook stores ``--limit`` as a plain string (not append),
    so ``-l a -l b`` silently keeps only ``b``. Users reach for the
    repeat-the-flag idiom because most CLIs accept it; we merge into
    the comma syntax ansible actually honours as a union.

    The merged flag is placed at the position of the FIRST limit
    occurrence; trailing limit tokens are removed. The flag form
    (``-l`` vs ``--limit``) follows the first occurrence. A trailing
    bare ``-l`` with no value is left alone — ansible will surface
    that as a usage error and inventing a value would mask it.
    """
    # Find every (start_index, flag_form, value) triple. Three forms:
    #   "-l X" / "--limit X" (two tokens) and "--limit=X" (one token).
    found: list[tuple[int, str, str]] = []
    i = 0
    while i < len(ansible_args):
        tok = ansible_args[i]
        if tok in ("-l", "--limit"):
            if i + 1 >= len(ansible_args):
                break  # dangling flag — leave for ansible to reject
            found.append((i, tok, ansible_args[i + 1]))
            i += 2
            continue
        if tok.startswith("--limit="):
            found.append((i, "--limit", tok[len("--limit=") :]))
            i += 1
            continue
        i += 1
    if len(found) < 2:
        return list(ansible_args)

    drop_indices: set[int] = set()
    for start, flag, _ in found:
        drop_indices.add(start)
        # Two-token forms also consume the value slot.
        if not ansible_args[start].startswith("--limit="):
            drop_indices.add(start + 1)

    first_pos, first_flag, _ = found[0]
    merged_value = ",".join(value for _, _, value in found)

    out: list[str] = []
    for idx, tok in enumerate(ansible_args):
        if idx == first_pos:
            out.extend([first_flag, merged_value])
            continue
        if idx in drop_indices:
            continue
        out.append(tok)
    return out


def ensure_inventory_arg(ansible_args: list[str]) -> list[str]:
    """If no -i/--inventory flag is set, prepend one pointing at the default file.

    A no-op when the user already supplied an inventory or no default exists.
    Returns the (possibly modified) args list — never mutates the input.
    """
    if any(arg in _INVENTORY_FLAGS or arg.startswith("--inventory=") for arg in ansible_args):
        return ansible_args
    default = detect_default_inventory()
    if default is None:
        return ansible_args
    return ["-i", default, *ansible_args]


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the AOM CLI.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="aom",
        description="Ansible Output Monitor — nom-style live view for ansible-playbook.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  aom playbook.yml                      Run playbook with compact view (default)
  aom --tui playbook.yml                Run with the full multi-panel TUI
  aom playbook.yml -i inv.ini -v        Flags after the playbook are forwarded
  aom playbook.yml -vvv --tags=deploy   …including ansible-playbook's own -v / -vv / -vvv
  aom inspect                           Launch the TUI on the most recent run
  aom inspect --text                    Dump the most recent run as plain text
  aom inspect prune --days 30           Delete sessions older than N days
  aom replay <session-id>               Replay a recorded session at original pace
  aom replay <session-id> --speed 10    Replay 10x faster
  aom rerun                             Rerun the latest session's failed hosts
  aom rerun <session-id> --failed       Rerun failed hosts from a specific session
  aom rerun <session-id> --unreachable  Rerun failed AND unreachable hosts
  aom rerun --changes-only -y           Rerun changed hosts; skip the prompt
  aom --no-record playbook.yml          Run without writing a session directory
  aom --install-completion bash >> ~/.bashrc   Enable tab-completion for bash

Argument forwarding:
  Anything after the playbook path is passed verbatim to ansible-playbook,
  with two ergonomic exceptions:
  - If you pass -i / --inventory, AOM leaves your inventory alone; otherwise
    AOM auto-detects ./inventory.ini (then .yml, .yaml, hosts) and prepends
    -i for convenience.
  - Repeated -l / --limit flags are merged into a single comma-joined value
    (e.g. `-l web1 -l web2` → `-l web1,web2`). ansible-playbook itself stores
    --limit as a single string and silently keeps only the LAST occurrence,
    which is rarely what users mean. AOM merges them so the union runs.

Verbosity:
  AOM's own debug flag is --verbose (long form only). The short -v
  is reserved for ansible-playbook, so `aom site.yml -v` raises
  ansible verbosity, not AOM verbosity.

Session recording:
  Every run writes ~/.local/state/aom/sessions/<uuidv7>/ containing
  events.jsonl, stderr.log, and meta.json. Recording is best-effort —
  disk errors are logged but never abort the run. Use `aom inspect`
  to replay past runs; `aom inspect prune` to clean up.
  Pass --no-record to disable session writing for a single invocation
  (debug logs from --verbose are unaffected).

Replay:
  `aom replay <session-id>` re-streams a recorded run's events.jsonl
  through the renderer at the original cadence (or scaled with
  --speed N — use --speed 0 for as-fast-as-possible). Replay does
  not reproduce AOM-emitted warnings, the preflight summary, or
  password-prompt log lines — only what's in the JSONL stream.

Shell completion:
  aom --install-completion <bash|zsh|fish>
  Prints the rc-file snippet to stdout. Pipe to your rc file or eval
  it directly. Powered by argcomplete; tab-completes subcommands,
  flags, and recorded session IDs.

Debugging:
  AOM_TRACE=1 aom site.yml  — dumps every pexpect loop transition to
  stderr (TIMEOUT branches, newline matches, buffer contents). Useful
  when an interactive prompt doesn't seem to fire — share the trace
  output and the bytes AOM is receiving become obvious.

File locations:
  Sessions:    ~/.local/state/aom/sessions/<uuidv7>/
  Config:      ~/.config/aom/config.yaml (optional)
  Inventory:   auto-detects ./inventory.ini, ./inventory.yml,
               ./inventory.yaml, ./inventory, ./hosts.ini, ./hosts.yml,
               ./hosts.yaml, ./hosts (first match wins).

Exit codes:
  0   playbook completed cleanly
  1   playbook failed, or AOM crashed
  2   ansible-playbook reported unreachable hosts, or AOM detected
      a CLI usage error (e.g. duplicate playbook positional)
  127 ansible-playbook executable not found
  130 cancelled by user (Ctrl+C)

See README.md and SPECIFICATION.md in the source tree for full details.
        """,
    )

    parser.add_argument(
        "--tui",
        action="store_true",
        help="Launch full multi-panel TUI instead of compact view",
    )

    parser.add_argument(
        "--format",
        choices=["compact", "json"],
        default="compact",
        help=(
            "Output format. 'compact' (default) streams the nom-style live view. "
            "'json' is silent during the run and emits a single JSON object on stdout "
            "at completion — designed for CI and `jq` pipelines. "
            "Mutually exclusive with --tui."
        ),
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print AOM pre-execution diagnostics and enable DEBUG logging",
    )

    parser.add_argument(
        "--no-record",
        action="store_true",
        dest="no_record",
        help=(
            "Disable session recording for this run. "
            "No directory is written under ~/.local/state/aom/sessions/."
        ),
    )

    parser.add_argument(
        "--install-completion",
        choices=("bash", "zsh", "fish"),
        metavar="SHELL",
        default=None,
        help=(
            "Print the rc-file snippet for the given shell to stdout, "
            "then exit. Pipe to your rc file (e.g. "
            "`aom --install-completion bash >> ~/.bashrc`)."
        ),
    )

    parser.add_argument(
        "playbook",
        nargs="?",
        default=None,
        help="Playbook file to run",
    )

    parser.add_argument(
        "ansible_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments passed to ansible-playbook",
    )

    # F5: arm shell completion. No-op unless the shell wrapper sets
    # the _ARGCOMPLETE env var, so this is free on the normal CLI path.
    argcomplete.autocomplete(parser)

    return parser


def _run_compact(
    playbook: str,
    ansible_args: list[str],
    record: bool = True,
    format: str = "compact",
) -> int:
    """Spawn the streaming renderer (compact ANSI or end-of-run JSON) via a LiveDriver.

    The composition root pattern: one EventSource (LiveDriver), one
    Renderer (factory-built), one call. See ARCHITECTURE.md §4.
    """
    from typing import cast

    from ansible_aom.drivers.live import LiveDriver
    from ansible_aom.renderer.factory import RenderMode, create_renderer

    try:
        renderer = create_renderer(
            mode=cast(RenderMode, format),
            is_tty=sys.stdout.isatty(),
        )
        driver = LiveDriver(playbook, ansible_args, record=record)
        return driver.drive(renderer)
    except KeyboardInterrupt:
        print("Cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _run_tui(playbook: str, ansible_args: list[str], record: bool = True) -> int:
    """Launch the Textual TUI driven by a LiveDriver.

    AOMApp owns its own event loop (``app.run()``) and pumps the
    driver from a worker thread; the driver wraps the same pexpect
    runner the compact path uses. ``app.exit_code`` is whatever
    ``driver.drive`` returned, reachable after ``app.run()`` exits.
    ``None`` (user quit before completion) maps to exit 1 — we treat
    an aborted-by-quit run as non-success without pretending to know
    the playbook's true outcome.
    """
    from ansible_aom.drivers.live import LiveDriver
    from ansible_aom.tui.app import AOMApp

    try:
        driver = LiveDriver(playbook, ansible_args, record=record)
        app = AOMApp(driver=driver, playbook=playbook, ansible_args=ansible_args)
        app.run()
    except KeyboardInterrupt:
        print("Cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    exit_code = app.exit_code
    return exit_code if exit_code is not None else 1


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    from ansible_aom.core import diagnostics

    diagnostics.install_from_env()

    if "--version" in sys.argv:
        from ansible_aom import source_hash

        # Install-time metadata version + live source-tree hash. The
        # version comes from the installed .dist-info (snapshotted by
        # uv/pip at install time) and can be stale for editable
        # installs. The src hash, by contrast, is computed from the
        # .py files Python is currently importing — so if the two
        # don't match a known-good reference, the user can tell at a
        # glance whether the running code matches what they think
        # they have installed.
        print(f"aom {__version__} ({source_hash()})")
        return 0

    if "--help" in sys.argv or "-h" in sys.argv:
        create_parser().print_help()
        return 0

    if "--install-completion" in sys.argv:
        from ansible_aom.completion import SUPPORTED_SHELLS, completion_snippet

        # Read the value ourselves; we cannot call create_parser().parse_args()
        # here because argcomplete may have side-effects we want to avoid on
        # this fast path, and because parse_args would also require a playbook
        # later in main(). Pulling the value with a tiny lookup keeps the path
        # explicit and side-effect-free.
        idx = sys.argv.index("--install-completion")
        shell = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""
        if shell not in SUPPORTED_SHELLS:
            print(
                f"aom: unsupported shell {shell!r}; expected one of {', '.join(SUPPORTED_SHELLS)}",
                file=sys.stderr,
            )
            return 2
        sys.stdout.write(completion_snippet(shell))
        return 0

    if len(sys.argv) > 1 and sys.argv[1] == "replay":
        from ansible_aom.drivers.replay import cli_main as replay_main

        return replay_main(sys.argv[2:])

    if len(sys.argv) > 1 and sys.argv[1] == "inspect":
        from ansible_aom.inspect.cli import main as inspect_main

        return inspect_main(sys.argv[2:])

    if len(sys.argv) > 1 and sys.argv[1] == "rerun":
        from ansible_aom.rerun.cli import main as rerun_main

        return rerun_main(sys.argv[2:])

    parser = create_parser()
    args = parser.parse_args()

    if args.verbose:
        aom_logger = logging.getLogger("ansible_aom")
        aom_logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        aom_logger.addHandler(console_handler)

        ansible_path = shutil.which("ansible-playbook")
        print(f"ansible-playbook path: {ansible_path or 'not found'}")
        print(f"ANSIBLE_STDOUT_CALLBACK: {os.environ.get('ANSIBLE_STDOUT_CALLBACK', '(not set)')}")
        print(f"Terminal: tty={sys.stdout.isatty()}, columns={shutil.get_terminal_size().columns}")
        aom_logger.debug("--list-tasks summary: verbose mode enabled, diagnostics printed")

    if args.playbook:
        if args.tui and args.format == "json":
            print(
                "aom: --tui and --format json are mutually exclusive. "
                "Use --format json without --tui for end-of-run JSON output.",
                file=sys.stderr,
            )
            return 2

        if detect_duplicate_playbook(args.playbook, args.ansible_args):
            print(
                f"aom: '{args.playbook}' appears twice on the command line — "
                "drop the trailing duplicate.",
                file=sys.stderr,
            )
            return 2

        ansible_args = ensure_inventory_arg(merge_limit_args(args.ansible_args))

        record = not args.no_record
        if args.tui:
            return _run_tui(args.playbook, ansible_args, record=record)
        return _run_compact(args.playbook, ansible_args, record=record, format=args.format)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
