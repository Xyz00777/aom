# Existing stderr Classification in AOM

**Date**: 2026-06-30
**Goal**: Determine whether AOM already classifies/categorizes/tags stderr lines from ansible-playbook, to avoid reinventing.

---

## 1. Does AOM's PTY parser already classify stderr lines by type?

**YES — partially.** The `PtyStreamParser._handle_plaintext` method (in `core/parser.py`) classifies non-JSON lines from the PTY stream into **two categories**:

### Category 1: Warnings / Deprecations

File: `/opt/syncthing/sync/ncc1031/git/ansible-aom/src/ansible_aom/core/parser.py`, lines 167–281

```python
# Lines 167-171: The regex patterns used for classification
WARNING_PATTERNS: list[str] = [
    r"^\[WARNING\]:",
    r"^\[DEPRECATION WARNING\]:",
    r"^\[DEPRECATED\]:",
]

# Lines 256-281: The classification logic
def _handle_plaintext(self, line: str) -> None:
    clean = _ANSI_SGR_RE.sub("", line)
    for pattern in self.WARNING_PATTERNS:
        if re.match(pattern, clean):
            warning_type = WarningType.WARNING
            if "DEPRECATION" in pattern:
                warning_type = WarningType.DEPRECATION
            elif "DEPRECATED" in pattern:
                warning_type = WarningType.DEPRECATION

            self._warnings.append(
                WarningEntry(
                    type=warning_type,
                    message=clean,
                    timestamp=datetime.now(),
                )
            )
            return

    self._plaintext_lines.append(line)
```

The `WarningEntry` model (lines 72-79 of `core/models.py`):

```python
@dataclass
class WarningEntry:
    """A classified warning or deprecation from the PTY stream."""
    type: WarningType
    message: str
    timestamp: datetime | None = None
    source: str = ""
```

The `WarningType` enum (lines 65-69 of `core/models.py`):

```python
class WarningType(Enum):
    """Warning classification type."""
    WARNING = "warning"
    DEPRECATION = "deprecation"
```

### Category 2: Password prompts

File: `/opt/syncthing/sync/ncc1031/git/ansible-aom/src/ansible_aom/core/parser.py`, lines 173-184

```python
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
```

These are detected in `feed_line` (lines 208-211) during `PRE_RUN_PROMPTS` phase:

```python
for pattern in self.PASSWORD_PATTERNS:
    if re.search(pattern, line_stripped):
        self._pending_password_prompt = line_stripped
        return []
```

### Category 3: Everything else (unclassified plaintext)

Lines that don't match warnings or password prompts fall through to `_plaintext_lines` (line 283):

```python
self._plaintext_lines.append(line)
```

**No further classification** — these are stored as raw strings with no type/kind/level metadata.

---

## 2. Does AOM's model carry a "kind" or "type" field on stderr lines?

**NO — for the raw stderr log.** The `SessionManager.record_stderr` method (in `session/store.py`, lines 360-372) writes lines verbatim to `stderr.log` with no classification:

```python
def record_stderr(self, session_id: str, line: str) -> None:
    stderr_file = self._active_sessions[session_id]["stderr_file"]
    with open(stderr_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")
```

**YES — for warnings specifically.** The `WarningEntry` dataclass carries `type: WarningType` (WARNING or DEPRECATION), `message`, `timestamp`, and `source`. But this is a separate data structure from the raw stderr log — warnings are extracted from the plaintext stream and stored in `parser.warnings`, while the raw line also goes to `_plaintext_lines`.

**NO — no `stderr_kind`, `stderr_type`, `stderr_category`, or `stderr_tag` field exists anywhere in the codebase.** The grep for these terms returned zero results.

---

## 3. Are there existing regex patterns for SSH, CONNECTION, etc.?

**NO — not in the parser or classification layer.** The grep for `SSH:`, `CONNECTION:`, `UNREACHABLE`, `FAILED`, `fatal` in `core/` and `ansible/` found:

- `SSH password:` — only as a password-prompt pattern (not as a debug/error line classifier)
- `UNREACHABLE` / `FAILED` — only as `Status` enum values in `core/models.py` (line 59-61), used for host state tracking from JSONL events, **not** for stderr line classification
- No regex patterns match `SSH: ` (the debug prefix), `CONNECTION:`, or other ansible stderr prefixes

The only ANSI-related regex is the SGR stripper (used in both `core/parser.py` line 38 and `core/prompts.py` line 77):

```python
_ANSI_SGR_RE = re.compile(r"\x1b\[[0-9;]*m")
```

