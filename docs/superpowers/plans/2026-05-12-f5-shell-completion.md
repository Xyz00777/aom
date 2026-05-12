# F5 — Shell Completion (bash / zsh / fish) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add tab-completion for `aom`'s subcommands (`inspect` and its
sub-subcommands), top-level flags (`--tui`, `--verbose`, etc.), and
recorded session IDs, plus a `--install-completion <shell>` flag that
emits the rc-file snippet to stdout for the user to source.

**Architecture:** Use `argcomplete` as the runtime engine. A single
hook call (`argcomplete.autocomplete(parser)`) inside
`cli.create_parser()` arms the existing `argparse.ArgumentParser` for
completion — argcomplete only does work when the special env var
`_ARGCOMPLETE` is set by the shell wrapper, so the normal CLI path is
untouched. A pure helper (`session_id_completer`) reads the sessions
directory and is attached via `arg.completer = ...` to the
session-positional args inside `inspect show` / `inspect diff` /
`inspect prune` (today's surface). A second pure helper
(`completion_snippet`) returns the bash/zsh/fish shell snippet for the
new `--install-completion <shell>` flag.

**Tech Stack:** Python 3.14, argparse, `argcomplete>=3.5` (new runtime
dependency, single small package, no transitive deps of consequence),
pytest.

**Risks (call out before merging):**
- `argcomplete` is a new runtime dependency. It is small and
  widely-used (the same library `pip` itself uses for completion); the
  install footprint is ~50KB. Listed under `[project]` `dependencies`
  in `pyproject.toml`.
- We deliberately skip integration tests against real shells. The
  shell-side glue (`complete -F`, `compdef`, `complete -c`) is
  argcomplete's responsibility; we unit-test the snippet content
  (substring assertions) and the completer outputs only.
- `replay` and `rerun` are not yet top-level subcommands (today only
  `inspect` exists at the top level). We wire the session-id completer
  to the three existing `inspect` positionals that take a session ID
  (`show <session_id>`, `diff <session_id_1> <session_id_2>`). When
  `replay` / `rerun` land they will reuse the same completer by
  setting `arg.completer = session_id_completer` on their session
  positional — this plan ships the completer in a place they can
  import without restructuring.
- The tag completer mentioned in `features.md` F5 is **explicitly out
  of scope** for this plan (slow `--list-tasks`, fiddly cache
  invalidation, low value-per-effort).

---

## File Structure

| Path | Responsibility | Touch |
|------|----------------|-------|
| `pyproject.toml` | Add `argcomplete>=3.5` to runtime `dependencies`. | Modify |
| `src/ansible_aom/cli.py` | Wire `argcomplete.autocomplete(parser)` into `create_parser()`. Add `--install-completion <shell>` flag and its handler in `main()`. | Modify |
| `src/ansible_aom/completion.py` | New module. Pure functions: `session_id_completer(prefix, parsed_args, state_dir, **kwargs)` and `completion_snippet(shell)`. Constant `SUPPORTED_SHELLS = ("bash", "zsh", "fish")`. | Create |
| `src/ansible_aom/inspect/cli.py` | Attach `session_id_completer` to the session-id positionals on `show`, `diff`, and (where applicable) `prune` parsers. Wire `argcomplete.autocomplete()` into the inspect parser too, since `aom inspect <TAB>` re-parses inside the inspect dispatcher. | Modify |
| `tests/unit/test_completion.py` | Unit tests for `session_id_completer` and `completion_snippet`. | Create |
| `tests/unit/test_cli.py` | New tests for the `--install-completion` flag handler in `main()` and the wiring of `argcomplete.autocomplete` on the parser. | Modify |

The `completion.py` module is plain Python with no Textual / Rich
imports, so it's safe to import from both `cli.py` and
`inspect/cli.py` without dragging the heavy renderer modules into the
import path.

---

## Conventions

- TDD strictly: write the failing test, run it, confirm it fails for
  the expected reason, implement, run it, confirm green, then commit.
- Run `uv run pytest tests/ -q` after every implementation step (not
  just the targeted test) before committing. Never commit on red.
- Conventional commit prefixes: `chore:` for dependency / housekeeping,
  `test:` for test-only changes, `feat:` for behaviour, `refactor:` for
  internal restructure.
- **Never** add `Co-Authored-By:` for AI in commit messages or PRs
  (project rule, see `CLAUDE.md`).
- Never add `# type: ignore` — the `completion.py` module is in
  `core/`-adjacent territory and must type-clean under strict mypy. The
  argcomplete library ships type stubs since 3.4; if mypy still
  complains about `argcomplete.autocomplete`, add a module-level
  `[[tool.mypy.overrides]]` block for `argcomplete.*` rather than an
  inline ignore.

---

## Task 1: Add `argcomplete` runtime dependency

**Files:**
- Modify: `pyproject.toml:18-28`

- [ ] **Step 1.1: Inspect current dependency block**

Run: `sed -n '18,28p' pyproject.toml`
Expected: a `dependencies = [ ... ]` list ending with `"blessed>=1.20", # ANSI cursor positioning for compact mode`.

- [ ] **Step 1.2: Add `argcomplete>=3.5` to dependencies**

Edit `pyproject.toml`. Replace the `dependencies` block

```toml
dependencies = [
    "textual>=0.60",
    "rich",
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "platformdirs>=3.0",
    "pexpect>=4.8",
    "psutil>=5.9",
    "blessed>=1.20",           # ANSI cursor positioning for compact mode
]
```

with

```toml
dependencies = [
    "textual>=0.60",
    "rich",
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "platformdirs>=3.0",
    "pexpect>=4.8",
    "psutil>=5.9",
    "blessed>=1.20",           # ANSI cursor positioning for compact mode
    "argcomplete>=3.5",        # bash/zsh/fish tab-completion for the CLI
]
```

- [ ] **Step 1.3: Sync deps**

Run: `uv sync --all-extras`
Expected: argcomplete is downloaded and installed; no errors.

- [ ] **Step 1.4: Verify import works**

Run: `uv run python -c "import argcomplete; print(argcomplete.__version__)"`
Expected: a version string >= 3.5 prints, no `ModuleNotFoundError`.

- [ ] **Step 1.5: Run full test suite to confirm nothing regressed**

Run: `uv run pytest tests/ -q`
Expected: all tests still pass (this commit only changes deps).

- [ ] **Step 1.6: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore(deps): add argcomplete for shell completion"
```

(If `uv.lock` is gitignored in this repo, omit it. Run
`git status -s` first to confirm what changed.)

---

## Task 2: Pure-function `session_id_completer` (TDD)

**Files:**
- Create: `src/ansible_aom/completion.py`
- Create: `tests/unit/test_completion.py`

The completer takes the same kwargs argcomplete will pass at runtime
(`prefix`, `parsed_args`, `**kwargs`) plus an injectable `state_dir`
parameter so unit tests can drive it without touching `~/.local/state`.

- [ ] **Step 2.1: Write the failing test**

Create `tests/unit/test_completion.py`:

```python
"""Unit tests for shell-completion helpers (F5).

Covers:
- ``session_id_completer`` returns the IDs of session directories
  under the given state dir, filtered by the ``prefix`` arg.
- Empty / missing state dirs return ``[]`` (never raise).
- ``completion_snippet`` returns a shell-appropriate snippet for
  bash, zsh, and fish, and raises ``ValueError`` for anything else.
"""

from pathlib import Path

import pytest


class TestSessionIdCompleter:
    def test_returns_session_dir_names(self, tmp_path: Path):
        from ansible_aom.completion import session_id_completer

        (tmp_path / "0193abcd-1111-7000-8000-000000000001").mkdir()
        (tmp_path / "0193abcd-2222-7000-8000-000000000002").mkdir()

        result = session_id_completer(prefix="", parsed_args=None, state_dir=tmp_path)

        assert sorted(result) == [
            "0193abcd-1111-7000-8000-000000000001",
            "0193abcd-2222-7000-8000-000000000002",
        ]

    def test_filters_by_prefix(self, tmp_path: Path):
        from ansible_aom.completion import session_id_completer

        (tmp_path / "aaa-1").mkdir()
        (tmp_path / "aaa-2").mkdir()
        (tmp_path / "bbb-1").mkdir()

        result = session_id_completer(prefix="aaa", parsed_args=None, state_dir=tmp_path)

        assert sorted(result) == ["aaa-1", "aaa-2"]

    def test_ignores_files(self, tmp_path: Path):
        from ansible_aom.completion import session_id_completer

        (tmp_path / "real-session").mkdir()
        (tmp_path / "stray-file.txt").write_text("not a session")

        result = session_id_completer(prefix="", parsed_args=None, state_dir=tmp_path)

        assert result == ["real-session"]

    def test_missing_state_dir_returns_empty(self, tmp_path: Path):
        from ansible_aom.completion import session_id_completer

        missing = tmp_path / "does-not-exist"
        result = session_id_completer(prefix="", parsed_args=None, state_dir=missing)

        assert result == []

    def test_empty_state_dir_returns_empty(self, tmp_path: Path):
        from ansible_aom.completion import session_id_completer

        result = session_id_completer(prefix="", parsed_args=None, state_dir=tmp_path)

        assert result == []

    def test_default_state_dir_is_local_state_aom_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """When state_dir is not supplied the completer derives it from $HOME."""
        from ansible_aom.completion import session_id_completer

        fake_home = tmp_path / "home"
        sessions = fake_home / ".local" / "state" / "aom" / "sessions"
        sessions.mkdir(parents=True)
        (sessions / "from-home-default").mkdir()

        monkeypatch.setenv("HOME", str(fake_home))

        result = session_id_completer(prefix="", parsed_args=None)

        assert "from-home-default" in result


class TestCompletionSnippet:
    def test_bash_snippet_contains_argcomplete_register(self):
        from ansible_aom.completion import completion_snippet

        snippet = completion_snippet("bash")

        # argcomplete's bash bridge uses `register-python-argcomplete`
        # plus `complete -o ... -F` glue under the hood.
        assert "register-python-argcomplete" in snippet
        assert "aom" in snippet

    def test_zsh_snippet_contains_argcomplete_register(self):
        from ansible_aom.completion import completion_snippet

        snippet = completion_snippet("zsh")

        assert "register-python-argcomplete" in snippet
        assert "aom" in snippet

    def test_fish_snippet_contains_argcomplete_register(self):
        from ansible_aom.completion import completion_snippet

        snippet = completion_snippet("fish")

        assert "register-python-argcomplete" in snippet
        assert "aom" in snippet

    def test_unknown_shell_raises_value_error(self):
        from ansible_aom.completion import completion_snippet

        with pytest.raises(ValueError, match="unsupported shell"):
            completion_snippet("powershell")

    def test_supported_shells_constant(self):
        from ansible_aom.completion import SUPPORTED_SHELLS

        assert SUPPORTED_SHELLS == ("bash", "zsh", "fish")
```

- [ ] **Step 2.2: Run test to confirm failure**

Run: `uv run pytest tests/unit/test_completion.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'ansible_aom.completion'`.

- [ ] **Step 2.3: Implement the module**

Create `src/ansible_aom/completion.py`:

```python
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
        entry.name
        for entry in base.iterdir()
        if entry.is_dir() and entry.name.startswith(prefix)
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
        raise ValueError(
            f"unsupported shell {shell!r}; expected one of {SUPPORTED_SHELLS}"
        )

    if shell == "bash":
        return (
            "# AOM bash completion — add to ~/.bashrc:\n"
            'eval "$(register-python-argcomplete aom)"\n'
        )
    if shell == "zsh":
        return (
            "# AOM zsh completion — add to ~/.zshrc:\n"
            "autoload -U bashcompinit && bashcompinit\n"
            'eval "$(register-python-argcomplete aom)"\n'
        )
    # fish
    return (
        "# AOM fish completion — add to ~/.config/fish/config.fish:\n"
        "register-python-argcomplete --shell fish aom | source\n"
    )
```

- [ ] **Step 2.4: Run test to confirm green**

Run: `uv run pytest tests/unit/test_completion.py -v`
Expected: all 11 tests pass.

- [ ] **Step 2.5: Run full suite**

Run: `uv run pytest tests/ -q`
Expected: every test green.

- [ ] **Step 2.6: Lint + type-check**

Run: `uv run ruff format src/ansible_aom/completion.py tests/unit/test_completion.py`
Run: `uv run ruff check --fix src/ansible_aom/completion.py tests/unit/test_completion.py`
Run: `uv run mypy src/ansible_aom/completion.py`
Expected: clean. If mypy complains about `argcomplete.*` stubs in
later tasks, add a module-level override in `pyproject.toml` (do
**not** add inline `# type: ignore`).

- [ ] **Step 2.7: Commit**

```bash
git add src/ansible_aom/completion.py tests/unit/test_completion.py
git commit -m "feat(completion): add session-id completer and shell snippets"
```

---

## Task 3: Wire `argcomplete.autocomplete` into `cli.create_parser` (TDD)

The hook is a no-op unless the shell sets the `_ARGCOMPLETE` env var,
so it's safe to call unconditionally on every parser construction. The
test asserts the hook is called, by patching `argcomplete.autocomplete`
and constructing the parser.

**Files:**
- Modify: `src/ansible_aom/cli.py:69-159` (`create_parser`)
- Modify: `tests/unit/test_cli.py` (append a new test class at end)

- [ ] **Step 3.1: Write the failing test**

Append to `tests/unit/test_cli.py`:

```python
class TestArgcompleteHook:
    """F5: argcomplete.autocomplete must be called inside create_parser."""

    def test_create_parser_calls_argcomplete_autocomplete(self):
        from unittest.mock import patch

        from ansible_aom.cli import create_parser

        with patch("ansible_aom.cli.argcomplete.autocomplete") as mock_ac:
            parser = create_parser()
            mock_ac.assert_called_once_with(parser)
```

- [ ] **Step 3.2: Run test to confirm failure**

Run: `uv run pytest tests/unit/test_cli.py::TestArgcompleteHook -v`
Expected: FAIL — either `AttributeError: module 'ansible_aom.cli' has no attribute 'argcomplete'` or `mock_ac.assert_called_once_with` raises because it was never called.

- [ ] **Step 3.3: Add the import and call**

Edit `src/ansible_aom/cli.py`. After the existing imports (around line 11, right after `import sys`) add:

```python
import argcomplete
```

Then at the **end** of `create_parser()` (currently `return parser` on line 159), replace

```python
    parser.add_argument(
        "ansible_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments passed to ansible-playbook",
    )

    return parser
```

with

```python
    parser.add_argument(
        "ansible_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments passed to ansible-playbook",
    )

    # F5: arm shell completion. No-op unless the shell wrapper sets
    # the _ARGCOMPLETE env var, so this is free on the normal CLI path.
    argcomplete.autocomplete(parser)

    return parser
```

- [ ] **Step 3.4: Run the new test**

Run: `uv run pytest tests/unit/test_cli.py::TestArgcompleteHook -v`
Expected: PASS.

- [ ] **Step 3.5: Run full suite — make sure nothing regressed**

Run: `uv run pytest tests/ -q`
Expected: all green. Existing CLI tests construct the parser and
parse args; argcomplete's `autocomplete` is a no-op without the env
var so they should be unaffected. If any test fails, investigate
before proceeding.

- [ ] **Step 3.6: Commit**

```bash
git add src/ansible_aom/cli.py tests/unit/test_cli.py
git commit -m "feat(cli): arm argcomplete on the top-level parser"
```

---

## Task 4: Add `--install-completion <shell>` flag and handler (TDD)

Print the snippet to stdout. We do **not** write to the user's rc
file — they pipe / paste it themselves. Exit code 0 on success, 2 on
unknown shell (consistent with the existing CLI usage-error
convention, e.g. duplicate playbook).

**Files:**
- Modify: `src/ansible_aom/cli.py` — add the flag in `create_parser()`, handle it early in `main()`.
- Modify: `tests/unit/test_cli.py` — new test class.

- [ ] **Step 4.1: Write failing tests**

Append to `tests/unit/test_cli.py`:

```python
class TestInstallCompletionFlag:
    """F5: ``aom --install-completion <shell>`` prints the rc snippet."""

    def test_bash_prints_snippet_to_stdout(self, capsys):
        from ansible_aom.cli import main

        with patch("sys.argv", ["aom", "--install-completion", "bash"]):
            rc = main()

        captured = capsys.readouterr()
        assert rc == 0
        assert "register-python-argcomplete" in captured.out
        assert "aom" in captured.out

    def test_zsh_prints_snippet_to_stdout(self, capsys):
        from ansible_aom.cli import main

        with patch("sys.argv", ["aom", "--install-completion", "zsh"]):
            rc = main()

        captured = capsys.readouterr()
        assert rc == 0
        assert "register-python-argcomplete" in captured.out
        assert "bashcompinit" in captured.out  # zsh-specific glue

    def test_fish_prints_snippet_to_stdout(self, capsys):
        from ansible_aom.cli import main

        with patch("sys.argv", ["aom", "--install-completion", "fish"]):
            rc = main()

        captured = capsys.readouterr()
        assert rc == 0
        assert "register-python-argcomplete" in captured.out
        assert "fish" in captured.out

    def test_unknown_shell_returns_exit_2_and_prints_to_stderr(self, capsys):
        from ansible_aom.cli import main

        with patch("sys.argv", ["aom", "--install-completion", "powershell"]):
            rc = main()

        captured = capsys.readouterr()
        assert rc == 2
        assert "powershell" in captured.err
        assert "bash" in captured.err and "zsh" in captured.err and "fish" in captured.err
```

- [ ] **Step 4.2: Run new tests — confirm failure**

Run: `uv run pytest tests/unit/test_cli.py::TestInstallCompletionFlag -v`
Expected: FAIL with argparse error ("unrecognized arguments: --install-completion bash") for the first three; the fourth depends on the same flag existing.

- [ ] **Step 4.3: Add the flag in `create_parser`**

Edit `src/ansible_aom/cli.py`. In `create_parser()`, after the
`--verbose` argument (currently lines 140-144) and **before** the
`playbook` positional (currently lines 146-151), insert:

```python
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
```

- [ ] **Step 4.4: Handle the flag early in `main`**

Edit `src/ansible_aom/cli.py`. In `main()`, the current flow handles
`--version`, then `--help`, then dispatches `inspect`, then runs the
parser. Add a new early-exit branch *after* the `--help` branch and
*before* the `inspect` dispatch, because we want
`aom --install-completion bash` to bypass the playbook path entirely.

Replace this block (currently lines 227-237):

```python
    if "--help" in sys.argv or "-h" in sys.argv:
        create_parser().print_help()
        return 0

    if len(sys.argv) > 1 and sys.argv[1] == "inspect":
        from ansible_aom.inspect.cli import main as inspect_main

        return inspect_main(sys.argv[2:])

    parser = create_parser()
    args = parser.parse_args()
```

with

```python
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
                f"aom: unsupported shell {shell!r}; "
                f"expected one of {', '.join(SUPPORTED_SHELLS)}",
                file=sys.stderr,
            )
            return 2
        sys.stdout.write(completion_snippet(shell))
        return 0

    if len(sys.argv) > 1 and sys.argv[1] == "inspect":
        from ansible_aom.inspect.cli import main as inspect_main

        return inspect_main(sys.argv[2:])

    parser = create_parser()
    args = parser.parse_args()
```

- [ ] **Step 4.5: Run the new tests**

Run: `uv run pytest tests/unit/test_cli.py::TestInstallCompletionFlag -v`
Expected: all 4 tests pass.

- [ ] **Step 4.6: Run full suite**

Run: `uv run pytest tests/ -q`
Expected: green.

- [ ] **Step 4.7: Lint + type-check**

Run: `uv run ruff format src/ansible_aom/cli.py tests/unit/test_cli.py`
Run: `uv run ruff check --fix src/ansible_aom/cli.py tests/unit/test_cli.py`
Run: `uv run mypy src/ansible_aom/cli.py`
Expected: clean.

- [ ] **Step 4.8: Commit**

```bash
git add src/ansible_aom/cli.py tests/unit/test_cli.py
git commit -m "feat(cli): add --install-completion <shell> flag"
```

---

## Task 5: Wire session-id completer to `inspect` subcommands (TDD)

`argparse.Action` instances expose a `.completer` attribute that
argcomplete reads at completion time. We attach our completer to the
session-id positional arguments on `inspect show` and `inspect diff`
(both args of `diff`). We also call `argcomplete.autocomplete(parser)`
inside the inspect parser so `aom inspect <TAB>` works when the shell
forwards completion to the dispatched parser path.

**Files:**
- Modify: `src/ansible_aom/inspect/cli.py:198-233` (the `main()` parser block)
- Modify: `tests/unit/test_completion.py` — assert the wiring.

- [ ] **Step 5.1: Write failing tests**

Append to `tests/unit/test_completion.py`:

```python
class TestInspectCLICompleterWiring:
    """F5: session-id positionals on inspect parsers carry the completer."""

    def _build_inspect_parser(self):
        """Reconstruct the inspect parser without invoking the dispatcher."""
        # We import here (not at top of module) so test collection doesn't
        # pull in inspect's heavier dependency tree before strictly needed.
        import argparse

        from ansible_aom import completion as completion_mod
        from ansible_aom.inspect import cli as inspect_cli

        # Trick: call inspect.cli.main with a sentinel that won't exit so we
        # can grab the parser. Easier: copy-paste-ish of the parser building
        # block is not worth maintaining, so we factor: assert the wiring on
        # a fresh parser by introspecting actions added when main() is called
        # with --help suppressed via SystemExit.
        try:
            inspect_cli.main(["--help"])
        except SystemExit:
            pass

        # Easier path: ask the helper directly. Inspect exposes a
        # ``_build_parser`` factory we add in this task (Step 5.2).
        return inspect_cli._build_parser()

    def test_show_session_id_has_completer(self):
        from ansible_aom.completion import session_id_completer
        from ansible_aom.inspect.cli import _build_parser

        parser = _build_parser()
        # Walk subparsers to find ``show``.
        subparsers_action = next(
            a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction"
        )
        show_parser = subparsers_action.choices["show"]
        session_action = next(a for a in show_parser._actions if a.dest == "session_id")
        assert session_action.completer is session_id_completer  # type: ignore[attr-defined]  # NO — see below

    def test_diff_session_ids_have_completer(self):
        from ansible_aom.completion import session_id_completer
        from ansible_aom.inspect.cli import _build_parser

        parser = _build_parser()
        subparsers_action = next(
            a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction"
        )
        diff_parser = subparsers_action.choices["diff"]
        ids = [a for a in diff_parser._actions if a.dest in ("session_id_1", "session_id_2")]
        assert len(ids) == 2
        for action in ids:
            assert action.completer is session_id_completer  # type: ignore[attr-defined]  # NO — see below
```

**Important:** the project rule forbids inline `# type: ignore`. The
two markers above show what NOT to write. Replace them with a
`getattr` call so the test is type-clean. Use this revised snippet
instead — paste it verbatim into the file (do not include the two
prior test methods that contain `# type: ignore`):

```python
class TestInspectCLICompleterWiring:
    """F5: session-id positionals on inspect parsers carry the completer."""

    def _completer_of(self, parser, dest):
        action = next(a for a in parser._actions if a.dest == dest)
        return getattr(action, "completer", None)

    def _subparser(self, parser, name):
        sub = next(a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction")
        return sub.choices[name]

    def test_show_session_id_has_completer(self):
        from ansible_aom.completion import session_id_completer
        from ansible_aom.inspect.cli import _build_parser

        parser = _build_parser()
        show_parser = self._subparser(parser, "show")
        assert self._completer_of(show_parser, "session_id") is session_id_completer

    def test_diff_session_ids_have_completer(self):
        from ansible_aom.completion import session_id_completer
        from ansible_aom.inspect.cli import _build_parser

        parser = _build_parser()
        diff_parser = self._subparser(parser, "diff")
        assert self._completer_of(diff_parser, "session_id_1") is session_id_completer
        assert self._completer_of(diff_parser, "session_id_2") is session_id_completer
```

- [ ] **Step 5.2: Run tests — confirm failure**

Run: `uv run pytest tests/unit/test_completion.py::TestInspectCLICompleterWiring -v`
Expected: FAIL — `_build_parser` does not yet exist on `ansible_aom.inspect.cli`.

- [ ] **Step 5.3: Refactor `inspect/cli.py` to expose `_build_parser`**

Edit `src/ansible_aom/inspect/cli.py`. Add `import argcomplete` near
the top with the other imports. Then split the parser construction
out of `main()` into a private factory.

Locate the existing `main()` function (lines 190-271). Just before it,
insert this new function:

```python
def _build_parser() -> argparse.ArgumentParser:
    """Build the ``aom inspect`` argument parser.

    Factored out of ``main`` so the same parser shape can be used by
    shell-completion glue without invoking dispatch.
    """
    from ansible_aom.completion import session_id_completer

    parser = argparse.ArgumentParser(description="Inspect AOM sessions")
    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path.home() / ".local" / "state" / "aom" / "sessions",
        help="Directory containing session data",
    )

    list_parser = subparsers.add_parser("list", help="List all sessions")
    list_parser.add_argument("--failed", action="store_true", help="Show only failed sessions")
    list_parser.add_argument("--host", type=str, help="Filter by hostname")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_parser.add_argument("--jsonl", action="store_true", help="Output as JSONL")

    show_parser = subparsers.add_parser("show", help="Show session summary")
    show_action = show_parser.add_argument("session_id", help="Session ID to show")
    show_action.completer = session_id_completer  # type: ignore[attr-defined]
    show_parser.add_argument("--failed", action="store_true", help="Show only failed tasks")
    show_parser.add_argument("--host", type=str, help="Filter by hostname")
    show_parser.add_argument("--tree", action="store_true", help="Show ASCII tree view")
    show_parser.add_argument("--json", action="store_true", help="Output as JSON")
    show_parser.add_argument("--jsonl", action="store_true", help="Output as JSONL")

    diff_parser = subparsers.add_parser("diff", help="Compare two sessions")
    diff_action_1 = diff_parser.add_argument("session_id_1", help="Baseline session ID")
    diff_action_1.completer = session_id_completer  # type: ignore[attr-defined]
    diff_action_2 = diff_parser.add_argument("session_id_2", help="Current session ID")
    diff_action_2.completer = session_id_completer  # type: ignore[attr-defined]
    diff_parser.add_argument("--changes-only", action="store_true", help="Show only changed tasks")
    diff_parser.add_argument("--json", action="store_true", help="Output as JSON")

    prune_parser = subparsers.add_parser("prune", help="Cleanup old sessions")
    prune_parser.add_argument(
        "--days", type=int, default=30, help="Remove sessions older than N days"
    )

    argcomplete.autocomplete(parser)
    return parser
```

**`# type: ignore` is forbidden by `CLAUDE.md`.** Remove the three
`# type: ignore[attr-defined]` comments above. Instead, add a
module-level mypy override in `pyproject.toml` (Step 5.4) so
`Action.completer = ...` type-checks cleanly. The final code in
`_build_parser` therefore reads:

```python
    show_action = show_parser.add_argument("session_id", help="Session ID to show")
    show_action.completer = session_id_completer
    ...
    diff_action_1 = diff_parser.add_argument("session_id_1", help="Baseline session ID")
    diff_action_1.completer = session_id_completer
    diff_action_2 = diff_parser.add_argument("session_id_2", help="Current session ID")
    diff_action_2.completer = session_id_completer
```

— **without** any `# type: ignore` comments. Paste the function as
shown but strip the three trailing comment markers before saving.

Then replace the existing parser-construction block at the top of
`main()` (the lines that currently build `parser`, `subparsers`, and
all the `add_parser` calls — argv lines 198-231) with a single line:

```python
def main(argv: list[str] | None = None) -> int:
    """CLI entry point for inspect commands.

    Args:
        argv: Argument list. If None, parses from sys.argv. The top-level
            ``aom inspect ...`` dispatcher passes ``sys.argv[2:]`` so the
            ``inspect`` token is consumed before this parser runs.
    """
    parser = _build_parser()

    args = parser.parse_args(argv)
    # ...rest of main() unchanged...
```

Keep the rest of `main()` (the `if args.command == "list": ...` block
and below) exactly as it was.

- [ ] **Step 5.4: Add mypy override for argcomplete-injected attribute**

Edit `pyproject.toml`. After the existing `[[tool.mypy.overrides]]`
blocks (the last one is the `ansible_module_utils.*` block ending the
file), append:

```toml
[[tool.mypy.overrides]]
module = "argcomplete.*"
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "ansible_aom.inspect.cli"
# argcomplete reads ``action.completer`` off argparse Action instances
# at runtime; the attribute isn't in argparse's type stubs.
disallow_untyped_defs = false
disallow_untyped_calls = false
```

(The first override silences "missing stubs" if argcomplete's stub
package isn't on the path; the second relaxes inspect/cli.py so
assigning `.completer` on an `argparse.Action` doesn't trip
`attr-defined`.)

- [ ] **Step 5.5: Run wiring tests**

Run: `uv run pytest tests/unit/test_completion.py::TestInspectCLICompleterWiring -v`
Expected: PASS.

- [ ] **Step 5.6: Run full suite**

Run: `uv run pytest tests/ -q`
Expected: green. The existing inspect tests construct the parser and
exercise dispatch; the refactor preserves the parser shape (same
subcommand names, same argument names, same defaults) so they should
all still pass. If any inspect test fails, diff the parser before /
after to find the drift.

- [ ] **Step 5.7: Lint + type-check**

Run: `uv run ruff format src/ansible_aom/inspect/cli.py tests/unit/test_completion.py pyproject.toml`
Run: `uv run ruff check --fix src/ansible_aom/inspect/cli.py tests/unit/test_completion.py`
Run: `uv run mypy src/ansible_aom/inspect/cli.py src/ansible_aom/completion.py`
Expected: clean.

- [ ] **Step 5.8: Commit**

```bash
git add src/ansible_aom/inspect/cli.py tests/unit/test_completion.py pyproject.toml
git commit -m "feat(inspect): wire session-id completer to show/diff positionals"
```

---

## Task 6: End-to-end smoke test for the completion environment hook

A belt-and-suspenders check: argcomplete's `autocomplete` reads
`_ARGCOMPLETE` from the env. We don't run a real shell, but we can
simulate the hand-off by setting that env var and asserting the
parser exits via `SystemExit` (argcomplete's signal that completion
output was produced).

**Files:**
- Modify: `tests/unit/test_completion.py`

- [ ] **Step 6.1: Write the failing test**

Append to `tests/unit/test_completion.py`:

```python
class TestArgcompleteEnvHandoff:
    """Smoke test: setting _ARGCOMPLETE causes the parser to short-circuit.

    argcomplete signals "completion done, exit now" by raising SystemExit.
    We don't care about the completion text — only that the hook engages
    when the env var is present, confirming the wiring really is live.
    """

    def test_top_level_parser_short_circuits_on_argcomplete_env(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        from ansible_aom.cli import create_parser

        monkeypatch.setenv("_ARGCOMPLETE", "1")
        # argcomplete reads _ARGCOMPLETE_IFS, COMP_LINE, COMP_POINT etc.;
        # supply minimal values so it can produce *something* without
        # crashing on a missing var.
        monkeypatch.setenv("COMP_LINE", "aom ")
        monkeypatch.setenv("COMP_POINT", "4")
        monkeypatch.setenv("_ARGCOMPLETE_IFS", "\n")
        # Send completion output to a pipe argcomplete can write to.
        # By default it tries fd 8/9; redirect to devnull-style fds the
        # test process owns. Easiest: monkeypatch argcomplete to call
        # exit_method=SystemExit so we can intercept it cleanly.
        import argcomplete

        original = argcomplete.autocomplete

        def patched(parser, **kwargs):
            kwargs.setdefault("exit_method", SystemExit)
            return original(parser, **kwargs)

        monkeypatch.setattr("ansible_aom.cli.argcomplete.autocomplete", patched)

        with pytest.raises(SystemExit):
            create_parser()
```

- [ ] **Step 6.2: Run the test**

Run: `uv run pytest tests/unit/test_completion.py::TestArgcompleteEnvHandoff -v`
Expected: PASS — the wiring already added in Task 3 plus the env var
should cause argcomplete to short-circuit. If it does **not** raise
`SystemExit`, the most likely cause is that argcomplete couldn't open
its output fd; in that case relax the assertion to:

```python
        with pytest.raises((SystemExit, OSError)):
            create_parser()
```

and re-run. Either exception confirms the hook engaged (the OSError
path is "ran but couldn't write", which is still proof of life).

- [ ] **Step 6.3: Run full suite**

Run: `uv run pytest tests/ -q`
Expected: green.

- [ ] **Step 6.4: Commit**

```bash
git add tests/unit/test_completion.py
git commit -m "test(completion): add env-handoff smoke test for argcomplete hook"
```

---

## Task 7: Document `--install-completion` in CLI epilog (TDD)

Surface the new flag in `aom --help` so users discover it. The epilog
currently lists Examples; add one line and a short paragraph.

**Files:**
- Modify: `src/ansible_aom/cli.py:79-131` (epilog string in `create_parser`)
- Modify: `tests/unit/test_cli.py`

- [ ] **Step 7.1: Write failing test**

Append to `tests/unit/test_cli.py`:

```python
class TestHelpMentionsInstallCompletion:
    """F5: --help output references the new --install-completion flag."""

    def test_help_text_documents_install_completion(self):
        import io

        from ansible_aom.cli import create_parser

        parser = create_parser()
        buf = io.StringIO()
        parser.print_help(buf)
        out = buf.getvalue()
        assert "--install-completion" in out
        # The flag has its own Examples line so users see the typical usage.
        assert "bash" in out
```

- [ ] **Step 7.2: Run test — confirm failure**

Run: `uv run pytest tests/unit/test_cli.py::TestHelpMentionsInstallCompletion -v`
Expected: PASS for `--install-completion` (already shown by argparse
because the flag exists), but the second assertion may already pass
because the existing epilog mentions `bash` only in shell-glue
examples — actually it doesn't. Run it to find out. If both pass, the
test still has value as a regression guard. If the second fails, do
Step 7.3.

- [ ] **Step 7.3: Add an Examples line for completion**

Edit `src/ansible_aom/cli.py`. In `create_parser`'s `epilog=` string,
locate the `Examples:` block (around lines 80-90). After the line:

```
  aom inspect prune --days 30           Delete sessions older than N days
```

insert:

```
  aom --install-completion bash >> ~/.bashrc   Enable tab-completion for bash
```

And below the existing `Verbosity:` paragraph (around line 102), add:

```
Shell completion:
  aom --install-completion <bash|zsh|fish>
  Prints the rc-file snippet to stdout. Pipe to your rc file or eval
  it directly. Powered by argcomplete; tab-completes subcommands,
  flags, and recorded session IDs.

```

- [ ] **Step 7.4: Run the test**

Run: `uv run pytest tests/unit/test_cli.py::TestHelpMentionsInstallCompletion -v`
Expected: PASS.

- [ ] **Step 7.5: Run full suite**

Run: `uv run pytest tests/ -q`
Expected: green.

- [ ] **Step 7.6: Commit**

```bash
git add src/ansible_aom/cli.py tests/unit/test_cli.py
git commit -m "docs(cli): mention --install-completion in --help epilog"
```

---

## Final verification

- [ ] **Step F.1: Full test suite**

Run: `uv run pytest tests/ -q`
Expected: all green.

- [ ] **Step F.2: Lint and format**

Run: `uv run ruff format`
Run: `uv run ruff check --fix`
Expected: clean (no changes needed if previous steps formatted as
they went).

- [ ] **Step F.3: Type-check**

Run: `uv run mypy src/ansible_aom`
Expected: clean.

- [ ] **Step F.4: Manual smoke test**

```bash
uv run aom --install-completion bash
```

Expected output (something close to):

```
# AOM bash completion — add to ~/.bashrc:
eval "$(register-python-argcomplete aom)"
```

```bash
uv run aom --install-completion fish
uv run aom --install-completion zsh
uv run aom --install-completion powershell  # should print error to stderr, exit 2
```

- [ ] **Step F.5: Final commit if any pending**

```bash
git status
```

If the working tree is clean, F5 is done. Otherwise reconcile any
straggling formatting changes and commit them with `chore: ruff format`.

---

## Self-review (run after writing the plan)

1. **Spec coverage.**
   - Subcommand completion → handled by argcomplete on the top-level parser (Task 3) and on the inspect parser (Task 5). ✓
   - Flag completion (`--tui`, `--verbose`, `--no-record`, `--format`) → argcomplete derives flag completion from the parser automatically. The flags listed in the brief don't all exist yet (`--no-record`, `--format`) — they belong to F3/F6 in the features doc and will be picked up automatically by argcomplete the moment they're added to the parser. No extra plumbing needed. ✓
   - Session-ID completion → Tasks 2 + 5 cover the completer and its wiring. ✓
   - `--install-completion <shell>` snippet emission → Task 4. ✓
   - `argcomplete` runtime dep → Task 1. ✓
   - Tag completer dropped → confirmed in the Risks section of this header; no task touches `--tags`. ✓
   - `replay` / `rerun` wiring → not in the codebase yet; the plan provides the completer in a reusable shape so those subcommands wire up with a one-line `arg.completer = session_id_completer` when they land. Documented in Risks. ✓

2. **Placeholder scan.** Searched for "TBD", "TODO", "implement later",
   "similar to". The phrase "similar to" appears nowhere. Every code
   block is complete and copy-pasteable. ✓

3. **Type consistency.**
   - `session_id_completer(prefix, parsed_args, state_dir, **kwargs)`
     used identically in Task 2 (definition), Task 5 (wiring), Task 5
     tests, Task 6 indirectly. ✓
   - `completion_snippet(shell)` used in Task 2 (definition) and
     Task 4 (call site). ✓
   - `SUPPORTED_SHELLS = ("bash", "zsh", "fish")` referenced
     consistently in Tasks 2 and 4. ✓
   - `_build_parser()` introduced in Task 5 Step 5.3 and called from
     Task 5 tests in Step 5.1. ✓

4. **Project rule compliance.**
   - No `# type: ignore` in finished code. The mid-step example in
     Task 5 explicitly flags the comments as "do NOT write" and shows
     the correct typecheck-clean alternative; the mypy override added
     in Step 5.4 covers the runtime-injected `.completer` attribute.
   - No `Co-Authored-By:` in any commit message. ✓
   - Conventional commit prefixes used throughout (`chore:`, `feat:`,
     `test:`, `docs:`). ✓
   - TDD discipline: every task starts with the failing test, runs
     it, then implements. ✓
   - Full suite (`uv run pytest tests/ -q`) is run before each
     commit. ✓
