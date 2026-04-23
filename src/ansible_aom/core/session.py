"""Session manager and artifact writer for AOM.

This module handles session recording, artifact creation, and session
inspection. See SPECIFICATION.md Section 6.3 for session details.
"""

import json
import logging
import shutil
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


_uuidv7_counter = 0
_uuidv7_last_ms = 0


def generate_uuidv7() -> str:
    """Generate a UUIDv7 session ID.

    UUIDv7 is time-sortable, which allows sessions to be ordered chronologically
    by their ID alone. The first 48 bits contain a timestamp, making the first
    8 characters suitable for display in list views.

    Returns:
        UUIDv7 string in standard format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    """
    global _uuidv7_counter, _uuidv7_last_ms

    now_ms = int(time.time() * 1000)

    if now_ms == _uuidv7_last_ms:
        _uuidv7_counter = (_uuidv7_counter + 1) & 0xFFF
        if _uuidv7_counter == 0:
            now_ms += 1
    else:
        _uuidv7_counter = 0
        _uuidv7_last_ms = now_ms

    rand_bytes = uuid.uuid4().bytes

    result = bytearray(16)
    result[0] = (now_ms >> 40) & 0xFF
    result[1] = (now_ms >> 32) & 0xFF
    result[2] = (now_ms >> 24) & 0xFF
    result[3] = (now_ms >> 16) & 0xFF
    result[4] = (now_ms >> 8) & 0xFF
    result[5] = now_ms & 0xFF
    result[6] = (0x70) | ((_uuidv7_counter >> 8) & 0x0F)
    result[7] = _uuidv7_counter & 0xFF
    result[8] = (rand_bytes[8] & 0x3F) | 0x80
    result[9:] = rand_bytes[9:16]

    return str(uuid.UUID(bytes=bytes(result)))


