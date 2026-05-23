## 2026-04-24 Potential Issues (all resolved as of 2026-05-11)

1. TUI widgets inheriting Textual classes need Textual installed and importable
   → **Resolved** — Textual ≥0.60 in pyproject.toml dependencies.
2. Rich Live display needs proper context manager lifecycle in compact/renderer.py
   → **Resolved** — replaced with direct ANSI cursor positioning (2026-05-08).
3. Signal handling in compact mode needs careful subprocess management
   → **Resolved** — runner.py handles KeyboardInterrupt + SIGINT via pexpect
     `sendintr` + `close(force=True)` (2026-05-10).
4. Password pass-through needs pexpect mocking in tests
   → **Resolved** — TC-143 through TC-148 fully covered in
     `tests/compact/test_password.py` (2026-05-08).
5. Some test functions use `pass` placeholder for complex integration tests
   → **Resolved** — all stubs replaced with real implementations.
6. tui/app.py needs to satisfy Renderer Protocol
   → **Resolved** — AOMApp implements full Renderer Protocol + worker-driven
     playbook execution (2026-05-11).

## 2026-05-23 Open issues

7. **Fallback host leaves default to Status.RUNNING** — when a task finishes
   but `runtime.hosts` is empty (implicit tasks like `meta: flush_handlers`),
   the fallback path creates host leaves with running spinners instead of the
   final status. Root cause: ansible doesn't emit `v2_runner_on_ok` for
   implicit tasks.
8. **Push blocked** — remote `git.eisen5.eu:2222` connection refused.
   7 unpushed commits on `feat/nom-compact-renderer`.