---

## 4. Code quotes for all matches found

### Warning classification (parser.py)

| What | File | Lines |
|------|------|-------|
| `WARNING_PATTERNS` regex list | `core/parser.py` | 167–171 |
| `PASSWORD_PATTERNS` regex list | `core/parser.py` | 173–184 |
| `_handle_plaintext` classification logic | `core/parser.py` | 256–281 |
| `WarningType` enum | `core/models.py` | 65–69 |
| `WarningEntry` dataclass | `core/models.py` | 72–79 |
| `drain_warnings` method | `core/parser.py` | 346–355 |
| `_ANSI_SGR_RE` (ANSI stripper) | `core/parser.py` | 38 |
| `_ANSI_SGR_RE` (ANSI stripper) | `core/prompts.py` | 77 |

### Stderr recording (no classification)

| What | File | Lines |
|------|------|-------|
| `record_stderr` (raw write) | `session/store.py` | 360–372 |
| `_SessionSink.record_stderr` | `ansible/runner.py` | 194–201 |
| `_NullSink.record_stderr` | `ansible/runner.py` | 120–121 |

### Stderr consumption points in runner.py

| What | File | Lines |
|------|------|-------|
| Preflight errors → `sink.record_stderr` | `ansible/runner.py` | 397 |
| Password prompt → `sink.record_stderr` | `ansible/runner.py` | 730–731 |
| Flushed held output → `sink.record_stderr` | `ansible/runner.py` | 821 |
| Warnings → `sink.record_stderr` | `ansible/runner.py` | 915 |

### Password prompt patterns (duplicated in runner.py for pexpect)

| What | File | Lines |
|------|------|-------|
| `_PASSWORD_PATTERNS` (pexpect-level) | `ansible/runner.py` | 230–245 |

### Interactive prompt detection (pure functions in core/)

| What | File | Lines |
|------|------|-------|
| `is_password_prompt` | `core/prompts.py` | 45–47 |
| `looks_like_interactive_prompt` | `core/prompts.py` | 85–146 |
| `reconstruct_pause_prompt` | `core/prompts.py` | 149–200 |

---

## 5. Verdict: PARTIAL-EXISTS

**Existing classification (reusable):**

| Classification | Where | Granularity |
|---------------|-------|-------------|
| `[WARNING]:` vs `[DEPRECATION WARNING]:` vs `[DEPRECATED]:` | `core/parser.py:_handle_plaintext` | 2 types (WARNING, DEPRECATION) |
| Password prompts (10 patterns) | `core/parser.py:PASSWORD_PATTERNS` + `core/prompts.py:PASSWORD_PATTERNS` | Binary (is-password vs not) |
| Interactive prompts (pause/vars_prompt) | `core/prompts.py:looks_like_interactive_prompt` | Binary (is-interactive vs not) |

**What does NOT exist (needs to be built):**

| Missing | Example lines |
|---------|---------------|
| SSH debug lines (`SSH: ` prefix) | `SSH: EXEC ssh -C ...` |
| Connection errors | `fatal: [host]: UNREACHABLE! => ...` (on stderr, not JSONL) |
| Verbose task output | `TASK [name] ********************` (plaintext echo) |
| Host-level status lines | `ok: [host]`, `changed: [host]`, `skipping: [host]` |
| Generic error lines | `[ERROR]: ...`, `ERROR! ...` |
| Module stderr | Lines from `module_stderr` field content |
| `CONNECTION:` debug lines | `CONNECTION: ...` |
| `fatal:` lines on stderr | `fatal: [hostname]: FAILED! => ...` |

**Key architectural insight:** The parser's `_handle_plaintext` method is the right extension point. Currently it classifies warnings (→ `WarningEntry`) and everything else (→ `_plaintext_lines`). A new stderr classification layer would slot into the `else` branch at line 283, before the `self._plaintext_lines.append(line)` fallthrough.

The `WarningEntry` pattern (dataclass with `type` enum + `message` + `timestamp`) is a good model to follow for the new classification — extend it or create a parallel `StderrEntry` with a richer `StderrKind` enum (e.g., `SSH_DEBUG`, `CONNECTION_DEBUG`, `TASK_HEADER`, `HOST_RESULT`, `ERROR`, `WARNING`, `DEPRECATION`, `UNKNOWN`).

**Bottom line:** The warning/deprecation classification is reusable. Everything else (SSH debug, connection errors, verbose task output, host result lines, generic errors) needs to be built from scratch.
