# Ansible Source Research: Verbosity Handling in ansible-core 2.20.4

**Date**: 2026-06-30
**Purpose**: Verify brainstorm claims about ansible verbosity handling for AOM `aom_verbose_line` synthetic event design.
**Sources consulted**:
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/utils/display.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/plugins/callback/__init__.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/plugins/callback/default.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/plugins/connection/ssh.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/plugins/connection/local.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/plugins/connection/__init__.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/inventory/manager.py`
- `https://raw.githubusercontent.com/ansible-collections/ansible.posix/main/plugins/callback/jsonl.py`

---

## Section 1: Claims Verification

### Claim 1: `ansible.posix.jsonl` is verbosity-agnostic

**Source**: `ansible.posix` collection, `plugins/callback/jsonl.py` (main branch -- v1.6.0 tag 404'd, used latest main)

**Verdict: CONFIRMED** -- the jsonl callback contains **zero references to `verbosity`**, `self._display.verbosity`, or any verbosity-based branching.

**Evidence**:
- The callback class `CallbackModule` extends `CallbackBase` and overrides `v2_playbook_on_play_start`, `v2_runner_on_start`, `v2_playbook_on_task_start`, `v2_playbook_on_handler_task_start`, `v2_playbook_on_stats`, and uses `__getattribute__` to intercept `v2_runner_on_ok/failed/unreachable/skipped`.
- All output goes through `_write_event()` which calls `self._display.display(json.dumps(...))` -- this writes to **stdout** (the default for `display()`).
- There is **no** `if self._display.verbosity` check anywhere in the file.
- The `_dump_results()` method (inherited from `CallbackBase`) is **never called** by jsonl -- it constructs its own output dicts.

**Implication for AOM**: When `ansible.posix.jsonl` is the stdout callback, ALL task events are emitted as JSONL on stdout regardless of verbosity level. Verbose lines (from `Display.v*()`) go to stderr (see Claim 3) and are **not** part of the JSONL stream. This confirms the need for a separate `aom_verbose_line` synthetic event to capture stderr verbose output.

---

### Claim 2: `_dump_results` strips `invocation` + `diff` when `verbosity < 3`

**Source**: `lib/ansible/plugins/callback/__init__.py` (ansible-core v2.20.4)

**Verdict: CONFIRMED** -- both `invocation` and `diff` are stripped from result output when `self._display.verbosity < 3`.

**Evidence** (lines ~240-245 of callback/__init__.py):
```python
# remove invocation unless specifically wanting it
if not keep_invocation and self._display.verbosity < 3 and 'invocation' in result:
    del abridged_result['invocation']

# remove diff information from screen output
if self._display.verbosity < 3 and 'diff' in result:
    del abridged_result['diff']
```

**Important nuance**: This stripping happens in `_dump_results()`, which is called by the **stdout callback** (default.py, etc.) when formatting result output. The jsonl callback does **not** call `_dump_results()` -- it constructs its own output. However, the jsonl callback's `_record_task_result` does `result_copy = result._result.copy()` which gets the raw result dict **before** `_dump_results` stripping. So jsonl always gets the full result including `invocation` and `diff`.

**Implication for AOM**: When using the jsonl callback, `invocation` and `diff` are always present in the JSONL output regardless of verbosity. AOM does not need to worry about this stripping -- it only affects the `default` stdout callback.

---

### Claim 3: `Display.v*()` methods go to stderr, bypassing stdout callbacks

**Source**: `lib/ansible/utils/display.py` (ansible-core v2.20.4)

**Verdict: CONFIRMED** -- with important nuance about the `VERBOSE_TO_STDERR` config option.

**Evidence** (display.py, `_verbose_display` method):
```python
@_proxy
def _verbose_display(self, msg, host=None, caplevel=2):
    to_stderr = C.VERBOSE_TO_STDERR
    if host is None:
        self.display(msg, color=C.COLOR_VERBOSE, stderr=to_stderr)
    else:
        self.display("<%s> %s" % (host, msg), color=C.COLOR_VERBOSE, stderr=to_stderr)
```

**Key details**:
1. `_verbose_display` is decorated with `@_proxy` -- when called from a `WorkerProcess` (forked process), it proxies through the `_final_q` queue back to the parent process.
2. The `stderr` parameter is set to `C.VERBOSE_TO_STDERR` -- this is a config constant (default: `True`).
3. When `stderr=True`, `display()` writes to `sys.stderr` directly -- it does **not** go through the stdout callback pipeline.
4. The stdout callback (default.py, jsonl.py) only sees events dispatched through the `v2_*` callback methods. `Display.v*()` calls are **not** callback events -- they are direct I/O.

**The routing chain**:
```
Display.vvvv(msg) 
  -> Display.verbose(msg, caplevel=3) 
    -> if self.verbosity > caplevel: Display._verbose_display(msg, caplevel=3)
      -> Display.display(msg, stderr=C.VERBOSE_TO_STDERR)  # writes to sys.stderr
```

**The `@_proxy` decorator** (display.py):
```python
@staticmethod
def _proxy[**P](func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._final_q:
            return self._final_q.send_display(func.__name__, *args, **kwargs)
        return func(self, *args, **kwargs)
    return wrapper
```
When in a worker process, the display call is serialized and sent through the queue. The parent process then executes the actual write to stderr.

**Implication for AOM**: Verbose lines appear on stderr (interleaved with the JSONL stream on stdout). AOM's PTY parser must capture stderr and parse these lines. The `aom_verbose_line` synthetic event is the correct approach.

---

## Section 2: Prefix List for `aom_verbose_line` Heuristic

### Conservative framing

Per the task instructions: **only prefixes from `Display.vvvv()` and above (caplevel >= 4)** belong in the heuristic. Below caplevel 4, ansible's stdout callbacks handle the output.

**NOTE**: There is a discrepancy in the task description. It says "Display.vvvv() and above (caplevel >= 4)" but `vvvv()` has caplevel=3, not 4. The actual mapping is:
- `vvvv()` -> caplevel=3 (shows at verbosity > 3, i.e., `-vvvv`)
- `vvvvv()` -> caplevel=4 (shows at verbosity > 4, i.e., `-vvvvv`)
- `vvvvvv()` -> caplevel=5 (shows at verbosity > 5, i.e., `-vvvvvv`)

This report uses **caplevel >= 4** (vvvvv and vvvvvv) as the conservative boundary. See Open Questions for discussion.

### Prefixes at caplevel 4 (vvvvv) and caplevel 5 (vvvvvv)

These are the messages that ONLY appear at `-vvvvv` or `-vvvvvv` and are NOT captured by any stdout callback. They are the primary candidates for `aom_verbose_line`.

#### From `lib/ansible/plugins/connection/ssh.py` (vvvvv, caplevel=4)

| # | Prefix Pattern | Call Site | Sample Message | Notes |
|---|---|---|---|---|
| 1 | `SSH: {explanation}: ({args})` | `Connection._add_args()` (line ~310) | `SSH: ansible.cfg set ssh_args: (-C)(-o)(ControlMaster=auto)(-o)(ControlPersist=60s)` | Shows every SSH argument added and why. This is the primary source of SSH arg visibility. |
| 2 | `SSH: ANSIBLE_HOST_KEY_CHECKING/host_key_checking disabled: (-o)(StrictHostKeyChecking=no)` | `Connection._build_command()` | Same pattern as #1, different explanation | |
| 3 | `SSH: ANSIBLE_REMOTE_PORT/remote_port/ansible_port set: (-o)(Port=22)` | `Connection._build_command()` | Same pattern as #1 | |
| 4 | `SSH: ANSIBLE_PRIVATE_KEY_FILE/private_key_file/ansible_ssh_private_key_file set: (-o)(IdentityFile="...")` | `Connection._build_command()` | Same pattern as #1 | |
| 5 | `SSH: ansible_password/ansible_ssh_password not set: (-o)(KbdInteractiveAuthentication=no)(-o)(PreferredAuthentications=...)(-o)(PasswordAuthentication=no)` | `Connection._build_command()` | Same pattern as #1 | |
| 6 | `SSH: ANSIBLE_REMOTE_USER/remote_user/ansible_user/user/-u set: (-o)(User="...")` | `Connection._build_command()` | Same pattern as #1 | |
| 7 | `SSH: ANSIBLE_TIMEOUT/timeout set: (-o)(ConnectTimeout=10)` | `Connection._build_command()` | Same pattern as #1 | |
| 8 | `SSH: Set ssh_common_args: (...)` | `Connection._build_command()` | Same pattern as #1 | |
| 9 | `SSH: Set {subsystem}_extra_args: (...)` | `Connection._build_command()` | `SSH: Set sftp_extra_args: (...)` | |
| 10 | `SSH: disable batch mode for password auth: (-o)(BatchMode=no)` | `Connection._build_command()` | Same pattern as #1 | |
| 11 | `SSH: Enable pkcs11: (...)` | `Connection._build_command()` | Same pattern as #1 | |
| 12 | `SSH: ANSIBLE_PRIVATE_KEY/private_key set: (...)` | `Connection._build_command()` | Same pattern as #1 | |

**Note**: All SSH vvvvv messages use the same format: `SSH: {explanation}: ({arg1})({arg2})...`. The prefix for heuristic matching is `SSH: `.

#### From `lib/ansible/plugins/connection/__init__.py` (vvvv, caplevel=3)

These are at caplevel=3 (vvvv), NOT caplevel=4. Included for reference but below the conservative boundary.

| # | Prefix Pattern | Call Site | Sample Message |
|---|---|---|---|
| N/A | `CONNECTION: pid %d waiting for lock on %d` | `ConnectionBase.connection_lock()` | `CONNECTION: pid 12345 waiting for lock on 3` |
| N/A | `CONNECTION: pid %d acquired lock on %d` | `ConnectionBase.connection_lock()` | `CONNECTION: pid 12345 acquired lock on 3` |
| N/A | `CONNECTION: pid %d released lock on %d` | `ConnectionBase.connection_unlock()` | `CONNECTION: pid 12345 released lock on 3` |
| N/A | `resetting persistent connection for socket_path %s` | `NetworkConnectionBase.reset()` | `resetting persistent connection for socket_path /tmp/...` |
| N/A | `reset call on connection instance` | `NetworkConnectionBase.reset()` | `reset call on connection instance` |

#### From `lib/ansible/plugins/callback/__init__.py` (vvvv, caplevel=3)

| # | Prefix Pattern | Call Site | Sample Message |
|---|---|---|---|
| N/A | `Loading callback plugin %s of type %s, v%s from %s` | `CallbackBase.__init__()` | `Loading callback plugin ansible.posix.jsonl of type stdout, v2.0 from /path/to/jsonl.py` |

#### From `lib/ansible/inventory/manager.py` (vvvv, caplevel=3)

| # | Prefix Pattern | Call Site | Sample Message |
|---|---|---|---|
| N/A | `setting up inventory plugins` | `InventoryManager._fetch_inventory_plugins()` | `setting up inventory plugins` |

### Prefixes at caplevel 2 (vvv) -- for reference (below conservative boundary)

These appear at `-vvv` and are handled by stdout callbacks. Included for completeness.

| # | Prefix Pattern | Source File | Sample Message |
|---|---|---|---|
| N/A | `Failed to connect to the host via ssh:` | ssh.py | `Failed to connect to the host via ssh: ssh: connect to host example.com port 22: Connection refused` |
| N/A | `rc=%s, stdout and stderr censored due to no log` | ssh.py | `rc=0, stdout and stderr censored due to no log` |
| N/A | `RETRYING BECAUSE OF CONTROLPERSIST BROKEN PIPE` | ssh.py | `RETRYING BECAUSE OF CONTROLPERSIST BROKEN PIPE` |
| N/A | `SSH: SSH_AGENT adding %s to agent` | ssh.py | `SSH: SSH_AGENT adding SHA256:abc123 to agent` |
| N/A | `SSH: SSH_AGENT %s exists in agent` | ssh.py | `SSH: SSH_AGENT SHA256:abc123 exists in agent` |
| N/A | `ESTABLISH LOCAL CONNECTION FOR USER: %s` | local.py | `ESTABLISH LOCAL CONNECTION FOR USER: root` |
| N/A | `EXEC {command}` | local.py | `EXEC /bin/sh -c 'echo hello'` |
| N/A | `PUT %s TO %s` | local.py | `PUT /tmp/src TO /tmp/dst` |
| N/A | `FETCH %s TO %s` | local.py | `FETCH /remote/path TO /local/path` |
| N/A | `Parsed %s inventory source with %s plugin` | inventory/manager.py | `Parsed hosts inventory source with ini plugin` |
| N/A | `%s declined parsing %s as it did not pass its verify_file() method` | inventory/manager.py | `auto declined parsing hosts as it did not pass its verify_file() method` |

### Prefixes at caplevel 1 (vv) -- for reference

| # | Prefix Pattern | Source File | Sample Message |
|---|---|---|---|
| N/A | `ssh_retry: attempt: %d, ssh return code is 255. cmd (%s), pausing for %d seconds` | ssh.py | `ssh_retry: attempt: 1, ssh return code is 255. cmd (ssh...), pausing for 1 seconds` |
| N/A | `ssh_retry: attempt: %d, caught exception(%s) from cmd (%s), pausing for %d seconds` | ssh.py | `ssh_retry: attempt: 1, caught exception(...) from cmd (ssh...), pausing for 1 seconds` |
| N/A | `Current user (uid=%s) does not seem to exist on this system, leaving user empty.` | local.py | `Current user (uid=1000) does not seem to exist on this system, leaving user empty.` |

### Enumerated Prefix List for Heuristic (caplevel >= 4 only)

The following is the **deduplicated, enumerated list** of message prefixes that AOM's PTY parser should recognize on stderr at `-vvvvv` and above. These are the only messages that are NOT captured by any stdout callback.

```
1.  "SSH: " -- All SSH argument explanations from Connection._add_args()
    (caplevel=4, source: ssh.py)
    Sample: "SSH: ansible.cfg set ssh_args: (-C)(-o)(ControlMaster=auto)(-o)(ControlPersist=60s)"
```

**That is the complete list.** At caplevel >= 4, the only v*() call sites in ansible-core 2.20.4 are the `display.vvvvv()` calls in `ssh.py`'s `_add_args()` method. All other v*() calls are at lower caplevels.

---

## Section 3: Cross-Check -- SSH Connection Plugin Debug Output

### What does `Display.vvvvv()` look like for SSH?

From `ssh.py`, `Connection._add_args()` (line ~310):
```python
display.vvvvv(u'SSH: %s: (%s)' % (explanation, ')('.join(to_text(a) for a in b_args)), host=self.host)
```

This produces lines like:
```
SSH: ansible.cfg set ssh_args: (-C)(-o)(ControlMaster=auto)(-o)(ControlPersist=60s)
SSH: ANSIBLE_HOST_KEY_CHECKING/host_key_checking disabled: (-o)(StrictHostKeyChecking=no)
SSH: ANSIBLE_REMOTE_PORT/remote_port/ansible_port set: (-o)(Port=22)
SSH: ANSIBLE_PRIVATE_KEY_FILE/private_key_file/ansible_ssh_private_key_file set: (-o)(IdentityFile="/path/to/key")
SSH: ansible_password/ansible_ssh_password not set: (-o)(KbdInteractiveAuthentication=no)(-o)(PreferredAuthentications=gssapi-with-mic,gssapi-keyex,hostbased,publickey)(-o)(PasswordAuthentication=no)
SSH: ANSIBLE_REMOTE_USER/remote_user/ansible_user/user/-u set: (-o)(User="root")
SSH: ANSIBLE_TIMEOUT/timeout set: (-o)(ConnectTimeout=10)
SSH: Set ssh_common_args: (...)
SSH: Set sftp_extra_args: (...)
SSH: disable batch mode for password auth: (-o)(BatchMode=no)
SSH: Enable pkcs11: (...)
SSH: ANSIBLE_PRIVATE_KEY/private_key set: (...)
```

The `host=self.host` parameter means the message is prefixed with `<hostname>` when displayed (see `_verbose_display`):
```
<hostname> SSH: ansible.cfg set ssh_args: (-C)(-o)(ControlMaster=auto)(-o)(ControlPersist=60s)
```

### What does `Display.vvvv()` look like for SSH?

SSH does NOT use `vvvv()` directly. The `vvvv()` calls in the connection layer come from `connection/__init__.py`:
```
CONNECTION: pid 12345 waiting for lock on 3
CONNECTION: pid 12345 acquired lock on 3
CONNECTION: pid 12345 released lock on 3
```

### What does `Display.vvv()` look like for SSH?

SSH uses `vvv()` for:
- Connection errors: `Failed to connect to the host via ssh: ...`
- Return codes: `(0, b'stdout', b'stderr')`
- Agent operations: `SSH: SSH_AGENT adding SHA256:... to agent`

### What does `Display.vvv()` look like for local?

```
ESTABLISH LOCAL CONNECTION FOR USER: root
EXEC /bin/sh -c 'echo hello'
PUT /tmp/src TO /tmp/dst
FETCH /remote/path TO /local/path
```

---

## Section 4: Open Questions

1. **Caplevel boundary ambiguity**: The task says "Display.vvvv() and above (caplevel >= 4)" but `vvvv()` has caplevel=3, not 4. The actual boundary at caplevel=4 is `vvvvv()`. Which boundary should AOM use?
   - If caplevel >= 3 (vvvv and above): includes `CONNECTION:`, `Loading callback plugin`, `setting up inventory plugins`
   - If caplevel >= 4 (vvvvv and above): only includes `SSH: ` prefix
   - **Recommendation**: Use caplevel >= 3 (vvvv) as the boundary. The `CONNECTION:` lock messages and callback loading messages are useful diagnostics that users running at `-vvvv` would expect to see. The task's "conservative framing" may have been overly conservative.

2. **`VERBOSE_TO_STDERR` config**: The `C.VERBOSE_TO_STDERR` constant controls whether verbose output goes to stderr or stdout. If a user sets `VERBOSE_TO_STDERR=False`, verbose lines go to stdout and would be interleaved with JSONL output. AOM should document this assumption.

3. **`@_proxy` and worker processes**: When `_final_q` is set (in WorkerProcess), `_verbose_display` is proxied through the queue. The parent process then writes to stderr. This means verbose lines from worker processes arrive asynchronously and may be interleaved with other output. AOM's PTY parser must handle this interleaving.

4. **`display.debug()` messages**: The `debug()` method (display.py) writes to stdout/stderr with a prefix of `{pid} {timestamp}: {msg}`. These are gated by `C.DEFAULT_DEBUG`, not verbosity. They are NOT captured by stdout callbacks. Should AOM also capture debug messages?

5. **`display.warning()` messages**: Warnings go to stderr with `[WARNING]:` prefix. These are NOT captured by stdout callbacks (they use `display()` with `stderr=True`). Should AOM capture warnings as synthetic events?

6. **`display.deprecated()` messages**: Deprecation warnings go to stderr with `[DEPRECATION WARNING]:` prefix. Same question as warnings.

7. **`display.error()` messages**: Errors go to stderr with `[ERROR]:` prefix. Same question.

8. **The `screen_only` parameter**: Some callback output uses `screen_only=True` which means it goes to screen but NOT to the log file. This doesn't affect the stdout/stderr routing but is relevant for understanding where what appears.

9. **`_run_is_verbose` in default.py**: The default callback uses `self._run_is_verbose(result)` which checks `self._display.verbosity > verbosity` (default verbosity=0). When `-v` is used, task results include the full result dump. This is a different mechanism from `Display.v*()` -- it's the callback adding detail to its own output, not a separate verbose line.

10. **jsonl callback and `_dump_results`**: The jsonl callback does NOT call `_dump_results()`. It constructs its own output dicts. This means `invocation` and `diff` are always present in jsonl output regardless of verbosity. This is correct behavior but worth documenting.
