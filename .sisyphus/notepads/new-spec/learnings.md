# Learnings: PTY Stream Parsing for AOM

## The Core Challenge

When running `ansible-playbook` via `pexpect.spawn()` with a PTY (pseudo-terminal), the output stream becomes a **merged stream** containing:

1. **JSONL events** - Structured events from `ansible.posix.jsonl` callback
2. **Non-JSONL content** - Various text output that bypasses the JSONL callback:
   - Password prompts (Vault, BECOME, SSH)
   - PLAY RECAP text (in some Ansible versions)
   - Deprecation warnings
   - Ansible banner text
   - SSH key fingerprints
   - Galaxy output (role downloads)

This document summarizes how to parse this mixed stream robustly.

---

## Existing Implementation Analysis

### ansible-aomp `json_stream.py` (Zero Dependencies)

**Location**: `/opt/syncthing/sync/ncc1031/git/ansible-aomp/src/ansible_aomp/json_stream.py`

**Key Design Decisions**:

```python
class JsonLineStream:
    def __init__(self):
        self._buffer = ""
        self._non_json_handler: Callable[[str], None] | None = None
    
    def set_non_json_handler(self, handler: Callable[[str], None]) -> None:
        """Set callback for non-JSON lines."""
        self._non_json_handler = handler
    
    def feed_line(self, line: str) -> Iterable[dict[str, Any]]:
        # Handle line continuation (backslash at end)
        if line.endswith('\\'):
            self._buffer += line[:-1]
            return
        
        # Add any buffered content
        if self._buffer:
            line = self._buffer + line
            self._buffer = ""
        
        # Skip empty lines
        if not line.strip():
            return
        
        # Try to parse as JSON
        try:
            obj = json.loads(line)
            yield obj
        except json.JSONDecodeError:
            # Not valid JSON - pass to handler
            if self._non_json_handler:
                self._non_json_handler(line)
            else:
                logger.debug(f"Non-JSON line: {line}")
```

**Strengths**:
- Simple, testable, no dependencies
- Buffering for multi-line JSON fragments
- Clean callback pattern for non-JSON lines
- `finalize()` handles remaining buffer

**Limitations**:
- **No content classification** - treats all non-JSON equally
- No distinction between password prompts, warnings, and other text
- No state machine for execution phase tracking

---

### ansible-aomp `runner.py` (Asyncio Subprocess)

**Location**: `/opt/syncthing/sync/ncc1031/git/ansible-aomp/src/ansible_aomp/runner.py`

**Key Pattern**:

```python
async def run_command(...):
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=process_env
    )
    
    async def read_stdout():
        if process.stdout:
            async for line in process.stdout:
                decoded = line.decode('utf-8', errors='replace').rstrip('\n\r')
                stdout_lines.append(decoded)
                if line_callback:
                    await line_callback(decoded)
    
    async def read_stderr():
        if process.stderr:
            async for line in process.stderr:
                decoded = line.decode('utf-8', errors='replace').rstrip('\n\r')
                if decoded:
                    logger.warning(decoded)
    
    # Read both streams concurrently
    await asyncio.gather(read_stdout(), read_stderr())
```

**Critical Difference for AOM**:
- aomp uses **separate stdout/stderr pipes**
- AOM uses **pexpect with PTY**, which merges both into one stream

**Why This Matters**:
1. In aomp: JSONL events on stdout, warnings on stderr (separate)
2. In AOM PTY: Everything mixed into one stream (merged)

---

## PTY Stream Characteristics

### What Goes Through the JSONL Callback?

The `ansible.posix.jsonl` callback writes these events to **stdout**:

| Event | When Emitted |
|-------|--------------|
| `v2_playbook_on_start` | Playbook begins |
| `v2_playbook_on_play_start` | Each play begins |
| `v2_runner_on_start` | Task starts (non-lockstep strategies) |
| `v2_playbook_on_task_start` | Task starts (lockstep strategies) |
| `v2_runner_on_ok` | Task succeeds |
| `v2_runner_on_failed` | Task fails |
| `v2_runner_on_skipped` | Task skipped |
| `v2_runner_on_unreachable` | Host unreachable |
| `v2_playbook_on_stats` | Playbook ends (PLAY RECAP data) |

