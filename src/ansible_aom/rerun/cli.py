"""CLI entry point for ``aom rerun``.

Reads a recorded session, derives a host list from failures /
unreachable / changes, and re-invokes ``ansible-playbook`` with the
original args plus a ``--limit`` matching the derived hosts.

The only piece in this file that's not pure-CLI plumbing is host-set
composition; the actual set computation lives in ``core.session``
(``collect_failed_hosts`` etc.) so it stays testable in isolation
and ``core/`` keeps its no-renderer rule.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

from ansible_aom.core.session import (
    collect_changed_hosts,
    collect_failed_hosts,
    collect_unreachable_hosts,
    list_sessions,
)


def _resolve_session_id(state_dir: Path, session_id_or_short: str | None) -> str:
    """Resolve an explicit session ID, short prefix, or "most recent" intent.

    Mirrors the inspect command's resolution semantics: full UUID wins
    over prefix match, prefix match must be unique, "no argument" picks
    the most recent session by start_time.

    Args:
        state_dir: Directory containing session sub-directories.
        session_id_or_short: Either a full 36-char UUID, an 8-char (or
            longer) prefix, or ``None`` to pick the latest session.

    Returns:
        The resolved full session ID.

    Raises:
        LookupError: When no session matches, no sessions exist at all,
            or a short prefix matches more than one session.
    """
    sessions = list_sessions(state_dir)
    if not sessions:
        raise LookupError(f"No sessions found in {state_dir}")

    if session_id_or_short is None:
        # list_sessions returns newest-first.
        return sessions[0]["session_id"]

    # Exact full-id match wins.
    for s in sessions:
        if s["session_id"] == session_id_or_short:
            return session_id_or_short

    # Otherwise treat as prefix.
    matches = [s for s in sessions if s["session_id"].startswith(session_id_or_short)]
    if not matches:
        raise LookupError(f"No session matching {session_id_or_short!r} in {state_dir}")
    if len(matches) > 1:
        ids = ", ".join(s["session_id"] for s in matches)
        raise LookupError(f"Prefix {session_id_or_short!r} is ambiguous: matches {ids}")
    return matches[0]["session_id"]


def _compose_host_set(
    session: dict,
    *,
    failed: bool,
    unreachable: bool,
    changes_only: bool,
) -> set[str]:
    """Combine the requested host categories into a single set.

    Semantics (from the F4 spec):
    - No flag → behave like ``--failed`` (the most common case).
    - ``--unreachable`` is a strict *superset* of ``--failed``: hosts
      that failed AND hosts that were unreachable. We never return only
      unreachable hosts on its own.
    - ``--changes-only`` adds hosts whose tasks reported ``changed: true``.
    - Multiple flags compose by union.

    Args:
        session: Loaded session dict (from ``load_session``).
        failed: Include hosts that hit ``v2_runner_on_failed``.
        unreachable: Include hosts from both failed AND unreachable.
        changes_only: Include hosts that had at least one changed task.

    Returns:
        Union of the requested host categories.
    """
    if not failed and not unreachable and not changes_only:
        # Default behaviour matches `--failed` so the bare command does
        # the most common thing.
        return collect_failed_hosts(session)

    hosts: set[str] = set()
    if failed:
        hosts |= collect_failed_hosts(session)
    if unreachable:
        # --unreachable means "everything to retry": failed ∪ unreachable.
        hosts |= collect_failed_hosts(session)
        hosts |= collect_unreachable_hosts(session)
    if changes_only:
        hosts |= collect_changed_hosts(session)
    return hosts


def _strip_limit_args(args: list[str]) -> list[str]:
    """Drop any pre-existing ``--limit`` / ``-l`` from the args list.

    Handles three forms:
    - ``--limit foo``      (two tokens)
    - ``--limit=foo``      (one token)
    - ``-l foo``           (two tokens, short form)

    A pre-existing limit is replaced — not unioned — because the user
    explicitly chose a subset by running ``aom rerun --failed``.
    Silently honouring an old ``--limit web1`` would intersect that
    with the failed set and could empty it, surprising the user.
    """
    out: list[str] = []
    skip_next = False
    for tok in args:
        if skip_next:
            skip_next = False
            continue
        if tok in ("--limit", "-l"):
            skip_next = True
            continue
        if tok.startswith("--limit="):
            continue
        out.append(tok)
    return out


def _build_rerun_command(
    session: dict,
    hosts: set[str],
) -> tuple[str, list[str]]:
    """Construct the (playbook, ansible_args) pair to spawn for the rerun.

    The session's recorded ``ansible_args`` are forwarded verbatim
    except for any pre-existing ``--limit`` / ``-l`` flags, which are
    dropped in favour of one built from ``hosts``. The new ``--limit``
    value is the sorted, comma-joined host list (sorted for
    determinism — the underlying set has no order).

    Args:
        session: Loaded session dict (must contain ``playbook`` and
            ``ansible_args``).
        hosts: Non-empty set of hostnames to limit the rerun to.

    Returns:
        ``(playbook_path, ansible_args)`` tuple ready for
        ``run_playbook``.

    Raises:
        ValueError: If ``hosts`` is empty (caller is expected to handle
            "nothing to rerun" before reaching this function).
    """
    if not hosts:
        raise ValueError("Cannot build rerun command for empty host set")
    playbook = session["playbook"]
    original_args = list(session.get("ansible_args") or [])
    cleaned = _strip_limit_args(original_args)
    limit_value = ",".join(sorted(hosts))
    return playbook, [*cleaned, "--limit", limit_value]


def _confirm(
    *,
    playbook: str,
    args: list[str],
    host_count: int,
    assume_yes: bool,
    input_fn: Callable[[str], str] | None,
) -> bool:
    """Print the rerun plan + warning, then ask for Y/n confirmation.

    Always prints the planned command line, host count, and a
    one-line warning that re-running may execute non-idempotent tasks
    (notifications, side-effecting modules, etc.) — this happens even
    when ``assume_yes`` is set so the user sees what's about to fire.

    Args:
        playbook: Resolved playbook path.
        args: Final ansible-playbook arg list (already includes
            ``--limit``).
        host_count: Length of the resolved host set, used for the
            "running on N host(s)" line.
        assume_yes: When True, skip the prompt and return True
            unconditionally (still prints the plan).
        input_fn: Injectable for tests. Defaults to ``builtins.input``
            when None and ``assume_yes`` is False; ignored when
            ``assume_yes`` is True.

    Returns:
        True if the user confirmed (or ``--yes`` was passed), False
        otherwise.
    """
    plural = "host" if host_count == 1 else "hosts"
    cmd_str = "ansible-playbook " + playbook + (" " + " ".join(args) if args else "")
    print(f"Planned: {cmd_str}")
    print(f"Targeting {host_count} {plural}.")
    print(
        "WARNING: re-running may execute non-idempotent tasks again "
        "(notifications, restarts, side-effecting modules)."
    )
    if assume_yes:
        return True

    fn = input_fn if input_fn is not None else input
    answer = fn("Proceed? [Y/n] ").strip().lower()
    if answer == "":
        return True
    return answer in ("y", "yes")


def _require_ansible_args(session: dict, session_id: str) -> list[str]:
    """Return the recorded ``ansible_args`` or refuse with a clear error.

    Sessions recorded by AOM ≥ schema 1.1 always have ``ansible_args``
    in ``meta.json`` (an empty list when no flags were passed). Older
    sessions don't have the field at all; rather than guess what flags
    the user originally ran, we refuse and explain.

    The schema bump is documented in the project changelog and in the
    docstring on ``SessionManager.start_session``.

    Args:
        session: Loaded session dict.
        session_id: Used in the error message so the user knows which
            session triggered the refusal.

    Returns:
        The recorded ``ansible_args`` list (possibly empty).

    Raises:
        SystemExit(2): If the field is missing or null.
    """
    args = session.get("ansible_args")
    if args is None:
        print(
            f"aom rerun: session {session_id} is missing 'ansible_args' "
            "in meta.json. This field was added in AOM session schema "
            "1.1 — older sessions cannot be re-run automatically because "
            "AOM doesn't know which flags (e.g. -i, --tags, --extra-vars) "
            "were originally passed. Re-record the session with the "
            "current AOM, or invoke ansible-playbook manually with "
            "--limit.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return list(args)


def _create_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for ``aom rerun``.

    Split out from ``main`` so tests can drive parsing in isolation.
    """
    parser = argparse.ArgumentParser(
        prog="aom rerun",
        description=(
            "Re-invoke ansible-playbook on hosts that need attention from "
            "a recorded session."
        ),
    )
    parser.add_argument(
        "session_id",
        nargs="?",
        default=None,
        help="Session ID (full UUID or 8-char prefix). Defaults to the latest session.",
    )
    parser.add_argument(
        "--failed",
        action="store_true",
        help="Re-run on hosts that hit v2_runner_on_failed (default when no flag is given).",
    )
    parser.add_argument(
        "--unreachable",
        action="store_true",
        help="Re-run on failed AND unreachable hosts.",
    )
    parser.add_argument(
        "--changes-only",
        action="store_true",
        dest="changes_only",
        help="Re-run on hosts that had at least one changed task.",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt.",
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        dest="state_dir",
        default=Path.home() / ".local" / "state" / "aom" / "sessions",
        help="Directory containing session data (default: ~/.local/state/aom/sessions).",
    )
    return parser


