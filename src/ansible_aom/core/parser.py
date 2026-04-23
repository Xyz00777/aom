"""PTY stream parser for AOM.

This module implements the 3-phase parser for ansible-playbook PTY output.
See SPECIFICATION.md Section 5.6 for phase details.

Phases:
1. PRE_RUN_PROMPTS: Password prompts before execution
2. EXECUTION: JSONL events with interleaved plaintext
3. POST_RUN_RECAP: Final PLAY RECAP output
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Callable

from ansible_aom.core.models import RoleGroupDefinition, WarningEntry, WarningType

logger = logging.getLogger(__name__)


class StreamPhase(Enum):
    """PTY stream parsing phases."""

    PRE_RUN_PROMPTS = auto()
    EXECUTION = auto()
    POST_RUN_RECAP = auto()


class JsonLineStream:
    """Parses JSON lines from a mixed JSON/plaintext stream."""

    def __init__(self) -> None:
        self._non_json_handler: Callable[[str], None] | None = None

    def feed_line(self, line: str) -> list[dict]:
        """Parse a line and return zero or more JSON events.

        Returns empty list for:
        - Empty lines
        - Invalid JSON
        - JSON without _event field
        """
        line = line.strip()
        if not line:
            return []

        if not line.startswith("{"):
            if self._non_json_handler:
                self._non_json_handler(line)
            return []

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON line: %s", line[:100])
            if self._non_json_handler:
                self._non_json_handler(line)
            return []

        if "_event" not in data:
            logger.warning("JSON missing _event field: %s", line[:100])
            return []

        return [data]

    def set_non_json_handler(self, handler: Callable[[str], None]) -> None:
        """Set handler for non-JSON lines."""
        self._non_json_handler = handler


class PtyStreamParser:
    """3-phase parser for ansible-playbook PTY output."""

    WARNING_PATTERNS: list[str] = [
        r"^\[WARNING\]:",
        r"^\[DEPRECATION WARNING\]:",
        r"^\[DEPRECATED\]:",
    ]

    PASSWORD_PATTERNS: list[str] = [
        r"Vault password: ",
        r"Vault password \([^)]+\): ",
        r"SSH password: ",
        r"BECOME password: ",
        r"BECOME password\[defaults to SSH password\]: ",
        r"New Vault password: ",
        r"Confirm New Vault password: ",
    ]

    RECAP_PATTERN: re.Pattern[str] = re.compile(r"^PLAY RECAP \*{5,}")

    def __init__(self) -> None:
        self.phase = StreamPhase.PRE_RUN_PROMPTS
        self._pending_password_prompt: str | None = None
        self._in_recap: bool = False
        self._recap_lines: list[str] = []
        self._warnings: list[WarningEntry] = []
        self._plaintext_lines: list[str] = []
        self._current_timestamp: datetime | None = None

    def feed_line(self, line: str) -> list[dict]:
        """Parse a line and return zero or more events."""
        line_stripped = line.rstrip("\n\r")

        if self.phase == StreamPhase.PRE_RUN_PROMPTS:
            self._handle_plaintext(line_stripped)

            if self._is_jsonl_start_event(line_stripped):
                self.phase = StreamPhase.EXECUTION
                return self._parse_and_return(line_stripped)

            for pattern in self.PASSWORD_PATTERNS:
                if re.search(pattern, line_stripped):
                    self._pending_password_prompt = line_stripped
                    return []

            return []

        if self.phase == StreamPhase.EXECUTION:
            if self._is_jsonl_stats_event(line_stripped):
                self.phase = StreamPhase.POST_RUN_RECAP
                self._in_recap = True
                return self._parse_and_return(line_stripped)

            if self._is_json(line_stripped):
                return self._parse_and_return(line_stripped)

            if self.RECAP_PATTERN.match(line_stripped):
                self.phase = StreamPhase.POST_RUN_RECAP
                self._in_recap = True
                return []

            self._handle_plaintext(line_stripped)
            return []

        if self.phase == StreamPhase.POST_RUN_RECAP:
            self._recap_lines.append(line_stripped)
            return []

        return []

    def _parse_and_return(self, line: str) -> list[dict]:
        """Parse JSON line and return events."""
        try:
            data = json.loads(line)
            if "_event" in data:
                return [data]
        except json.JSONDecodeError:
            pass
        return []

    def _handle_plaintext(self, line: str) -> None:
        """Classify and handle non-JSON lines from PTY stream."""
        for pattern in self.WARNING_PATTERNS:
            if re.match(pattern, line):
                warning_type = WarningType.WARNING
                if "DEPRECATION" in pattern:
                    warning_type = WarningType.DEPRECATION
                elif "DEPRECATED" in pattern:
                    warning_type = WarningType.DEPRECATION

                self._warnings.append(
                    WarningEntry(
                        type=warning_type,
                        message=line,
                        timestamp=datetime.now(),
                    )
                )
                return

        self._plaintext_lines.append(line)

    def _is_jsonl_start_event(self, line: str) -> bool:
        """Check if line is a v2_playbook_on_start event."""
        if not line.startswith("{"):
            return False
        try:
            data = json.loads(line)
            return bool(data.get("_event") == "v2_playbook_on_start")
        except json.JSONDecodeError:
            return False

    def _is_jsonl_stats_event(self, line: str) -> bool:
        """Check if line is a v2_playbook_on_stats event."""
        if not line.startswith("{"):
            return False
        try:
            data = json.loads(line)
            return bool(data.get("_event") == "v2_playbook_on_stats")
        except json.JSONDecodeError:
            return False

    def _is_json(self, line: str) -> bool:
        """Check if line is valid JSON."""
        if not line.startswith("{"):
            return False
        try:
            json.loads(line)
            return True
        except json.JSONDecodeError:
            return False

    def _parse_json(self, line: str) -> dict:
        """Parse a JSON line into a dict."""
        result = json.loads(line)
        assert isinstance(result, dict), "Expected JSON object"
        return result

    def _handle_recap_output(self, line: str) -> None:
        """Handle PLAY RECAP output lines."""
        self._recap_lines.append(line)

    @property
    def warnings(self) -> list[WarningEntry]:
        return self._warnings

    @property
    def recap_lines(self) -> list[str]:
        return self._recap_lines

    @property
    def plaintext_lines(self) -> list[str]:
        return self._plaintext_lines

    @property
    def pending_password_prompt(self) -> str | None:
        return self._pending_password_prompt

    def clear_password_prompt(self) -> None:
        """Clear pending password prompt after handling."""
        self._pending_password_prompt = None


@dataclass
class PreParseResult:
    """Result from pre-parse phase (--list-tasks + --list-hosts)."""

    plays: list[dict]
    play_hosts: list[dict]


def parse_list_hosts_output(output: str) -> list[dict]:
    """Parse --list-hosts output into structured data.

    Returns list of dicts with keys:
    - play_number: int
    - name: str
    - hosts_pattern: list[str]
    - hosts: list[str]
    """
    result: list[dict] = []
    current_play: dict | None = None

    for line in output.splitlines():
        if not line.strip():
            continue

        if line.startswith("playbook:"):
            continue

        play_match = re.match(r"\s{2}play #(\d+)\s+\(([^)]+)\):\s+(.+?)\tTAGS:", line)
        if play_match:
            if current_play:
                result.append(current_play)
            play_number = int(play_match.group(1))
            hosts_pattern = play_match.group(2)
            name = play_match.group(3)
            current_play = {
                "play_number": play_number,
                "name": name,
                "hosts_pattern": [p.strip() for p in hosts_pattern.split(",")],
                "hosts": [],
            }
            continue

        if current_play is not None:
            if re.match(r"\s{4}hosts \(\d+\):", line):
                continue
            if re.match(r"\s{4}pattern:", line):
                continue
            if re.match(r"\s{4}tasks:", line):
                continue

            host_match = re.match(r"\s{6}(.+)", line)
            if host_match:
                hostname = host_match.group(1).strip()
                if hostname and hostname not in current_play["hosts"]:
                    current_play["hosts"].append(hostname)

    if current_play:
        result.append(current_play)

    return result


def parse_list_tasks_output(output: str) -> list[dict]:
    """Parse --list-tasks output into structured data.

    Returns list of dicts with keys:
    - play_number: int
    - name: str
    - tasks: list[dict] with keys: name, role, tags
    """
    result: list[dict] = []
    current_play: dict | None = None

    for line in output.splitlines():
        if not line.strip():
            continue

        if line.startswith("playbook:"):
            continue

        play_match = re.match(r"\s{2}play #(\d+)\s*\(([^)]+)\):\s+(.+?)\tTAGS:", line)
        if play_match:
            if current_play:
                result.append(current_play)
            play_number = int(play_match.group(1))
            name = play_match.group(3)
            current_play = {
                "play_number": play_number,
                "name": name,
                "tasks": [],
            }
            continue

        if current_play is not None:
            task_match = re.match(r"\s{4}(.+?)\tTAGS:\s*(\[.*\])", line)
            if task_match:
                task_name = task_match.group(1).strip()
                tags_str = task_match.group(2)

                role = None
                if " : " in task_name:
                    role, task_name = task_name.split(" : ", 1)
                    role = role.strip()

                tags: list[str] = []
                if tags_str and tags_str != "[]":
                    tags = [
                        t.strip().strip("'\"") for t in tags_str.strip("[]").split(",") if t.strip()
                    ]

                current_play["tasks"].append(
                    {
                        "name": task_name,
                        "role": role,
                        "tags": tags,
                    }
                )

    if current_play:
        result.append(current_play)

    return result


def group_roles(tasks: list) -> list:
    """Group consecutive same-role tasks (5 or more) into RoleGroupDefinition.

    Args:
        tasks: List of TaskDefinition objects

    Returns:
        List of TaskDefinition or RoleGroupDefinition objects
    """
    if not tasks:
        return []

    result: list = []
    current_role: str | None = None
    current_group: list = []

    for task in tasks:
        task_role = getattr(task, "role", None)

        if task_role is None:
            if len(current_group) >= 5:
                assert current_role is not None, "role should not be None for grouped tasks"
                result.append(RoleGroupDefinition(role=current_role, tasks=current_group))
            else:
                result.extend(current_group)
            current_group = []
            current_role = None
            result.append(task)
        elif current_role == task_role:
            current_group.append(task)
        else:
            if len(current_group) >= 5:
                assert current_role is not None, "role should not be None for grouped tasks"
                result.append(RoleGroupDefinition(role=current_role, tasks=current_group))
            else:
                result.extend(current_group)
            current_group = [task]
            current_role = task_role

    if len(current_group) >= 5:
        assert current_role is not None, "role should not be None for grouped tasks"
        result.append(RoleGroupDefinition(role=current_role, tasks=current_group))
    else:
        result.extend(current_group)

    return result