**All of these are JSON lines** - easy to parse.

---

### What DOESN'T Go Through JSONL Callback?

#### 1. Password Prompts (getpass)

**Origin**: Ansible's `getpass` module reads from `/dev/tty`

**In PTY Mode**: The prompt and masked input appear in the PTY master stream

**Patterns**:
```
Vault password: 
Vault password (dev): 
SSH password: 
BECOME password: 
BECOME password[defaults to SSH password]: 
New Vault password: 
Confirm New Vault password: 
```

**Detection Regex**:
```python
PASSWORD_PATTERNS = [
    r'^Vault password(?:\s*\([^)]+\))?: $',
    r'^SSH password: $',
    r'^BECOME password(?:\s*\[.*\])?: $',
    r'^New Vault password: $',
    r'^Confirm New Vault password: $',
]
```

**Key Insight**: Password prompts appear **before** any JSONL events start - Ansible asks for passwords before running the playbook.

---

#### 2. PLAY RECAP Text

**Origin**: Ansible's Display class prints this after completion

**In JSONL mode**: The `v2_playbook_on_stats` event contains structured stats
**In some versions**: Plain text PLAY RECAP also appears

**Typical Output**:
```
PLAY RECAP *********************************************************************
localhost                  : ok=2    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

**When It Appears**: After `v2_playbook_on_stats` event in the stream

**JSONL Provides**: Same data in structured form:
```json
{
  "_event": "v2_playbook_on_stats",
  "stats": {
    "localhost": {
      "ok": 2, "changed": 1, "unreachable": 0, 
      "failures": 0, "skipped": 0, "rescued": 0, "ignored": 0
    }
  }
}
```

---

#### 3. Deprecation Warnings

**Origin**: Ansible's Display.deprecated() method writes to stderr

**In PTY Mode**: Merged into stdout stream

**Patterns**:
```
[DEPRECATION WARNING]: ...
[WARNING]: ...
```

**These can appear at any time** during playbook execution.

---

#### 4. Ansible Banner Text

**Origin**: Display class prints task banners

**Example**:
```
TASK [Install nginx] ***********************************************************
```

**In JSONL mode**: Task names come from JSONL events, not banner text

---

#### 5. SSH Key Fingerprints

**Origin**: SSH client prompts

**Example**:
```
The authenticity of host 'example.com (192.168.1.1)' can't be established.
ED25519 key fingerprint is SHA256:xxxxx.
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

**When**: First SSH connection to unknown host

---

#### 6. Galaxy Output

**Origin**: `ansible-galaxy` role downloads during playbook

**Example**:
```
- downloading role 'nginx', owned by geerlingguy
- downloading role from https://github.com/geerlingguy/ansible-role-nginx.git
- extracting geerlingguy.nginx to /etc/ansible/roles/geerlingguy.nginx
```

**When**: Playbook has role dependencies being resolved

---

## Temporal Sequence in PTY Stream

### Phase 1: Pre-Execution (Before Playbook Starts)

```
[Password prompts - if --ask-vault-pass, --ask-become-pass, etc.]
Vault password: ********
BECOME password: ********

[SSH key prompts - if first connection to host]
The authenticity of host '...' can't be established.
Are you sure you want to continue connecting? yes
```

**Characteristics**:
- Interactive, requires user input
- No JSONL events yet
- Text ends with ': ' followed by password input mask

---

### Phase 2: Playbook Execution (JSONL Events + Warnings)

```
{"_event":"v2_playbook_on_start","_timestamp":"..."}
{"_event":"v2_playbook_on_play_start","_timestamp":"...","play":{...}}

[Deprecation warnings may interleave]
[DEPRECATION WARNING]: Module 'foo' is deprecated

{"_event":"v2_runner_on_start","_timestamp":"...","task":{...}}
{"_event":"v2_runner_on_ok","_timestamp":"...","task":{...},"hosts":{...}}
...
```

