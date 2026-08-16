"""PTY stream parser for AOM.

This module implements the 3-phase parser for ansible-playbook PTY output.
See SPECIFICATION.md Section 5.6 for phase details.

Phases:
1. PRE_RUN_PROMPTS: Password prompts before execution
2. EXECUTION: JSONL events with interleaved plaintext
3. POST_RUN_RECAP: Final PLAY RECAP output
"""

import json as stdlib_json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, cast

import orjson

from ansible_aom.core.event_types import JsonlEvent
from ansible_aom.core.models import (
    IncludeCacheEntry,
    PlayDefinition,
    RoleGroupDefinition,
    WarningEntry,
    WarningType,
)
from ansible_aom.core.state_machine import MAX_LOG_LINES
from ansible_aom.core.stderr_classifier import classify

logger = logging.getLogger(__name__)

# CSI SGR (Select Graphic Rendition) sequences — what colour codes look
# like in raw terminal output. Strip these before pattern-matching log
# lines so warnings whose [WARNING]: prefix is wrapped in colour escapes
# still anchor against the WARNING_PATTERNS regexes.
_ANSI_SGR_RE = re.compile(r"\x1b\[[0-9;]*m")

# A leading foreground-magenta SGR (``\x1b[1;35m`` bright / ``\x1b[0;35m`` or
# ``\x1b[35m`` plain). ansible-core colours ``[WARNING]`` bright purple and
# ``[DEPRECATION WARNING]`` purple, and hard-wraps them to the terminal width
# so continuation lines arrive as magenta body text with no ``[WARNING]: ``
# prefix. The colour is the only signal that ties such a line back to its
# warning — see ``_handle_plaintext``.
_MAGENTA_SGR_RE = re.compile(r"^\x1b\[(?:\d+;)*35m")


def _has_surrogate_codepoint(s: str) -> bool:
    """True if ``s`` contains any surrogate codepoint (U+D800..U+DFFF).

    R6: pexpect's ``codec_errors="surrogateescape"`` decodes invalid UTF-8
    bytes into lone-surrogate codepoints so the original bytes round-trip
    through ``str`` losslessly. ``orjson`` rejects those strings as
    "surrogates not allowed", so the parser falls back to stdlib
    ``json.loads`` (which preserves them) only when needed.
    """
    for ch in s:
        if 0xD800 <= ord(ch) <= 0xDFFF:
            return True
    return False


def _safe_loads(line: str) -> Any:
    """Parse one JSONL line, picking orjson or stdlib json by content.

    R6: orjson is faster but rejects any string containing surrogate
    codepoints — which now happens whenever pexpect surfaces invalid
    UTF-8 from the PTY stream. stdlib ``json.loads`` accepts surrogates
    natively and round-trips them via ``\\uXXXX`` escapes, so the
    original byte sequence is preserved through ``record_event``.
    """
    if _has_surrogate_codepoint(line):
        return stdlib_json.loads(line)
    return orjson.loads(line)


_RETRYING_RE = re.compile(
    r"FAILED\s*-\s*RETRYING:\s*(?:\[(?P<host1>[^\]]+)\]|(?P<host2>[^:]+)):\s*(?P<task>.*?)\s*\((?P<left>\d+)\s+retries\s+left\)",
    re.IGNORECASE,
)
_ASYNC_POLL_RE = re.compile(
    r"ASYNC\s+POLL\s+on\s+(?P<host>[^:]+):\s*jid=(?P<jid>\S+)",
    re.IGNORECASE,
)


class StreamPhase(Enum):
    """PTY stream parsing phases."""

    PRE_RUN_PROMPTS = auto()
    EXECUTION = auto()
    POST_RUN_RECAP = auto()