class SessionManager:
    """Manages session recording and artifact creation.

    Sessions are stored during execution at:
        ~/.local/state/aom/sessions/{uuidv7}/
        ├── events.jsonl      # All JSONL events
        ├── stderr.log        # Captured stderr
        └── meta.json         # Session metadata

    After completion, sessions are consolidated to:
        ~/.local/state/aom/artifacts/{uuidv7}.aom

    Attributes:
        session_id: The current session ID (UUIDv7)
        session_dir: The session directory path
    """

    def __init__(
        self,
        session_dir: Path | None = None,
        artifacts_dir: Path | None = None,
        playbook: str = "",
    ) -> None:
        self._session_dir = session_dir
        self._artifacts_dir = artifacts_dir
        self._playbook = playbook
        self._session_id: str | None = None
        self._events_file: Path | None = None
        self._stderr_file: Path | None = None
        self._meta_file: Path | None = None
        self._start_time: datetime | None = None
        self._active_sessions: dict[str, dict[str, Any]] = {}

    @property
    def session_id(self) -> str | None:
        return self._session_id

    @property
    def session_dir(self) -> Path | None:
        return self._session_dir

    def start_session(self, playbook: str) -> str:
        """Create a new session and return the session ID (UUIDv7).

        Creates the session directory structure with events.jsonl, stderr.log,
        and meta.json files.

        Args:
            playbook: Path to the playbook being executed

        Returns:
            The session ID (UUIDv7 format)
        """
        session_id = generate_uuidv7()
        self._session_id = session_id
        self._playbook = playbook
        self._start_time = datetime.now(timezone.utc)

        assert self._session_dir is not None, "Session directory must be set"
        session_path = self._session_dir / session_id
        session_path.mkdir(parents=True, exist_ok=True)
        session_path.chmod(0o755)

        self._events_file = session_path / "events.jsonl"
        self._stderr_file = session_path / "stderr.log"
        self._meta_file = session_path / "meta.json"

        self._events_file.touch()
        self._events_file.chmod(0o644)

        self._stderr_file.touch()
        self._stderr_file.chmod(0o644)

        meta = {
            "playbook": playbook,
            "start_time": self._start_time.isoformat().replace("+00:00", "Z"),
            "version": "1.0",
            "session_id": session_id,
        }
        with open(self._meta_file, "w") as f:
            json.dump(meta, f)
        self._meta_file.chmod(0o644)

        self._active_sessions[session_id] = {
            "session_path": session_path,
            "events_file": self._events_file,
            "stderr_file": self._stderr_file,
            "meta_file": self._meta_file,
            "start_time": self._start_time,
            "playbook": playbook,
        }

        return session_id

    def record_event(self, session_id: str, event: dict[str, Any]) -> None:
        """Record a JSONL event to the session file.

        Args:
            session_id: The session ID
            event: The event dictionary to record
        """
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")

        events_file = self._active_sessions[session_id]["events_file"]
        with open(events_file, "a") as f:
            f.write(json.dumps(event) + "\n")

    def record_stderr(self, session_id: str, line: str) -> None:
        """Record a stderr line.

        Args:
            session_id: The session ID
            line: The stderr line to record
        """
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")

        stderr_file = self._active_sessions[session_id]["stderr_file"]
        with open(stderr_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def end_session(self, session_id: str, status: str) -> None:
        """Finalize session and update metadata.

        Args:
            session_id: The session ID
            status: Final status ("completed", "failed", "crashed")
        """
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session_info = self._active_sessions[session_id]
        meta_file = session_info["meta_file"]
        start_time = session_info["start_time"]

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        with open(meta_file) as f:
            meta = json.load(f)

        meta["status"] = status
        meta["end_time"] = end_time.isoformat().replace("+00:00", "Z")
        meta["duration_seconds"] = duration

        with open(meta_file, "w") as f:
            json.dump(meta, f)

    def create_artifact(self, session_id: str) -> Path:
        """Create .aom artifact file from session.

        The artifact format is JSONL with:
        - First line: metadata header
        - Middle lines: events
        - Last line: stats summary

        Args:
            session_id: The session ID

        Returns:
            Path to the created artifact file
        """
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session_info = self._active_sessions[session_id]
        session_path = session_info["session_path"]

        if self._artifacts_dir is None:
            raise ValueError("artifacts_dir not set")

        self._artifacts_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = self._artifacts_dir / f"{session_id}.aom"

        events_file = session_path / "events.jsonl"
        meta_file = session_path / "meta.json"

        with open(meta_file) as f:
            meta = json.load(f)

        events = []
        if events_file.exists():
            with open(events_file) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        events.append(json.loads(line))

        stats_event = None
        for event in reversed(events):
            if event.get("_event") == "v2_playbook_on_stats":
                stats_event = event
                break

        with open(artifact_path, "w") as f:
            metadata_line = {
                "type": "metadata",
                "playbook": meta["playbook"],
                "version": meta.get("version", "1.0"),
                "created": meta.get(
                    "end_time", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                ),
                "session_id": session_id,
            }
            f.write(json.dumps(metadata_line) + "\n")

            for event in events:
                event_line = {"type": "event", **event}
                f.write(json.dumps(event_line) + "\n")

            if stats_event:
                stats_line = {
                    "type": "stats",
                    **stats_event.get("stats", {}),
                }
            else:
                stats_line = {"type": "stats"}
            f.write(json.dumps(stats_line) + "\n")

        artifact_path.chmod(0o600)

        return artifact_path


def cleanup_old_sessions(
    session_dir: Path,
    keep_count: int = 100,
    keep_days: int = 30,
) -> int:
    """Remove old sessions based on policy.

    Sessions are cleaned up based on:
    - Count: Keep the most recent N sessions
    - Age: Remove sessions older than D days

    Args:
        session_dir: Directory containing session directories
        keep_count: Maximum number of sessions to keep (default 100)
        keep_days: Maximum age in days (default 30)

    Returns:
        Number of sessions deleted
    """
    if not session_dir.exists():
        return 0

    sessions = []
    for session_path in session_dir.iterdir():
        if not session_path.is_dir():
            continue

        meta_file = session_path / "meta.json"
        if meta_file.exists():
            try:
                with open(meta_file) as f:
                    meta = json.load(f)
                start_time_str = meta.get("start_time", "")
                if start_time_str:
                    start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                    sessions.append((session_path, start_time, meta))
            except json.JSONDecodeError, ValueError:
                sessions.append((session_path, datetime.now(timezone.utc), {}))
        else:
            sessions.append((session_path, datetime.now(timezone.utc), {}))

    sessions.sort(key=lambda x: x[1], reverse=True)

    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)

    to_delete = []
    for i, (session_path, start_time, meta) in enumerate(sessions):
        if i >= keep_count or start_time < cutoff:
            to_delete.append(session_path)

    deleted = 0
    for session_path in to_delete:
        shutil.rmtree(session_path)
        deleted += 1

    return deleted