**Characteristics**:
- JSONL events are primary content
- Non-JSON lines are warnings/errors
- These typically go to stderr in non-PTY mode, but merge in PTY

---

### Phase 3: Post-Execution (PLAY RECAP)

```
{"_event":"v2_playbook_on_stats","_timestamp":"...","stats":{...}}

[Optionally: Plaintext PLAY RECAP]
PLAY RECAP *********************************************************************
localhost: ok=2, changed=1, unreachable=0, failed=0, skipped=0

[Final output from Display class]
```

**Characteristics**:
- `v2_playbook_on_stats` is the last JSONL event
- Plaintext PLAY RECAP may follow
- Process exits after this

---

## Robust Stream Parser Design

### State Machine for Stream Phases

```python
from enum import Enum, auto

class StreamPhase(Enum):
    """Execution phases for the PTY stream."""
    PRE_RUN_PROMPTS = auto()   # Password/SSH prompts before execution
    EXECUTION      = auto()    # JSONL events + warnings
    POST_RUN_RECAP = auto()    # After v2_playbook_on_stats
    COMPLETED      = auto()    # Process has exited
```

### Enhanced Stream Parser

```python
import json
import re
from typing import Callable, Iterable
from collections.abc import Generator

class PtyStreamParser:
    """
    Parse mixed JSONL and text stream from pexpect PTY.
    
    Handles:
    - JSONL events from ansible.posix.jsonl callback
    - Password prompts (Vault, BECOME, SSH)
    - Warnings and deprecation notices
    - PLAY RECAP text
    - SSH key fingerprint prompts
    """
    
    PASSWORD_PATTERNS = [
        r'^Vault password(?:\s*\([^)]+\))?: $',
        r'^SSH password: $',
        r'^BECOME password(?:\s*\[.*\])?: $',
        r'^New Vault password: $',
        r'^Confirm New Vault password: $',
    ]
    
    WARNING_PATTERNS = [
        r'^\[DEPRECATION WARNING\]: ',
        r'^\[WARNING\]: ',
    ]
    
    PLAY_RECAP_PATTERN = r'^PLAY RECAP \*+$'
    SSH_PROMPT_PATTERN = r'^The authenticity of host .* can\'t be established'
    
    def __init__(self):
        self._buffer = ""
        self._phase = StreamPhase.PRE_RUN_PROMPTS
        self._last_event_type = None
        
        # Callbacks
        self._on_event: Callable[[dict], None] | None = None
        self._on_password_prompt: Callable[[str], str] | None = None
        self._on_warning: Callable[[str], None] | None = None
        self._on_text: Callable[[str], None] | None = None
    
    def set_callbacks(
        self,
        on_event: Callable[[dict], None] | None = None,
        on_password_prompt: Callable[[str], str] | None = None,
        on_warning: Callable[[str], None] | None = None,
        on_text: Callable[[str], None] | None = None,
    ) -> None:
        """Set callbacks for different stream content types."""
        self._on_event = on_event
        self._on_password_prompt = on_password_prompt
        self._on_warning = on_warning
        self._on_text = on_text
    
    def feed_line(self, line: str) -> Generator[dict, None, None]:
        """
        Process a line from the PTY stream.
        
        Yields parsed JSONL events.
        Calls appropriate callbacks for non-JSON content.
        """
        # Handle line continuation
        if line.endswith('\\'):
            self._buffer += line[:-1]
            return
        
        if self._buffer:
            line = self._buffer + line
            self._buffer = ""
        
        stripped = line.strip()
        if not stripped:
            return
        
        # Phase-aware classification
        if self._phase == StreamPhase.PRE_RUN_PROMPTS:
            yield from self._handle_pre_run_line(stripped)
        elif self._phase == StreamPhase.EXECUTION:
            yield from self._handle_execution_line(stripped, line)
        elif self._phase == StreamPhase.POST_RUN_RECAP:
            yield from self._handle_post_run_line(stripped)
    
    def _handle_pre_run_line(self, line: str) -> Generator[dict, None, None]:
        """Handle lines before playbook execution starts."""
        # Check for password prompts
        for pattern in self.PASSWORD_PATTERNS:
            if re.match(pattern, line):
                if self._on_password_prompt:
                    # This will block until user provides password
                    password = self._on_password_prompt(line)
                    # Password is sent to PTY separately
                return
        
        # Check for SSH key prompt
        if re.match(self.SSH_PROMPT_PATTERN, line):
            if self._on_text:
                self._on_text(line)
            return
        
        # Try to parse as JSON (start of execution)
        try:
            obj = json.loads(line)
            event_type = obj.get('_event', '')
            
            if event_type == 'v2_playbook_on_start':
                self._phase = StreamPhase.EXECUTION
                self._last_event_type = event_type
                yield obj
                return
        except json.JSONDecodeError:
            pass
        
        # Unknown pre-run text
        if self._on_text:
            self._on_text(line)
    
    def _handle_execution_line(self, line: str, raw_line: str) -> Generator[dict, None, None]:
        """Handle lines during playbook execution."""
        # Try JSON parse
        try:
            obj = json.loads(line)
            event_type = obj.get('_event', '')
            
            # Track last event type
            self._last_event_type = event_type
            
            # Check for end of execution
            if event_type == 'v2_playbook_on_stats':
                self._phase = StreamPhase.POST_RUN_RECAP
            
            yield obj
            return
        except json.JSONDecodeError:
            pass
        
        # Non-JSON during execution - classify
        for pattern in self.WARNING_PATTERNS:
            if re.match(pattern, line):
                if self._on_warning:
                    self._on_warning(line)
                return
        
        # Plain text line
        if self._on_text:
            self._on_text(raw_line.rstrip())
    
    def _handle_post_run_line(self, line: str) -> Generator[dict, None, None]:
        """Handle lines after playbook completes."""
        # PLAY RECAP text
        if re.match(self.PLAY_RECAP_PATTERN, line):
            if self._on_text:
                self._on_text(line)
            return
        
        # Stats line (host : ok=X changed=Y ...)
        if re.match(r'^[a-zA-Z0-9_.-]+\s*:', line):
            if self._on_text:
                self._on_text(line)
            return
        
        # Final output
        self._phase = StreamPhase.COMPLETED
        if self._on_text:
            self._on_text(line)
    
    def finalize(self) -> Generator[dict, None, None]:
        """Process any remaining buffer."""
        if self._buffer.strip():
            try:
                obj = json.loads(self._buffer)
                yield obj
            except json.JSONDecodeError:
                if self._on_text:
                    self._on_text(self._buffer)
```

