"""Shell-completion helpers for the AOM CLI (F5).

Two responsibilities:

1. ``session_id_completer`` — argcomplete-compatible callable that
   returns the list of recorded session IDs under
   ``~/.local/state/aom/sessions/`` (or an explicit ``state_dir``
   passed for tests). It must accept argcomplete's standard kwargs
   (``prefix``, ``parsed_args``, ``**kwargs``) and never raise — a
   missing state dir simply yields no completions.

2. ``completion_snippet`` — returns the rc-file snippet a user
   sources to enable completion for the chosen shell. We delegate to
   argcomplete's ``register-python-argcomplete`` helper rather than
   hand-rolling shell glue, because that helper is the one place
   argcomplete commits to a stable wire-format across versions.

The shell wrappers all run ``register-python-argcomplete aom`` once
per shell startup; the wrapper that is emitted by argcomplete then
sets the ``_ARGCOMPLETE`` env var when the user hits tab, which is
what ``argcomplete.autocomplete(parser)`` checks for in
``cli.create_parser``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

SUPPORTED_SHELLS: tuple[str, str, str] = ("bash", "zsh", "fish")


def _default_state_dir() -> Path:
    """Resolve the default sessions directory.

    Mirrors the literal used by ``inspect/cli.py`` so completion and
    inspection share the same source of truth without importing from
    inspect (which would create a needless dependency edge).
    """
    return Path(os.path.expanduser("~")) / ".local" / "state" / "aom" / "sessions"


def session_id_completer(
    prefix: str = "",
    parsed_args: Any = None,
    state_dir: Path | None = None,
    **_kwargs: Any,
) -> list[str]:
    """Return session IDs under ``state_dir`` whose names start with ``prefix``.

    The signature matches argcomplete's contract — it always passes
    ``prefix``, ``parsed_args``, ``action``, and ``parser`` as kwargs.
    We accept and ignore the unused extras via ``**_kwargs``.

    Args:
        prefix: The partial token the user has typed so far.
        parsed_args: argparse Namespace argcomplete has built so far.
            Unused here, accepted for protocol compatibility.
        state_dir: Override the default ``~/.local/state/aom/sessions``
            location. Tests pass a tmp_path; production passes None.

    Returns:
        Sorted list of session-ID directory names. Empty list when the
        state dir is missing or empty.
    """
    base = state_dir if state_dir is not None else _default_state_dir()
    if not base.exists():
        return []
    return [
        entry.name for entry in base.iterdir() if entry.is_dir() and entry.name.startswith(prefix)
    ]


def completion_snippet(shell: str) -> str:
    """Return the rc-file snippet to enable AOM tab-completion in ``shell``.

    The snippet shells out to ``register-python-argcomplete``, which
    is installed alongside the ``argcomplete`` package and emits the
    appropriate ``complete -F`` (bash) / ``compdef`` (zsh) /
    ``complete -c`` (fish) glue for the given program name.

    Args:
        shell: One of ``SUPPORTED_SHELLS``.

    Returns:
        Multiline string the user pipes / sources from their rc file.

    Raises:
        ValueError: ``shell`` is not in ``SUPPORTED_SHELLS``.
    """
    if shell not in SUPPORTED_SHELLS:
        raise ValueError(f"unsupported shell {shell!r}; expected one of {SUPPORTED_SHELLS}")

    if shell == "bash":
        return (
            '# AOM bash completion - add to ~/.bashrc:\neval "$(register-python-argcomplete aom)"\n'
        )
    if shell == "zsh":
        return (
            "# AOM zsh completion - add to ~/.zshrc:\n"
            "autoload -U bashcompinit && bashcompinit\n"
            'eval "$(register-python-argcomplete aom)"\n'
        )
    # fish
    return (
        "# AOM fish completion - add to ~/.config/fish/config.fish:\n"
        "register-python-argcomplete --shell fish aom | source\n"
    )
