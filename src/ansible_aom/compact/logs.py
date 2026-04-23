"""Log streaming for compact mode.

Log streaming + non-TTY fallback.
See SPECIFICATION.md Section 4.3 for non-TTY behavior.

TDD: This file contains STUB implementations only. Tests come first.
"""


class LogStreamer:
    """Manages log output in compact mode."""

    def __init__(self, max_lines: int = 50000) -> None:
        self._max_lines = max_lines

    def append(self, line: str) -> None:
        raise NotImplementedError("append - tests first")

    def get_lines(self) -> list[str]:
        raise NotImplementedError("get_lines - tests first")

    def clear(self) -> None:
        raise NotImplementedError("clear - tests first")