---

## Integration with pexpect

### pexpect.spawn Pattern for AOM

```python
import pexpect
import sys

def run_ansible_with_pty(playbook: str, args: list[str], env: dict) -> int:
    """
    Run ansible-playbook via pexpect PTY.
    
    Returns exit code.
    """
    parser = PtyStreamParser()
    parser.set_callbacks(
        on_event=handle_event,
        on_password_prompt=handle_password_prompt,
        on_warning=log_warning,
        on_text=handle_raw_text
    )
    
    cmd = ['ansible-playbook', playbook, *args]
    
    child = pexpect.spawn(
        ' '.join(cmd),  # Or use list form
        encoding='utf-8',
        timeout=300,
        env=env
    )
    
    try:
        while True:
            try:
                index = child.expect([pexpect.EOF, '\n'], timeout=0.1)
                
                if index == 0:  # EOF
                    break
                
                # Process line
                line = child.before
                for event in parser.feed_line(line):
                    handle_event(event)
                    
            except pexpect.TIMEOUT:
                # Check if process is still running
                if not child.isalive():
                    break
                continue
            except pexpect.exceptions.TIMEOUT:
                continue
    finally:
        child.close()
    
    return child.exitstatus
```

---

## Password Prompt Handling with PTY

### Why pexpect is Required