class JsonLineStream:
    """Parses JSON lines from a mixed JSON/plaintext stream.

    Pexpect can split a JSONL event across two reads on a slow link or a
    very long ``msg`` payload. To avoid dropping both halves, a partial
    line that looks like JSON (starts with ``{`` but fails to parse) is
    stashed in ``_carry`` and prepended to the next ``feed_line`` input.
    The carry is hard-capped at ``_CARRY_LIMIT`` bytes — past that we
    assume the stream is wedged and drop rather than grow without bound.
    """

    # 1 MB. Real ansible events are usually <10 KB; a single event larger
    # than this is almost certainly a bug or a pathological host output.
    _CARRY_LIMIT = 1_000_000

    def __init__(self) -> None:
        self._non_json_handler: Callable[[str], None] | None = None
        self._carry: str = ""

    def feed_line(self, line: str) -> list[JsonlEvent]:
        """Parse a line and return zero or more JSON events.

        Returns empty list for:
        - Empty lines
        - Invalid JSON (stored as carry if line started with ``{``)
        - JSON without _event field
        """
        # Stash the raw incoming chunk so we can fall back to it if the
        # carry-prepended view turns out to be garbage that would
        # otherwise swallow this line's event.
        raw = line
        # Prepend any pending partial from a previous call so a JSONL
        # event split across two reads is rejoined.
        if self._carry:
            line = self._carry + line
            self._carry = ""

        line = line.strip()
        if not line:
            return []

        if not line.startswith("{"):
            if self._non_json_handler:
                self._non_json_handler(line)
            return []

        try:
            data = _safe_loads(line)
        except ValueError:
            # The carry-prepended view failed. If the bare new chunk
            # parses cleanly on its own as a JSON object, the carry
            # was garbage masquerading as a split-event head — drop
            # the carry and process the bare chunk.
            raw_stripped = raw.strip()
            if raw_stripped != line and raw_stripped.startswith("{"):
                try:
                    data = _safe_loads(raw_stripped)
                except ValueError:
                    data = None
                if isinstance(data, dict):
                    if "_event" not in data:
                        logger.warning("JSON missing _event field: %s", raw_stripped[:100])
                        return []
                    return [cast(JsonlEvent, data)]
            # Stash as carry if there's room, otherwise drop. Without
            # the cap a runaway/garbage stream would grow ``_carry``
            # without bound.
            if len(line) <= self._CARRY_LIMIT:
                self._carry = line
                return []
            logger.warning("Invalid JSON line (carry overflow, dropped): %s", line[:100])
            if self._non_json_handler:
                self._non_json_handler(line)
            return []

        if not isinstance(data, dict) or "_event" not in data:
            logger.warning("JSON missing _event field: %s", line[:100])
            return []

        return [cast(JsonlEvent, data)]

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
        r"\[sudo\] password for [^:\n]+: ",
        r"Password for [^:\n]+: ",
        r"Password: ",
    ]

    RECAP_PATTERN: re.Pattern[str] = re.compile(r"^PLAY RECAP \*{5,}")

    def __init__(self) -> None:
        self.phase = StreamPhase.PRE_RUN_PROMPTS
        self._pending_password_prompt: str | None = None
        self._in_recap: bool = False
        self._recap_lines: list[str] = []
        self._warnings: list[WarningEntry] = []
        # The warning currently being assembled from wrapped continuation
        # lines. None between warning blocks. Set when a ``[WARNING]``/
        # ``[DEPRECATION WARNING]`` first line (or an orphan magenta line)
        # arrives; cleared by any non-magenta plaintext line, a blank line,
        # or a consumed JSON event (see ``_parse_and_return``).
        self._current_warning: WarningEntry | None = None
        self._plaintext_lines: list[str] = []
        # True when the most recent classified output line was plaintext;
        # flipped False as soon as a JSONL event is consumed. Lets the
        # runner's TIMEOUT prompt heuristic reject a stale plaintext line
        # (an early ``?`` banner) that is no longer the child's latest
        # output. See ``latest_output_is_plaintext``.
        self._plaintext_is_latest_output: bool = False
        self._current_timestamp: datetime | None = None
        # Connection tracking: host -> ordered list of active connection_ids.
        # Populated by aom_connection_acquired / aom_connection_released events
        # flowing through feed_line. Used by _handle_plaintext to attach the
        # most-recent connection_id and determine attribution_confidence.
        self._active_connections: dict[str, list[str]] = {}

    def feed_line(self, line: str) -> list[JsonlEvent]:
        """Parse a line and return zero or more events."""
        line_stripped = line.rstrip("\n\r")

        if self.phase == StreamPhase.PRE_RUN_PROMPTS:
            events = self._handle_plaintext(line_stripped)

            if self._is_jsonl_start_event(line_stripped):
                self.phase = StreamPhase.EXECUTION
                return self._parse_and_return(line_stripped)

            for pattern in self.PASSWORD_PATTERNS:
                if re.search(pattern, line_stripped):
                    self._pending_password_prompt = line_stripped
                    return []

            # Lines starting with { that aren't a start event are malformed
            # JSON (e.g. truncated carry). Return empty — not stderr.
            if line_stripped.startswith("{"):
                return []

            return events

        if self.phase == StreamPhase.EXECUTION:
            if self._is_jsonl_stats_event(line_stripped):
                self.phase = StreamPhase.POST_RUN_RECAP
                self._in_recap = True
                return self._parse_and_return(line_stripped)

            if self._is_json(line_stripped):
                parsed = self._parse_and_return(line_stripped)
                if parsed:
                    self._handle_connection_event(parsed[0])
                return parsed

            if self.RECAP_PATTERN.match(line_stripped):
                self.phase = StreamPhase.POST_RUN_RECAP
                self._in_recap = True
                return []

            # Lines starting with { that failed _is_json are malformed JSON
            # (e.g. truncated carry). Return empty — they are not stderr.
            if line_stripped.startswith("{"):
                return []

            return self._handle_plaintext(line_stripped)

        if self.phase == StreamPhase.POST_RUN_RECAP:
            self._recap_lines.append(line_stripped)
            # R13: cap _recap_lines at MAX_LOG_LINES so a verbose
            # ``PLAY RECAP`` (e.g. -v with hundreds of host stats per
            # line × thousands of hosts) can't grow the list without
            # bound. Mirror the R2 plaintext_lines pattern — drop
            # oldest first so the most-recent recap tail stays
            # available for completion-time display.
            if len(self._recap_lines) > MAX_LOG_LINES:
                del self._recap_lines[: len(self._recap_lines) - MAX_LOG_LINES]
            return []

        return []

    def _parse_and_return(self, line: str) -> list[JsonlEvent]:
        """Parse JSON line and return events."""
        try:
            data = _safe_loads(line)
            if isinstance(data, dict) and "_event" in data:
                # A JSONL event is the child's latest output — invalidate
                # any prior plaintext line as a prompt candidate and close
                # any open multi-line warning block so a later magenta line
                # can't fold into a warning from before this event.
                self._plaintext_is_latest_output = False
                self._current_warning = None
                return [cast(JsonlEvent, data)]
        except ValueError:
            pass
        return []

    def _handle_plaintext(self, line: str) -> list[JsonlEvent]:
        """Classify and handle non-JSON lines from PTY stream.

        Real ansible-playbook output is colorised — warnings come through
        wrapped in SGR escape sequences (e.g. ``\\x1b[1;35m[WARNING]:``).
        Strip them before pattern-matching so the WARNING_PATTERNS regexes
        (anchored at line start) still match, and store the stripped form
        so downstream UI doesn't have to re-strip.

        Returns:
            A list containing a synthetic ``aom_stderr_line`` event for
            non-warning plaintext lines, or an empty list for warnings
            (which are handled via the existing ``drain_warnings`` path).
        """
        clean = _ANSI_SGR_RE.sub("", line)
        # Empty or whitespace-only lines are not stderr — they also close any
        # open multi-line warning block.
        if not clean or not clean.strip():
            self._current_warning = None
            return []

        for pattern in self.WARNING_PATTERNS:
            if re.match(pattern, clean):
                warning_type = WarningType.WARNING
                if "DEPRECATION" in pattern:
                    warning_type = WarningType.DEPRECATION
                elif "DEPRECATED" in pattern:
                    warning_type = WarningType.DEPRECATION

                entry = WarningEntry(
                    type=warning_type,
                    message=clean,
                    timestamp=datetime.now(),
                )
                self._warnings.append(entry)
                self._current_warning = entry
                return []

        # ansible hard-wraps warnings to the terminal width and colours the
        # whole block magenta; continuation lines carry no ``[WARNING]: ``
        # prefix, only the colour. Fold a magenta, prefix-less line into the
        # open warning block — or, if none is open, record it as its own
        # warning (colour-based classification) — so it never becomes a
        # spurious ``source='unknown'`` aom_stderr_line event.
        if _MAGENTA_SGR_RE.match(line):
            if self._current_warning is not None:
                self._current_warning.message = (
                    self._current_warning.message.rstrip() + " " + clean.strip()
                )
            else:
                entry = WarningEntry(
                    type=WarningType.WARNING,
                    message=clean,
                    timestamp=datetime.now(),
                )
                self._warnings.append(entry)
                self._current_warning = entry
            return []

        # ansible-core 2.20 deprecation blocks emitted WITHOUT SGR codes
        # (e.g. under the mitogen strategy, where workers write from a
        # non-TTY context) arrive as plaintext: the header line, then the
        # source-context and help-text continuation lines. While a
        # *deprecation* block is open, fold an uncolored plaintext line
        # into it instead of closing the block — otherwise each
        # continuation becomes a spurious ``source='unknown'``
        # aom_stderr_line event. Plain ``[WARNING]`` blocks are excluded:
        # their continuations are always magenta-wrapped, and an uncolored
        # line after one (e.g. ``TASK [nginx] *******``) is a new line, not
        # a continuation. Lines carrying any other colour (red, green, …)
        # still close the block and emit their own event. The block also
        # closes on a blank line or a JSONL event (see feed_line).
        if (
            self._current_warning is not None
            and self._current_warning.type == WarningType.DEPRECATION
            and not _ANSI_SGR_RE.search(line)
        ):
            self._current_warning.message = (
                self._current_warning.message.rstrip() + " " + clean.strip()
            )
            return []

        # Not warning-family: any open warning block ends here.
        self._current_warning = None

        retry_m = _RETRYING_RE.search(clean)
        if retry_m:
            host = (retry_m.group("host1") or retry_m.group("host2") or "").strip()
            retries_left = int(retry_m.group("left"))
            task_name = retry_m.group("task").strip()
            now_iso = datetime.now(timezone.utc).isoformat()
            return [
                cast(
                    JsonlEvent,
                    {
                        "_event": "v2_runner_retry",
                        "_timestamp": now_iso,
                        "host": host,
                        "retries_left": retries_left,
                        "task": {"name": task_name},
                    },
                )
            ]

        poll_m = _ASYNC_POLL_RE.search(clean)
        if poll_m:
            host = poll_m.group("host").strip()
            jid = poll_m.group("jid").strip()
            now_iso = datetime.now(timezone.utc).isoformat()
            return [
                cast(
                    JsonlEvent,
                    {
                        "_event": "v2_runner_on_async_poll",
                        "_timestamp": now_iso,
                        "host": host,
                        "ansible_job_id": jid,
                        "task": {},
                    },
                )
            ]

        # Classify the line via stderr_classifier and emit a synthetic

        # aom_stderr_line event so the session recording captures it.
        classified = classify(clean)
        now_iso = datetime.now(timezone.utc).isoformat()
        conn_id, confidence = self._resolve_connection(classified.host)
        stderr_event: JsonlEvent = {
            "_event": "aom_stderr_line",
            "_timestamp": now_iso,
            "line": line,
            "source": classified.source.value,
            "level": classified.level.value,
            "host": classified.host,
            "connection_id": conn_id,
            "attribution_confidence": confidence,
        }

        self._plaintext_lines.append(line)
        # This plaintext line is now the child's latest output — it may be
        # a live prompt candidate until a JSONL event supersedes it.
        self._plaintext_is_latest_output = True
        # R2: cap plaintext_lines at MAX_LOG_LINES so a long noisy run
        # can't grow this list without bound. Drop oldest first — the
        # tail is what's useful for "what did pexpect just see?" stall
        # diagnostics in runner.py.
        if len(self._plaintext_lines) > MAX_LOG_LINES:
            del self._plaintext_lines[: len(self._plaintext_lines) - MAX_LOG_LINES]

        return [stderr_event]

    def _handle_connection_event(self, event: JsonlEvent) -> None:
        """Update connection tracking state from a connection event.

        Intercepts ``aom_connection_acquired`` and ``aom_connection_released``
        events that flow through ``feed_line`` in EXECUTION phase. Maintains
        ``_active_connections`` as a host -> ordered list of active
        connection_ids so ``_handle_plaintext`` can look up the most-recent
        connection for a host and determine attribution confidence.
        """
        event_type = event.get("_event")
        host = event.get("host")
        conn_id = event.get("connection_id")
        if host is None or conn_id is None:
            return

        if event_type == "aom_connection_acquired":
            self._active_connections.setdefault(host, []).append(conn_id)
        elif event_type == "aom_connection_released":
            conns = self._active_connections.get(host)
            if conns and conn_id in conns:
                conns.remove(conn_id)
                if not conns:
                    del self._active_connections[host]

    def _resolve_connection(self, host: str | None) -> tuple[str | None, str]:
        """Resolve connection_id and attribution_confidence for a stderr line.

        Args:
            host: The host extracted by the classifier, or None for run-level lines.

        Returns:
            A ``(connection_id, attribution_confidence)`` pair. Run-level lines
            (host is None) always get ``(None, "unique")``. Lines with a host
            that has exactly one active connection get that connection_id and
            ``"unique"``. Lines with a host that has multiple overlapping active
            connections get the most-recent connection_id and ``"ambiguous"``.
            Lines with a host that has no active connections get ``(None, "unique")``.
        """
        if host is None:
            return None, "unique"

        conns = self._active_connections.get(host)
        if not conns:
            return None, "unique"

        if len(conns) == 1:
            return conns[0], "unique"

        return conns[-1], "ambiguous"

    def _is_jsonl_start_event(self, line: str) -> bool:
        """Check if line is a JSONL start event.

        Accepts both v2_playbook_on_start (ansible-core <2.20) and
        v2_playbook_on_play_start (ansible-core >=2.20, which no longer
        emits v2_playbook_on_start).
        """
        if not line.startswith("{"):
            return False
        try:
            data = _safe_loads(line)
            return bool(
                data.get("_event")
                in (
                    "v2_playbook_on_start",
                    "v2_playbook_on_play_start",
                )
            )
        except ValueError:
            return False

    def _is_jsonl_stats_event(self, line: str) -> bool:
        """Check if line is a v2_playbook_on_stats event."""
        if not line.startswith("{"):
            return False
        try:
            data = _safe_loads(line)
            return bool(data.get("_event") == "v2_playbook_on_stats")
        except ValueError:
            return False

    def _is_json(self, line: str) -> bool:
        """Check if line is valid JSON."""
        if not line.startswith("{"):
            return False
        try:
            _safe_loads(line)
            return True
        except ValueError:
            return False

    def _parse_json(self, line: str) -> dict:
        """Parse a JSON line into a dict."""
        result = _safe_loads(line)
        assert isinstance(result, dict), "Expected JSON object"
        return result

    def _handle_recap_output(self, line: str) -> None:
        """Handle PLAY RECAP output lines."""
        self._recap_lines.append(line)

    @property
    def warnings(self) -> list[WarningEntry]:
        return self._warnings

    def drain_warnings(self) -> list[WarningEntry]:
        """Return all warnings detected since the last drain and reset.

        Lets the caller (typically the runner) forward newly-seen warnings
        to the renderer without having to track an index. The internal
        list is replaced — `self.warnings` is empty afterward.
        """
        drained = self._warnings
        self._warnings = []
        return drained

    @property
    def recap_lines(self) -> list[str]:
        return self._recap_lines

    @property
    def plaintext_lines(self) -> list[str]:
        return self._plaintext_lines

    @property
    def latest_output_is_plaintext(self) -> bool:
        """True if the most recent classified output line was plaintext.

        A JSONL event consumed after a plaintext line flips this False.
        The runner's TIMEOUT prompt heuristic uses ``plaintext_lines[-1]``
        as a prompt candidate, but JSONL events never touch that list —
        so a stale line ending in ``?`` early in a run would otherwise
        stay the 'last plaintext' forever and arm a block-forever
        ``input()`` trap on every later quiet window. Gate the candidate
        on this flag so only genuinely-latest plaintext counts.
        """
        return self._plaintext_is_latest_output

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
    definitions: list[PlayDefinition] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    include_cache: dict[str, IncludeCacheEntry] = field(default_factory=dict)


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
            name = play_match.group(3).strip()
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
            name = play_match.group(3).strip()
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