def _default_runner(playbook: str, ansible_args: list[str]) -> int:
    """Real-world runner: spawn the renderer + run_playbook.

    Lazy-imported so unit tests can stub ``runner`` without paying the
    cost of importing pexpect / Textual.
    """
    from ansible_aom.renderer.factory import create_renderer
    from ansible_aom.runner import run_playbook

    renderer = create_renderer(tui_mode=False, is_tty=sys.stdout.isatty())
    return run_playbook(playbook, ansible_args, renderer)


def main(
    argv: list[str] | None = None,
    *,
    runner: Callable[[str, list[str]], int] | None = None,
    input_fn: Callable[[str], str] | None = None,
) -> int:
    """CLI entry point for ``aom rerun``.

    Args:
        argv: Argument list. If None, parses from ``sys.argv``. The
            top-level dispatcher in ``ansible_aom.cli`` passes
            ``sys.argv[2:]`` so the ``rerun`` token is consumed first.
        runner: Injectable rerun executor. Defaults to
            ``_default_runner`` (which spawns a real ansible-playbook
            via ``run_playbook``). Tests pass a fake to avoid
            subprocesses.
        input_fn: Injectable input function for the confirmation
            prompt. Defaults to ``builtins.input``. Tests pass a
            lambda.

    Returns:
        Exit code:
            0 — rerun completed (or was declined cleanly by the user)
            1 — no sessions / no hosts to rerun / unknown session
            2 — old session missing ``ansible_args`` (schema mismatch)
            other — propagated from ``runner``
    """
    from ansible_aom.core.session import load_session

    args = _create_parser().parse_args(argv)

    try:
        session_id = _resolve_session_id(args.state_dir, args.session_id)
    except LookupError as exc:
        print(f"aom rerun: {exc}", file=sys.stderr)
        return 1

    session = load_session(session_id, args.state_dir)
    if session is None:
        print(f"aom rerun: failed to load session {session_id}", file=sys.stderr)
        return 1

    # _require_ansible_args raises SystemExit(2) on missing field; we
    # catch it here so callers (and tests) see a clean integer return
    # rather than a propagated exception.
    try:
        ansible_args_recorded = _require_ansible_args(session, session_id)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 2
        return code
    # Replace whatever was on the loaded dict (defensive: ensures the
    # downstream builder sees the validated list).
    session["ansible_args"] = ansible_args_recorded

    hosts = _compose_host_set(
        session,
        failed=args.failed,
        unreachable=args.unreachable,
        changes_only=args.changes_only,
    )

    if not hosts:
        print(
            f"aom rerun: no hosts to rerun in session {session_id} "
            f"(nothing matched the requested filter).",
            file=sys.stderr,
        )
        return 1

    playbook, rerun_args = _build_rerun_command(session, hosts)

    if not _confirm(
        playbook=playbook,
        args=rerun_args,
        host_count=len(hosts),
        assume_yes=args.yes,
        input_fn=input_fn,
    ):
        return 0

    runner_fn = runner if runner is not None else _default_runner
    return runner_fn(playbook, rerun_args)