**Problem**: Ansible's `getpass` module reads passwords from `/dev/tty`

- Regular subprocess stdin/stdout pipes don't work
- Password prompts need terminal interaction (masking, echo off)
- Textual/ANSI renderers capture stdin, preventing direct Terminal input

**Solution**: pexpect creates a PTY (pseudo-terminal)

```python
# pexpect creates a PTY automatically
child = pexpect.spawn('ansible-playbook playbook.yml')

# The PTY acts as /dev/tty for the subprocess
# Password prompts appear on child.before
# User input goes to child.sendline()
```

### Password Prompt Detection

```python
PASSWORD_PATTERNS = [
    (r'Vault password(?:\s*\([^)]+\))?: $', 'vault'),
    (r'Vault password \(([^)]+)\): $', 'vault_id'),
    (r'SSH password: $', 'ssh'),
    (r'BECOME password(?:\s*\[.*\])?: $', 'become'),
    (r'New Vault password: $', 'new_vault'),
    (r'Confirm New Vault password: $', 'confirm_vault'),
]

def detect_password_prompt(child: pexpect.spawn, timeout: float = 60) -> tuple[str, str] | None:
    """
    Detect password prompt in pexpect output.
    
    Returns (prompt_text, prompt_type) or None.
    """
    import re
    
    # Compile patterns
    patterns = [pexpect.EOF, pexpect.TIMEOUT]
    for pattern, _ in PASSWORD_PATTERNS:
        patterns.append(re.compile(pattern))
    
    try:
        index = child.expect(patterns, timeout=timeout)
        
        if index < 2:  # EOF or TIMEOUT
            return None
        
        # Got a password prompt
        prompt_text = child.before + child.after
        prompt_type = PASSWORD_PATTERNS[index - 2][1]
        return (prompt_text, prompt_type)
        
    except pexpect.TIMEOUT:
        return None
    except pexpect.EOF:
        return None
```

### Compact Mode Password Handling

**Approach**: Pass-through to terminal

```python
def handle_password_prompt(prompt_text: str, child: pexpect.spawn) -> str:
    """
    Handle password prompt in compact mode.
    
    1. Stop ANSI rendering (Rich Live)
    2. Show prompt from subprocess on actual terminal
    3. User types password (getpass handles masking)
    4. Send to PTY
    5. Resume rendering
    """
    # Stop live display
    live_display.stop()
    
    # Move cursor to bottom for prompt visibility
    sys.stdout.write('\033[999;0H')  # Move to bottom
    sys.stdout.flush()
    
    # Prompt is already visible from pexpect stream
    # getpass reads from /dev/tty (works in PTY mode)
    import getpass
    password = getpass.getpass('')
    
    # Send to PTY
    child.sendline(password)
    
    # Resume display
    live_display.start()
    
    return password
```

---

## Test Fixture Analysis

### From ansible-aomp Test Fixtures

**`success.jsonl`** (7 events):
```jsonl
{"_event":"v2_playbook_on_start","_timestamp":"..."}
{"_event":"v2_playbook_on_play_start","_timestamp":"...","play":{...},"tasks":[]}
{"_event":"v2_runner_on_start","_timestamp":"...","hosts":{},"task":{...}}
{"_event":"v2_runner_on_ok","_timestamp":"...","hosts":{...},"task":{...}}
{"_event":"v2_runner_on_start","_timestamp":"...","hosts":{},"task":{...}}
{"_event":"v2_runner_on_ok","_timestamp":"...","hosts":{...},"task":{...}}
{"_event":"v2_playbook_on_stats","_timestamp":"...","stats":{...}}
```

**`failure.jsonl`** (9 events):
- Includes `v2_runner_on_failed` event
- Includes `v2_runner_on_skipped` event
- Host result has error details (`rc`, `cmd`, `msg`)

### Test Cases for Stream Parsing