def group_roles(tasks: list, parent_role: str | None = None) -> list:
    """Group consecutive same-role tasks (5 or more) into RoleGroupDefinition.

    Args:
        tasks: List of TaskDefinition objects
        parent_role: Name of the enclosing role, or None for top-level
            grouping under a play. Populated onto every produced
            ``RoleGroupDefinition`` so downstream walkers can reconstruct
            the full role path.

    Returns:
        List of TaskDefinition or RoleGroupDefinition objects. If the
        input already contains a nested ``RoleGroupDefinition`` (e.g. a
        parent's preflight that was itself recursively grouped), the
        nested group is passed through unchanged — only the *direct*
        ``TaskDefinition`` children at this level are re-grouped. This is
        a pure data-shape operation: no I/O, no recursion into role
        ``tasks/main.yml`` files.
    """
    if not tasks:
        return []

    result: list = []
    current_role: str | None = None
    current_group: list = []

    for task in tasks:
        # Pass-through: an already-grouped child role keeps its existing
        # grouping and the parent role that was set when it was built.
        if isinstance(task, RoleGroupDefinition):
            if len(current_group) >= 5:
                assert current_role is not None, "role should not be None for grouped tasks"
                result.append(
                    RoleGroupDefinition(role=current_role, tasks=current_group, parent=parent_role)
                )
            else:
                result.extend(current_group)
            current_group = []
            current_role = None
            result.append(task)
            continue

        task_role = getattr(task, "role", None)

        if task_role is None:
            if len(current_group) >= 5:
                assert current_role is not None, "role should not be None for grouped tasks"
                result.append(
                    RoleGroupDefinition(role=current_role, tasks=current_group, parent=parent_role)
                )
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
                result.append(
                    RoleGroupDefinition(role=current_role, tasks=current_group, parent=parent_role)
                )
            else:
                result.extend(current_group)
            current_group = [task]
            current_role = task_role

    if len(current_group) >= 5:
        assert current_role is not None, "role should not be None for grouped tasks"
        result.append(
            RoleGroupDefinition(role=current_role, tasks=current_group, parent=parent_role)
        )
    else:
        result.extend(current_group)

    return result
