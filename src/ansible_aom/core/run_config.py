"""Pure normalization of an ansible-playbook invocation into a hashable key.

The :class:`RunConfigKey` is the load-bearing identity used by the history
lookup feature: two invocations that "do the same thing" must produce equal
keys, while invocations that differ in a way that matters for runtime (tags,
``--start-at-task``, ``--step`` pacing, etc.) must produce different keys.

This module is intentionally pure stdlib — it lives in ``core/`` and must not
import any infrastructure. The argv parser is a small index-based loop so
``flag value`` pairs can be consumed together while unknown tokens are dropped
without crashing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Verbosity flags and other no-op-for-identity boolean flags.
_IGNORED_BOOL_FLAGS: frozenset[str] = frozenset(
    {
        "-v",
        "-vv",
        "-vvv",
        "-vvvv",
        "--verbose",
        "--syntax-check",
    }
)


@dataclass(frozen=True, slots=True)
class RunConfigKey:
    """Hashable normalization of an ansible-playbook invocation.

    Equality semantics are defined by the field set: two keys are equal iff
    every field matches. ``tags``, ``skip_tags`` and ``extra_vars`` are sorted
    tuples (order does not matter to ansible); ``inventories`` keeps source
    order because ansible merges multiple ``-i`` left-to-right.
    """

    playbook: str
    inventories: tuple[str, ...]
    limit: str | None
    tags: tuple[str, ...]
    skip_tags: tuple[str, ...]
    extra_vars: tuple[str, ...]
    check: bool
    diff: bool
    start_at_task: str | None
    step: bool


def _split_csv_sorted(value: str) -> tuple[str, ...]:
    """Split a comma-separated flag value, strip whitespace, drop empties, sort."""
    parts = [p.strip() for p in value.split(",")]
    return tuple(sorted(p for p in parts if p))


def build_run_config_key(*, playbook: str, ansible_args: list[str]) -> RunConfigKey:
    """Build a :class:`RunConfigKey` from a playbook path and ansible argv tail.

    ``ansible_args`` is the list of tokens that would be passed to
    ``ansible-playbook`` *after* the playbook path itself. Unknown tokens are
    silently dropped — a future ansible flag must never crash this parser. The
    acceptable trade-off is that two argvs differing only by an unknown flag
    will bucket together (the history hint may be slightly off, never wrong).
    """
    inventories: list[str] = []
    limit: str | None = None
    tags: tuple[str, ...] = ()
    skip_tags: tuple[str, ...] = ()
    extra_vars: list[str] = []
    check = False
    diff = False
    start_at_task: str | None = None
    step = False

    i = 0
    n = len(ansible_args)
    while i < n:
        token = ansible_args[i]

        if token in _IGNORED_BOOL_FLAGS:
            i += 1
            continue

        if token in ("-i", "--inventory", "--inventory-file"):
            if i + 1 < n:
                inventories.append(ansible_args[i + 1])
                i += 2
            else:
                i += 1
            continue

        if token in ("-l", "--limit"):
            if i + 1 < n:
                limit = ansible_args[i + 1]
                i += 2
            else:
                i += 1
            continue

        if token in ("-t", "--tags"):
            if i + 1 < n:
                tags = _split_csv_sorted(ansible_args[i + 1])
                i += 2
            else:
                i += 1
            continue

        if token == "--skip-tags":
            if i + 1 < n:
                skip_tags = _split_csv_sorted(ansible_args[i + 1])
                i += 2
            else:
                i += 1
            continue

        if token in ("-e", "--extra-vars"):
            if i + 1 < n:
                extra_vars.append(ansible_args[i + 1])
                i += 2
            else:
                i += 1
            continue

        if token == "--check":
            check = True
            i += 1
            continue

        if token == "--diff":
            diff = True
            i += 1
            continue

        if token == "--start-at-task":
            if i + 1 < n:
                start_at_task = ansible_args[i + 1]
                i += 2
            else:
                i += 1
            continue

        if token == "--step":
            step = True
            i += 1
            continue

        # Unknown token: advance by one. We don't know whether it takes a
        # value, so we can't reliably consume the next token; leaving the
        # next token to be inspected on the next iteration is the safest
        # default — if it happens to be a known flag, we still pick it up.
        i += 1

    return RunConfigKey(
        playbook=str(Path(playbook).resolve()),
        inventories=tuple(inventories),
        limit=limit,
        tags=tags,
        skip_tags=skip_tags,
        extra_vars=tuple(sorted(extra_vars)),
        check=check,
        diff=diff,
        start_at_task=start_at_task,
        step=step,
    )
