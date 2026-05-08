## 2026-04-24 Potential Issues

1. TUI widgets inheriting Textual classes need Textual installed and importable
2. Rich Live display needs proper context manager lifecycle in compact/renderer.py
3. Signal handling in compact mode needs careful subprocess management
4. Password pass-through needs pexpect mocking in tests
5. Some test functions use `pass` placeholder for complex integration tests (signal handling, non-TTY)
6. tui/app.py needs to satisfy Renderer Protocol - currently raises NotImplementedError on all methods