```python
def test_mixed_json_and_warnings():
    """Test stream with mixed JSON and warnings."""
    stream = JsonLineStream()
    
    warnings = []
    stream.set_non_json_handler(lambda line: warnings.append(line))
    
    lines = [
        '{"_event": "v2_playbook_on_start"}',
        '[DEPRECATION WARNING]: foo is deprecated',
        '{"_event": "v2_playbook_on_play_start"}',
        'Sunday 09 November 2025  16:39:04 +0100',  # timestamp line
        '{"_event": "v2_runner_on_ok"}',
    ]
    
    events = []
    for line in lines:
        events.extend(stream.feed_line(line))
    
    assert len(events) == 3
    assert len(warnings) == 2
    assert "DEPRECATION" in warnings[0]
    assert "Sunday" in warnings[1]


def test_multiline_json():
    """Test buffering for multi-line JSON."""
    stream = JsonLineStream()
    
    # First line with continuation
    results = list(stream.feed_line('{"_event": "v2_runner_on_ok", \\'))
    assert len(results) == 0
    
    # Complete the JSON
    results = list(stream.feed_line('"task": {"name": "test"}}'))
    assert len(results) == 1
    assert results[0]["_event"] == "v2_runner_on_ok"
```

---

## Key Design Recommendations

### 1. Separate Concerns

```
StreamParser (core)     → JSONL event parsing + text classification
PasswordHandler         → Interactive password prompts (pexpect)
EventHandler           → Business logic for each event type
StateTracker           → Run state machine
Renderer               → Display updates
```

### 2. Use Phase-Aware Parsing

```python
phase = PRE_RUN_PROMPTS  → Look for password prompts
phase = EXECUTION        → Process JSONL + warnings
phase = POST_RUN_RECAP   → Handle final output
phase = COMPLETED        → Done
```

### 3. Buffer Line-by-Line

- Don't assume lines are complete JSON
- Handle backslash continuation
- Call `finalize()` at stream end

### 4. Classify Non-JSON Content

```python
if is_password_prompt(line):
    → on_password_prompt callback
elif is_warning(line):
    → on_warning callback
elif is_play_recap(line):
    → on_text callback (but note it)
else:
    → on_text callback (unknown)
```

### 5. Handle Interactive Prompts in PTY Context

- pexpect provides PTY for password masking
- Use `getpass.getpass()` for terminal input
- Stop ANSI rendering during password entry

---

## Implementation Checklist for AOM

### Core Parser (`core/parser.py`)

- [ ] `PtyStreamParser` class with phase tracking
- [ ] `feed_line()` method for incremental parsing
- [ ] `set_callbacks()` for event/warning/text handlers
- [ ] Password prompt pattern detection
- [ ] Warning pattern detection
- [ ] PLAY RECAP pattern detection
- [ ] `finalize()` for remaining buffer

### Runner (`services/runner.py`)

- [ ] `pexpect.spawn()` with PTY
- [ ] Line-by-line reading with `expect([EOF, '\n'])`
- [ ] Timeout handling for password prompts
- [ ] Signal forwarding (Ctrl+C)
- [ ] Process status tracking

### Password Handling

- [ ] `PasswordHandler` class for compact mode
- [ ] TUI modal integration for `--tui` mode
- [ ] Multiple password type support
- [ ] Integration with pexpect

### State Machine

- [ ] RunState enum with proper transitions
- [ ] Phase tracking (PRE_RUN, EXECUTION, POST_RUN)
- [ ] Event handling per type

---

## References

- **ansible-aomp json_stream.py**: `/opt/syncthing/sync/ncc1031/git/ansible-aomp/src/ansible_aomp/json_stream.py`
- **ansible-aomp runner.py**: `/opt/syncthing/sync/ncc1031/git/ansible-aomp/src/ansible_aomp/runner.py`
- **ansible-aomp tests**: `/opt/syncthing/sync/ncc1031/git/ansible-aomp/tests/test_json_stream.py`
- **AOM Specification**: `/opt/syncthing/sync/ncc1031/git/new_ansible-aom/SPECIFICATION.md`
- **pexpect Documentation**: https://pexpect.readthedocs.io/

---

*Last Updated: 2026-04-20*
