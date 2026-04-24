"""Log streaming for compact mode.

Log streaming + non-TTY fallback.
See SPECIFICATION.md Section 4.3 for non-TTY behavior.
"""

from collections import deque

MIN_LOG_LINES = 1000


class LogStreamer:
    """Memory-bounded circular buffer for log lines. NOT thread-safe."""

    def __init__(self, max_lines: int = 50000) -> None:
        if max_lines < MIN_LOG_LINES:
            raise ValueError(f"max_lines must be >= {MIN_LOG_LINES}, got {max_lines}")
        self._max_lines = max_lines
        self._lines: deque[str] = deque(maxlen=max_lines)

    def append(self, line: str) -> None:
        self._lines.append(line)

    def get_lines(self, offset: int = 0, limit: int | None = None) -> list[str]:
        if offset < 0:
            raise ValueError(f"offset must be >= 0, got {offset}")
        if offset >= len(self._lines):
            return []
        all_lines = list(self._lines)
        return all_lines[offset:] if limit is None else all_lines[offset : offset + limit]

    def clear(self) -> None:
        self._lines.clear()