def list_sessions(session_dir: Path) -> list[dict[str, Any]]:
    """List all sessions in the state directory.

    Returns sessions sorted by start time (newest first).

    Args:
        session_dir: Directory containing session directories

    Returns:
        List of session summary dictionaries, each containing:
        - session_id: Full UUID
        - short_id: First 8 characters for display
        - playbook: Playbook name
        - start_time: Start time string
        - status: Session status
        - duration_seconds: Duration in seconds (if completed)
    """
    if not session_dir.exists():
        return []

    sessions = []
    for session_path in session_dir.iterdir():
        if not session_path.is_dir():
            continue

        meta_file = session_path / "meta.json"
        if not meta_file.exists():
            continue

        try:
            with open(meta_file) as f:
                meta = json.load(f)

            session_id = session_path.name
            sessions.append(
                {
                    "session_id": session_id,
                    "short_id": session_id[:8],
                    "playbook": meta.get("playbook", ""),
                    "start_time": meta.get("start_time", ""),
                    "status": meta.get("status", ""),
                    "duration_seconds": meta.get("duration_seconds"),
                }
            )
        except json.JSONDecodeError, KeyError:
            continue

    sessions.sort(key=lambda x: x.get("start_time", ""), reverse=True)

    return sessions


def load_session(session_id: str, session_dir: Path) -> dict[str, Any] | None:
    """Load a session by ID.

    Args:
        session_id: The session ID to load
        session_dir: Directory containing session directories

    Returns:
        Session dictionary containing:
        - metadata fields (playbook, status, etc.)
        - events: List of parsed event dictionaries
        - stderr: List of stderr lines
        - malformed_lines: Count of malformed JSONL lines
        Returns None if session not found.
    """
    session_path = session_dir / session_id
    if not session_path.exists():
        return None

    meta_file = session_path / "meta.json"
    events_file = session_path / "events.jsonl"
    stderr_file = session_path / "stderr.log"

    result: dict[str, Any] = {}

    if meta_file.exists():
        try:
            with open(meta_file) as f:
                result = json.load(f)
        except json.JSONDecodeError:
            result = {"playbook": "", "status": ""}

    events = []
    malformed_lines = 0

    if events_file.exists():
        with open(events_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    malformed_lines += 1

    result["events"] = events
    result["malformed_lines"] = malformed_lines

    if stderr_file.exists():
        with open(stderr_file) as f:
            result["stderr"] = f.read().splitlines()
    else:
        result["stderr"] = []

    result["session_id"] = session_id

    return result


def create_session_summary(session: dict[str, Any]) -> dict[str, Any]:
    """Create a human-readable summary of a session.

    Args:
        session: Session dictionary from load_session

    Returns:
        Summary dictionary with key session information
    """
    summary = {
        "session_id": session.get("session_id", ""),
        "playbook": session.get("playbook", ""),
        "status": session.get("status", ""),
        "start_time": session.get("start_time", ""),
        "end_time": session.get("end_time"),
        "duration_seconds": session.get("duration_seconds"),
        "malformed_lines": session.get("malformed_lines", 0),
        "event_count": len(session.get("events", [])),
    }

    if summary.get("malformed_lines", 0) > 0:
        summary["summary_note"] = f"{summary['malformed_lines']} malformed lines"

    return summary
