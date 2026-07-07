# stderr Classification Taxonomy for ansible-core 2.20.4

**Date**: 2026-06-30
**Purpose**: Exhaustive enumeration of every category of line that ansible-core 2.20.x and ansible.posix write to stderr, for building the AOM `aom_stderr_line` classifier.
**Sources consulted**:
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/utils/display.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/plugins/callback/__init__.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/plugins/callback/default.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/plugins/connection/ssh.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/plugins/connection/local.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/plugins/connection/__init__.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/inventory/manager.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/plugins/loader.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/parsing/vault/__init__.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/executor/playbook_executor.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/executor/task_queue_manager.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/executor/task_executor.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/executor/process/worker.py`
- `https://raw.githubusercontent.com/ansible/ansible/v2.20.4/lib/ansible/cli/__init__.py`
- `https://raw.githubusercontent.com/ansible-collections/ansible.posix/main/plugins/callback/jsonl.py`

---

## How stderr Routing Works

The `Display` class (singleton) has a single `display()` method that writes to either `sys.stdout` or `sys.stderr`:

```python
# display.py, line ~280
if not stderr:
    fileobj = sys.stdout
else:
    fileobj = sys.stderr
```

The routing decision is made per-call via the `stderr` parameter. The following `Display` methods **always** set `stderr=True`:

| Method | stderr value | Source (display.py) |
|--------|-------------|-------------------|
| `_verbose_display()` | `C.VERBOSE_TO_STDERR` (default: `True`) | line ~370 |
| `_warning()` | `stderr=True` | line ~470 |
| `_deprecated()` | `stderr=True` | line ~430 |
| `_error()` | `stderr=True` | line ~510 |
| `debug()` | `stderr=False` (goes to stdout) | line ~380 |

**Key insight**: `_verbose_display()` uses `C.VERBOSE_TO_STDERR` which defaults to `True` but is configurable. If a user sets `VERBOSE_TO_STDERR=False`, all verbose output goes to stdout instead. AOM should document this assumption.

---

## Section 1: Exhaustive Line Category Enumeration

### Category 1: Warnings (`[WARNING]:`)

**Prefix pattern**: `^\[WARNING\]: `

**Caplevel**: Always emitted (caplevel=-2 in `_warning()`). Not gated by verbosity.

**Source**: `display.py`, `_warning()` method, line ~460-470:
```python
@_proxy
def _warning(self, warning: _messages.WarningSummary) -> None:
    msg = _display_utils.format_message(warning, ...)
    msg = f"[WARNING]: {msg}"
    if self._deduplicate(msg, self._warns):
        return
    self.display(msg, color=C.config.get_config_value('COLOR_WARN'), stderr=True, caplevel=-2)
```

**Sample lines**:
```
[WARNING]: No inventory was parsed, only implicit localhost is available
[WARNING]: Could not match supplied host pattern, ignoring: nonexistent
[WARNING]: provided hosts list is empty, only localhost is available. Note that the implicit localhost does not match 'all'
[WARNING]: Invalid/incorrect username/password. Skipping remaining 0 retries to prevent account lockout:
[WARNING]: Error in vault password prompt (some_vault_id): ...
[WARNING]: Error getting vault password file (some_vault_id): ...
[WARNING]: Error in vault password file loading (some_vault_id): ...
[WARNING]: Skipping callback plugin 'some_plugin', unable to load
[WARNING]: Failed to load callback plugin 'some_plugin'.
[WARNING]: Failed to load inventory plugin, skipping some_plugin
[WARNING]: Unable to parse /path/to/inventory as an inventory source
[WARNING]: Reset is not implemented for this connection
[WARNING]: Not prompting as we are not in interactive mode
[WARNING]: Could not create retry file '/path/to/retry'.
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[WARNING]: You are running the development version of Ansible.
[WARNING]: running with default collection some.collection
[WARNING]: Non UTF-8 encoded data replaced with "?" while displaying text to stdout/stderr.
[WARNING]: failed to patch stdout/stderr for fork-safety: ...
[WARNING]: failed to reconfigure stdout/stderr with custom encoding error handler: ...
[WARNING]: log file at '/path' is not writeable and we cannot create it, aborting
[WARNING]: DEFAULT_LOG_PATH can not be a directory '/path', aborting
[WARNING]: One or more worker processes are still running and will be terminated.
[WARNING]: The loop variable 'item' is already in use.
[WARNING]: Persistent connection logging is enabled for host. This will log ALL interactions
```

**Host association**: None. Warnings are run-level messages. No `<hostname>` prefix.

**Deduplication**: `_warning()` deduplicates via `self._warns` set. Same warning text is only emitted once per run.

**Sub-categories** (all share the `[WARNING]:` prefix):
- Inventory loading failures
- Plugin loading failures
- Vault password errors
- SSH connection warnings
- Configuration warnings
- Runtime warnings (loop vars, retry files, etc.)
- System warnings (via `system_warning()` which calls `warning()`)

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/utils/display.py#L460-L470

---

### Category 2: Deprecation Warnings (`[DEPRECATION WARNING]:`)

**Prefix pattern**: `^\[DEPRECATION WARNING\]: `

**Caplevel**: Always emitted (caplevel not set, but gated by `DEPRECATION_WARNINGS` config). Not gated by verbosity.

**Source**: `display.py`, `_deprecated()` method, line ~420-435:
```python
@_proxy
def _deprecated(self, warning: _messages.DeprecationSummary) -> None:
    if not _deprecation_warnings_enabled():
        return
    self.warning('Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.')
    msg = _display_utils.format_message(warning, ...)
    msg = f'[DEPRECATION WARNING]: {msg}'
    if self._deduplicate(msg, self._deprecations):
        return
    self.display(msg, color=C.config.get_config_value('COLOR_DEPRECATE'), stderr=True)
```

**Sample lines**:
```
[DEPRECATION WARNING]: The 'some_plugin' callback plugin implements deprecated method 'runner_on_ok'.
[DEPRECATION WARNING]: Distribution Ubuntu 20.04 on host db1 should use the python3 interpreter, but is using python2.
[DEPRECATION WARNING]: Use [x:y] inclusive subscripts instead of [x-y] which has been removed
```

**Host association**: None. Deprecation warnings are run-level.

**Note**: `_deprecated()` first emits a `[WARNING]:` line about disabling deprecation warnings, then the actual `[DEPRECATION WARNING]:` line. The classifier will see TWO stderr lines per deprecation.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/utils/display.py#L420-L435

---

### Category 3: Errors (`[ERROR]:`)

**Prefix pattern**: `^\[ERROR\]: `

**Caplevel**: Always emitted (caplevel=-1 in `_error()`). Not gated by verbosity.

**Source**: `display.py`, `_error()` method, line ~500-515:
```python
@_proxy
def _error(self, error: _messages.ErrorSummary, stderr: bool) -> None:
    msg = _display_utils.format_message(error, ...)
    msg = f'[ERROR]: {msg}'
    if self._deduplicate(msg, self._errors):
        return
    self.display(msg, color=C.config.get_config_value('COLOR_ERROR'), stderr=stderr, caplevel=-1)
```

**Sample lines**:
```
[ERROR]: No matching task "some_task" found.
[ERROR]: User interrupted execution
[ERROR]: Unexpected Exception, this is probably a bug.
```

**Host association**: None. Errors are run-level.

**Deduplication**: `_error()` deduplicates via `self._errors` set.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/utils/display.py#L500-L515

---

### Category 4: Preflight / Startup Errors (unprefixed, to stderr)

**Prefix pattern**: `^ERROR: ` (uppercase, no brackets, from `cli/__init__.py`)

**Caplevel**: Always emitted, before Display is fully initialized.

**Source**: `cli/__init__.py`, line ~55-60:
```python
except Exception as ex:
    if isinstance(ex, AnsibleError):
        ex_msg = ' '.join((ex.message, ex._help_text or '')).strip()
    else:
        ex_msg = str(ex)
    print(f'ERROR: {ex_msg}\n\n{"".join(traceback.format_exception(ex))}', file=sys.stderr)
    sys.exit(5)
```

**Sample lines**:
```
ERROR: Ansible could not initialize the preferred locale: ...
ERROR: Ansible requires the locale encoding to be UTF-8; Detected ...
ERROR: Ansible requires the filesystem encoding to be UTF-8; Detected ...
ERROR: Ansible requires blocking IO on stdin/stdout/stderr. Non-blocking file handles detected: ...
```

**Host association**: None. These are pre-CLI-initialization errors.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/cli/__init__.py#L55-L60

---

### Category 5: CLI-level Errors (via `display.error()`)

**Prefix pattern**: `^\[ERROR\]: ` (same as Category 3, but from CLI context)

**Source**: `cli/__init__.py`, `cli_executor()` method, line ~230-240:
```python
except AnsibleError as ex:
    display.error(ex)
    exit_code = ex._exit_code
except KeyboardInterrupt:
    display.error("User interrupted execution")
    exit_code = ExitCode.KEYBOARD_INTERRUPT
except Exception as ex:
    ...
    display.error(ex2)
    exit_code = ExitCode.UNKNOWN_ERROR
```

**Sample lines**:
```
[ERROR]: Specified inventory, host pattern and/or --limit leaves us with no hosts to target.
[ERROR]: No inventory was parsed, please check your configuration and options.
```

**Host association**: None.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/cli/__init__.py#L230-L240

---

### Category 6: SSH Verbose Debug (`SSH: ` at caplevel=4, vvvvv)

**Prefix pattern**: `^SSH: ` (when host is set, prefixed as `<hostname> SSH: `)

**Caplevel**: 4 (vvvvv). Only visible at `-vvvvv` and above.

**Source**: `ssh.py`, `_add_args()` method, line ~310:
```python
display.vvvvv(u'SSH: %s: (%s)' % (explanation, ')('.join(to_text(a) for a in b_args)), host=self.host)
```

**Sample lines**:
```
<hostname> SSH: ansible.cfg set ssh_args: (-C)(-o)(ControlMaster=auto)(-o)(ControlPersist=60s)
<hostname> SSH: ANSIBLE_HOST_KEY_CHECKING/host_key_checking disabled: (-o)(StrictHostKeyChecking=no)
<hostname> SSH: ANSIBLE_REMOTE_PORT/remote_port/ansible_port set: (-o)(Port=22)
<hostname> SSH: ANSIBLE_PRIVATE_KEY_FILE/private_key_file/ansible_ssh_private_key_file set: (-o)(IdentityFile="/path/to/key")
<hostname> SSH: ansible_password/ansible_ssh_password not set: (-o)(KbdInteractiveAuthentication=no)(-o)(PreferredAuthentications=...)(-o)(PasswordAuthentication=no)
<hostname> SSH: ANSIBLE_REMOTE_USER/remote_user/ansible_user/user/-u set: (-o)(User="root")
<hostname> SSH: ANSIBLE_TIMEOUT/timeout set: (-o)(ConnectTimeout=10)
<hostname> SSH: Set ssh_common_args: (...)
<hostname> SSH: Set sftp_extra_args: (...)
<hostname> SSH: disable batch mode for password auth: (-o)(BatchMode=no)
<hostname> SSH: Enable pkcs11: (...)
<hostname> SSH: ANSIBLE_PRIVATE_KEY/private_key set: (...)
```

**Host association**: YES. `host=self.host` is passed, so `_verbose_display` wraps it as `<hostname> SSH: ...`.

**Host extraction**: From `<hostname> SSH:` prefix. The hostname is between `<` and `>` before `SSH:`.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/ssh.py#L310-L315

---

### Category 7: SSH Agent Operations (`SSH: SSH_AGENT ...` at caplevel=2, vvv)

**Prefix pattern**: `^SSH: SSH_AGENT `

**Caplevel**: 2 (vvv). Visible at `-vvv` and above.

**Source**: `ssh.py`, `_populate_agent()` method, line ~340-350:
```python
if public_key not in client:
    display.vvv(f'SSH: SSH_AGENT adding {fingerprint} to agent', host=self.host)
    ...
else:
    display.vvv(f'SSH: SSH_AGENT {fingerprint} exists in agent', host=self.host)
```

**Sample lines**:
```
<hostname> SSH: SSH_AGENT adding SHA256:abc123 to agent
<hostname> SSH: SSH_AGENT SHA256:abc123 exists in agent
```

**Host association**: YES. `host=self.host` is passed.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/ssh.py#L340-L350

---

### Category 8: SSH Connection Errors (`Failed to connect to the host via ssh:` at caplevel=2, vvv)

**Prefix pattern**: `^Failed to connect to the host via ssh:`

**Caplevel**: 2 (vvv). Visible at `-vvv` and above.

**Source**: `ssh.py`, `_handle_error()` function, line ~100-110:
```python
if SSH_ERROR:
    msg = "Failed to connect to the host via ssh:"
    ...
    display.vvv(msg, host=host)
```

Also for non-255 return codes (1-254):
```python
if 1 <= return_tuple[0] <= 254:
    msg = u"Failed to connect to the host via ssh:"
    ...
    display.vvv(msg, host=host)
```

**Sample lines**:
```
<hostname> Failed to connect to the host via ssh: ssh: connect to host example.com port 22: Connection refused
<hostname> Failed to connect to the host via ssh: Permission denied (publickey,password).
```

**Host association**: YES. `host=host` is passed.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/ssh.py#L100-L120

---

### Category 9: SSH Retry Messages (`ssh_retry:` at caplevel=1, vv)

**Prefix pattern**: `^ssh_retry: attempt:`

**Caplevel**: 1 (vv). Visible at `-vv` and above.

**Source**: `ssh.py`, `_ssh_retry` decorator, line ~170-180:
```python
if isinstance(e, AnsibleConnectionFailure):
    msg = u"ssh_retry: attempt: %d, ssh return code is 255. cmd (%s), pausing for %d seconds" % (attempt + 1, cmd_summary, pause)
else:
    msg = (u"ssh_retry: attempt: %d, caught exception(%s) from cmd (%s), "
           u"pausing for %d seconds" % (attempt + 1, to_text(e), cmd_summary, pause))
display.vv(msg, host=self.host)
```

**Sample lines**:
```
<hostname> ssh_retry: attempt: 1, ssh return code is 255. cmd (ssh...), pausing for 1 seconds
<hostname> ssh_retry: attempt: 2, caught exception(Connection refused) from cmd (ssh...), pausing for 3 seconds
```

**Host association**: YES. `host=self.host` is passed.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/ssh.py#L170-L180

---

### Category 10: SSH Return Code / Censored Output (`rc=%s` at caplevel=2, vvv)

**Prefix pattern**: `^rc=`

**Caplevel**: 2 (vvv). Visible at `-vvv` and above.

**Source**: `ssh.py`, `_ssh_retry` decorator, line ~150-155:
```python
if self._play_context.no_log:
    display.vvv(u'rc=%s, stdout and stderr censored due to no log' % return_tuple[0], host=self.host)
else:
    display.vvv(str(return_tuple), host=self.host)
```

**Sample lines**:
```
<hostname> rc=0, stdout and stderr censored due to no log
<hostname> (0, b'stdout', b'stderr')
```

**Host association**: YES. `host=self.host` is passed.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/ssh.py#L150-L155

---

### Category 11: ControlPersist Broken Pipe (`RETRYING BECAUSE OF CONTROLPERSIST BROKEN PIPE` at caplevel=2, vvv)

**Prefix pattern**: `^RETRYING BECAUSE OF CONTROLPERSIST BROKEN PIPE`

**Caplevel**: 2 (vvv). Visible at `-vvv` and above.

**Source**: `ssh.py`, `_ssh_retry` decorator, line ~160-165:
```python
except (AnsibleControlPersistBrokenPipeError):
    ...
    display.vvv(u"RETRYING BECAUSE OF CONTROLPERSIST BROKEN PIPE")
```

**Sample line**:
```
RETRYING BECAUSE OF CONTROLPERSIST BROKEN PIPE
```

**Host association**: NO. `host` is NOT passed in this call. It's a bare string.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/ssh.py#L160-L165

---

### Category 12: Connection Lock Messages (`CONNECTION: pid ...` at caplevel=3, vvvv)

**Prefix pattern**: `^CONNECTION: pid \d+ (waiting for|acquired|released) lock on \d+`

**Caplevel**: 3 (vvvv). Visible at `-vvvv` and above.

**Source**: `connection/__init__.py`, `connection_lock()` and `connection_unlock()` methods, line ~130-140:
```python
def connection_lock(self) -> None:
    f = self._play_context.connection_lockfd
    display.vvvv('CONNECTION: pid %d waiting for lock on %d' % (os.getpid(), f), host=self._play_context.remote_addr)
    fcntl.lockf(f, fcntl.LOCK_EX)
    display.vvvv('CONNECTION: pid %d acquired lock on %d' % (os.getpid(), f), host=self._play_context.remote_addr)

def connection_unlock(self) -> None:
    f = self._play_context.connection_lockfd
    fcntl.lockf(f, fcntl.LOCK_UN)
    display.vvvv('CONNECTION: pid %d released lock on %d' % (os.getpid(), f), host=self._play_context.remote_addr)
```

**Sample lines**:
```
<hostname> CONNECTION: pid 12345 waiting for lock on 3
<hostname> CONNECTION: pid 12345 acquired lock on 3
<hostname> CONNECTION: pid 12345 released lock on 3
```

**Host association**: YES. `host=self._play_context.remote_addr` is passed.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/__init__.py#L130-L140

---

### Category 13: Persistent Connection Reset (`resetting persistent connection` at caplevel=3, vvvv)

**Prefix pattern**: `^resetting persistent connection for socket_path`

**Caplevel**: 3 (vvvv). Visible at `-vvvv` and above.

**Source**: `connection/__init__.py`, `NetworkConnectionBase.reset()` method, line ~200-205:
```python
def reset(self) -> None:
    if self._socket_path:
        self.queue_message('vvvv', 'resetting persistent connection for socket_path %s' % self._socket_path)
        self.close()
    self.queue_message('vvvv', 'reset call on connection instance')
```

**Note**: This uses `queue_message()` which queues the message for the controller process. The controller then calls `display.vvvv()` with the message. The host is NOT directly embedded in the message string.

**Sample lines**:
```
resetting persistent connection for socket_path /tmp/ansible-ssh-somepath
reset call on connection instance
```

**Host association**: Indirect. The message is queued per-connection-instance, which is per-host. But the host is not in the message text.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/__init__.py#L200-L205

---

### Category 14: Callback Loading (`Loading callback plugin` at caplevel=3, vvvv)

**Prefix pattern**: `^Loading callback plugin`

**Caplevel**: 3 (vvvv). Visible at `-vvvv` and above.

**Source**: `callback/__init__.py`, `CallbackBase.__init__()`, line ~55-60:
```python
if self._display.verbosity >= 4:
    name = getattr(self, 'CALLBACK_NAME', 'unnamed')
    ctype = getattr(self, 'CALLBACK_TYPE', 'old')
    version = getattr(self, 'CALLBACK_VERSION', '1.0')
    self._display.vvvv('Loading callback plugin %s of type %s, v%s from %s' % (name, ctype, version, sys.modules[self.__module__].__file__))
```

**Sample line**:
```
Loading callback plugin ansible.posix.jsonl of type stdout, v2.0 from /path/to/jsonl.py
```

**Host association**: NO. No host parameter.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/callback/__init__.py#L55-L60

---

### Category 15: Inventory Plugin Setup (`setting up inventory plugins` at caplevel=3, vvvv)

**Prefix pattern**: `^setting up inventory plugins`

**Caplevel**: 3 (vvvv). Visible at `-vvvv` and above.

**Source**: `inventory/manager.py`, `_fetch_inventory_plugins()` method, line ~100:
```python
display.vvvv('setting up inventory plugins')
```

**Sample line**:
```
setting up inventory plugins
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/inventory/manager.py#L100

---

### Category 16: Inventory Parsing Results (`Parsed ... inventory source` at caplevel=2, vvv)

**Prefix pattern**: `^Parsed .* inventory source with .* plugin`

**Caplevel**: 2 (vvv). Visible at `-vvv` and above.

**Source**: `inventory/manager.py`, `parse_source()` method, line ~160:
```python
parsed = True
display.vvv('Parsed %s inventory source with %s plugin' % (source, plugin_name))
```

**Sample line**:
```
Parsed hosts inventory source with ini plugin
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/inventory/manager.py#L160

---

### Category 17: Inventory Plugin Declined (`declined parsing` at caplevel=2, vvv)

**Prefix pattern**: `^.* declined parsing .* as it did not pass its verify_file() method`

**Caplevel**: 2 (vvv). Visible at `-vvv` and above.

**Source**: `inventory/manager.py`, `parse_source()` method, line ~170:
```python
display.vvv("%s declined parsing %s as it did not pass its verify_file() method" % (plugin_name, source))
```

**Sample line**:
```
auto declined parsing hosts as it did not pass its verify_file() method
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/inventory/manager.py#L170

---

### Category 18: Local Connection Establishment (`ESTABLISH LOCAL CONNECTION FOR USER:` at caplevel=2, vvv)

**Prefix pattern**: `^ESTABLISH LOCAL CONNECTION FOR USER:`

**Caplevel**: 2 (vvv). Visible at `-vvv` and above.

**Source**: `local.py`, `_connect()` method, line ~40-45:
```python
if not self._connected:
    display.vvv(u"ESTABLISH LOCAL CONNECTION FOR USER: {0}".format(self._play_context.remote_user), host=self._play_context.remote_addr)
    self._connected = True
```

**Sample line**:
```
<hostname> ESTABLISH LOCAL CONNECTION FOR USER: root
```

**Host association**: YES. `host=self._play_context.remote_addr` is passed.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/local.py#L40-L45

---

### Category 19: Local EXEC/PUT/FETCH (caplevel=2, vvv)

**Prefix patterns**:
- `^EXEC ` (local command execution)
- `^PUT .* TO ` (file transfer to remote)
- `^FETCH .* TO ` (file transfer from remote)

**Caplevel**: 2 (vvv). Visible at `-vvv` and above.

**Source**: `local.py`:
```python
# exec_command(), line ~65:
display.vvv(u"EXEC {0}".format(to_text(cmd)), host=self._play_context.remote_addr)

# put_file(), line ~130:
display.vvv(u"PUT {0} TO {1}".format(in_path, out_path), host=self._play_context.remote_addr)

# fetch_file(), line ~145:
display.vvv(u"FETCH {0} TO {1}".format(in_path, out_path), host=self._play_context.remote_addr)
```

**Sample lines**:
```
<hostname> EXEC /bin/sh -c 'echo hello'
<hostname> PUT /tmp/src TO /tmp/dst
<hostname> FETCH /remote/path TO /local/path
```

**Host association**: YES. `host=self._play_context.remote_addr` is passed.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/local.py#L65, L130, L145

---

### Category 20: Local User Detection (`Current user (uid=...)` at caplevel=1, vv)

**Prefix pattern**: `^Current user (uid=\d+) does not seem to exist on this system`

**Caplevel**: 1 (vv). Visible at `-vv` and above.

**Source**: `local.py`, `__init__()` method, line ~30-35:
```python
try:
    self.default_user = getpass.getuser()
except (ImportError, KeyError, OSError):
    display.vv("Current user (uid=%s) does not seem to exist on this system, leaving user empty." % os.getuid())
    self.default_user = ""
```

**Sample line**:
```
Current user (uid=1000) does not seem to exist on this system, leaving user empty.
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/local.py#L30-L35

---

### Category 21: Vault Password Prompts (interactive, to stderr)

**Prefix pattern**: `^Vault password(?: \(.*?\))?: $` or `^New vault password(?: \(.*?\))?: $`

**Caplevel**: Always emitted (not gated by verbosity). Interactive prompt.

**Source**: `parsing/vault/__init__.py`, `PromptVaultSecret.ask_vault_passwords()` method, line ~200-210:
```python
def ask_vault_passwords(self):
    b_vault_passwords = []
    for prompt_format in self.prompt_formats:
        prompt = prompt_format % {'vault_id': self.vault_id}
        try:
            vault_pass = display.prompt(prompt, private=True)
```

And `display.py`, `prompt()` method, line ~530:
```python
@staticmethod
def prompt(msg: str, private: bool = False) -> str:
    if private:
        return getpass.getpass(msg)
    else:
        return input(msg)
```

`getpass.getpass()` writes the prompt string to stderr (this is Python stdlib behavior).

**Sample lines**:
```
Vault password (default):
Vault password:
New vault password (myvault):
Confirm new vault password (myvault):
```

**Host association**: NO. These are interactive prompts.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/parsing/vault/__init__.py#L200-L210

---

### Category 22: Become Password Prompts (interactive, to stderr)

**Prefix pattern**: `^(SSH|BECOME) password(?: \[defaults to SSH password\])?: $`

**Caplevel**: Always emitted (not gated by verbosity). Interactive prompt.

**Source**: `cli/__init__.py`, `ask_passwords()` method, line ~180-195:
```python
@staticmethod
def ask_passwords():
    op = context.CLIARGS
    sshpass = None
    becomepass = None
    become_prompt_method = "BECOME" if C.AGNOSTIC_BECOME_PROMPT else op['become_method'].upper()
    try:
        become_prompt = "%s password: " % become_prompt_method
        if op['ask_pass']:
            sshpass = CLI._get_secret("SSH password: ")
            become_prompt = "%s password[defaults to SSH password]: " % become_prompt_method
```

`CLI._get_secret()` calls `getpass.getpass()` which writes to stderr.

**Sample lines**:
```
SSH password:
BECOME password:
sudo password[defaults to SSH password]:
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/cli/__init__.py#L180-L195

---

### Category 23: Vault Decryption Attempts (`Trying to use vault secret` at vvvvv, caplevel=4)

**Prefix pattern**: `^Trying to use vault secret`

**Caplevel**: 4 (vvvvv). Visible at `-vvvvv` and above.

**Source**: `parsing/vault/__init__.py`, `VaultLib.decrypt_and_get_vault_id()` method, line ~350-360:
```python
display.vvvvv(u'Trying to use vault secret=(%s) id=%s to decrypt %s' % (to_text(vault_secret), to_text(vault_secret_id), to_text(origin)))
```

**Sample line**:
```
Trying to use vault secret=(...) id=default to decrypt <origin>
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/parsing/vault/__init__.py#L350-L360

---

### Category 24: Vault Encryption Details (`Encrypting with vault_id` at vvvvv, caplevel=4)

**Prefix pattern**: `^Encrypting with vault_id`

**Caplevel**: 4 (vvvvv). Visible at `-vvvvv` and above.

**Source**: `parsing/vault/__init__.py`, `VaultLib.encrypt()` method, line ~300-305:
```python
if vault_id:
    display.vvvvv(u'Encrypting with vault_id "%s" and vault secret %s' % (to_text(vault_id), to_text(secret)))
else:
    display.vvvvv(u'Encrypting without a vault_id using vault secret %s' % to_text(secret))
```

**Sample line**:
```
Encrypting with vault_id "default" and vault secret <secret>
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/parsing/vault/__init__.py#L300-L305

---

### Category 25: Vault Decrypt Success (`Decrypt successful with secret` at vvvvv, caplevel=4)

**Prefix pattern**: `^Decrypt.* successful with secret`

**Caplevel**: 4 (vvvvv). Visible at `-vvvvv` and above.

**Source**: `parsing/vault/__init__.py`, `VaultLib.decrypt_and_get_vault_id()` method, line ~370-375:
```python
display.vvvvv(
    u'Decrypt%s successful with secret=%s and vault_id=%s' % (to_text(file_slug), to_text(vault_secret), to_text(vault_secret_id))
)
```

**Sample line**:
```
Decrypt of "file.yml" successful with secret=<secret> and vault_id=default
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/parsing/vault/__init__.py#L370-L375

---

### Category 26: Vault ID Matching (`encrypt_vault_id=` at vvvvv, caplevel=4)

**Prefix pattern**: `^encrypt_vault_id=`

**Caplevel**: 4 (vvvvv). Visible at `-vvvvv` and above.

**Source**: `parsing/vault/__init__.py`, `match_encrypt_vault_id_secret()` method, line ~260:
```python
display.vvvvv(u'encrypt_vault_id=%s' % to_text(encrypt_vault_id))
```

**Sample line**:
```
encrypt_vault_id=myvault
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/parsing/vault/__init__.py#L260

---

### Category 27: Vault Password File Loading (`Reading vault password file` at vvvvv, caplevel=4)

**Prefix pattern**: `^Reading vault password file:`

**Caplevel**: 4 (vvvvv). Visible at `-vvvvv` and above.

**Source**: `cli/__init__.py`, `setup_vault_secrets()` method, line ~150:
```python
display.vvvvv('Reading vault password file: %s' % vault_id_value)
```

**Sample line**:
```
Reading vault password file: /path/to/vault-pass
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/cli/__init__.py#L150

---

### Category 28: Vault Password Script Execution (`The vault password file ... is a client script` at vvvvv, caplevel=4)

**Prefix pattern**: `^The vault password file .* is a (client )?script`

**Caplevel**: 4 (vvvvv). Visible at `-vvvvv` and above.

**Source**: `parsing/vault/__init__.py`, `get_file_vault_secret()` method, line ~230:
```python
display.vvvvv(u'The vault password file %s is a client script.' % to_text(this_path))
```

And `cli/__init__.py`, `get_password_from_file()` method, line ~210:
```python
display.vvvvv(u'The password file %s is a script.' % to_text(pwd_file))
```

**Sample lines**:
```
The vault password file /path/to/vault-pass is a client script.
The password file /path/to/password-script is a script.
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/parsing/vault/__init__.py#L230

---

### Category 29: Plugin Loading Debug (`trying ...` at debug level)

**Prefix pattern**: `^trying ` (from plugin loader path search)

**Caplevel**: Debug (gated by `C.DEFAULT_DEBUG`, not verbosity). Only visible when `ANSIBLE_DEBUG=1` or `DEFAULT_DEBUG=True`.

**Source**: `plugins/loader.py`, `_find_plugin_legacy()` method, line ~350:
```python
display.debug('trying %s' % path)
```

**Sample line**:
```
trying /path/to/plugin/directory
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/loader.py#L350

---

### Category 30: Config File Loading (`Using ... as config file` at caplevel=1, v)

**Prefix pattern**: `^Using .* as config file`

**Caplevel**: 1 (v). Visible at `-v` and above.

**Source**: `cli/__init__.py`, `run()` method, line ~90:
```python
if C.CONFIG_FILE:
    display.v(u"Using %s as config file" % to_text(C.CONFIG_FILE))
else:
    display.v(u"No config file found; using defaults")
```

**Sample lines**:
```
Using /etc/ansible/ansible.cfg as config file
No config file found; using defaults
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/cli/__init__.py#L90

---

### Category 31: Play Count (`N plays in ...` at caplevel=1, vv)

**Prefix pattern**: `^\d+ plays in `

**Caplevel**: 1 (vv). Visible at `-vv` and above.

**Source**: `playbook_executor.py`, `run()` method, line ~80:
```python
display.vv(u'%d plays in %s' % (len(plays), to_text(playbook_path)))
```

**Sample line**:
```
2 plays in site.yml
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/executor/playbook_executor.py#L80

---

### Category 32: Collection Playbook Detection (`running playbook inside collection` at caplevel=0, v)

**Prefix pattern**: `^running playbook inside collection `

**Caplevel**: 0 (v). Visible at `-v` and above.

**Source**: `playbook_executor.py`, `run()` method, line ~65:
```python
if playbook_collection:
    display.v("running playbook inside collection {0}".format(playbook_collection))
```

**Sample line**:
```
running playbook inside collection my.collection
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/executor/playbook_executor.py#L65

---

### Category 33: WorkerProcess Stderr Warnings (errant direct writes)

**Prefix pattern**: `^[WARNING]: WorkerProcess for \[`

**Caplevel**: Always emitted (via `display.warning()`).

**Source**: `executor/process/worker.py`, `_run()` method, line ~120-130:
```python
for name, stdio in (('stdout', sys.stdout), ('stderr', sys.stderr)):
    if data := stdio.getvalue():
        display.warning(
            (
                f'WorkerProcess for [{self._host}/{self._task}] errantly sent data directly to {name} instead of using Display:\n'
                f'{textwrap.indent(data[:256], "    ")}\n'
            ),
            formatted=True
        )
```

**Sample line**:
```
[WARNING]: WorkerProcess for [web1/Task_name] errantly sent data directly to stdout instead of using Display:
    some data
```

**Host association**: YES. The host is embedded in the message: `WorkerProcess for [hostname/task_name]`.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/executor/process/worker.py#L120-L130

---

### Category 34: Retry File Generation (`to retry, use:` at display level)

**Prefix pattern**: `^\tto retry, use: --limit @`

**Caplevel**: Always emitted (via `display.display()`, not gated by verbosity).

**Source**: `playbook_executor.py`, `run()` method, line ~130:
```python
if self._generate_retry_inventory(filename, retries):
    display.display("\tto retry, use: --limit @%s\n" % filename)
```

**Sample line**:
```
	to retry, use: --limit @/path/to/site.retry
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/executor/playbook_executor.py#L130

---

### Category 35: Syntax Check Success (`No issues encountered` at display level)

**Prefix pattern**: `^No issues encountered`

**Caplevel**: Always emitted (via `display.display()`, not gated by verbosity).

**Source**: `playbook_executor.py`, `run()` method, line ~140:
```python
if context.CLIARGS['syntax']:
    display.display("No issues encountered")
```

**Sample line**:
```
No issues encountered
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/executor/playbook_executor.py#L140

---

### Category 36: Host Pattern Mismatch Warnings (`Could not match supplied host pattern`)

**Prefix pattern**: `^Could not match supplied host pattern, ignoring:`

**Caplevel**: Depends on `HOST_PATTERN_MISMATCH` config. Can be debug, warning, or error.

**Source**: `inventory/manager.py`, `_enumerate_matches()` method, line ~280:
```python
if not results and not matching_groups and pattern != 'all':
    msg = "Could not match supplied host pattern, ignoring: %s" % pattern
    display.debug(msg)
    if C.HOST_PATTERN_MISMATCH == 'warning':
        display.warning(msg)
    elif C.HOST_PATTERN_MISMATCH == 'error':
        raise AnsibleError(msg)
```

**Sample line**:
```
[WARNING]: Could not match supplied host pattern, ignoring: nonexistent
```

**Host association**: NO.

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/inventory/manager.py#L280

---

### Category 37: SSH Debug Lines from SSH Client (`debug1: ...`)

**Prefix pattern**: `^debug\d+: `

**Caplevel**: These come from the SSH client itself (via `-vvv` on the SSH command), NOT from ansible. They appear on stderr of the SSH subprocess.

**Source**: `ssh.py`, line ~55:
```python
SSH_DEBUG = re.compile(r'^debug\d+: .*')
```

This regex is defined but only used to filter SSH debug lines from stderr output. The SSH client's stderr is captured by ansible but not re-displayed.

**Note**: These lines are consumed by the SSH connection plugin and are NOT re-emitted to ansible's stderr. They are filtered out. Included here for completeness — they should NOT appear in AOM's stderr stream.

**Host association**: N/A (filtered out by ansible).

**URL**: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/ssh.py#L55

---

### Category 38: JSONL Callback Output (to stdout, NOT stderr)

**Prefix pattern**: `^{` (JSON object)

**Caplevel**: Not gated by verbosity. Always emitted.

**Source**: `ansible.posix.jsonl`, `_write_event()` method:
```python
def _write_event(self, event_name, output):
    output['_event'] = event_name
    output['_timestamp'] = current_time()
    self._display.display(json.dumps(output, cls=AnsibleJSONEncoder, indent=self._json_indent, separators=',:', sort_keys=True))
```

**Important**: This goes to `sys.stdout` (the default for `display()`), NOT stderr. Included here to clarify the boundary: JSONL events are on stdout, everything else in this taxonomy is on stderr.

**Host association**: YES (embedded in the JSON structure under `hosts` key).

**URL**: https://github.com/ansible-collections/ansible.posix/blob/main/plugins/callback/jsonl.py#L120-L125

---

## Section 2: Summary Table — All stderr Categories

| # | Category | Prefix Pattern | Caplevel | Verbosity | Host? | Source File |
|---|----------|---------------|----------|-----------|-------|------------|
| 1 | Warnings | `[WARNING]:` | -2 | always | No | display.py |
| 2 | Deprecation Warnings | `[DEPRECATION WARNING]:` | none | always (gated by config) | No | display.py |
| 3 | Errors | `[ERROR]:` | -1 | always | No | display.py |
| 4 | Preflight Errors | `ERROR:` (no brackets) | none | always | No | cli/__init__.py |
| 5 | CLI Errors | `[ERROR]:` | -1 | always | No | cli/__init__.py |
| 6 | SSH Debug | `SSH:` | 4 | -vvvvv | Yes | ssh.py |
| 7 | SSH Agent | `SSH: SSH_AGENT` | 2 | -vvv | Yes | ssh.py |
| 8 | SSH Connection Errors | `Failed to connect to the host via ssh:` | 2 | -vvv | Yes | ssh.py |
| 9 | SSH Retry | `ssh_retry: attempt:` | 1 | -vv | Yes | ssh.py |
| 10 | SSH Return Code | `rc=` | 2 | -vvv | Yes | ssh.py |
| 11 | ControlPersist Broken Pipe | `RETRYING BECAUSE OF CONTROLPERSIST BROKEN PIPE` | 2 | -vvv | No | ssh.py |
| 12 | Connection Lock | `CONNECTION: pid` | 3 | -vvvv | Yes | connection/__init__.py |
| 13 | Persistent Connection Reset | `resetting persistent connection` | 3 | -vvvv | Indirect | connection/__init__.py |
| 14 | Callback Loading | `Loading callback plugin` | 3 | -vvvv | No | callback/__init__.py |
| 15 | Inventory Plugin Setup | `setting up inventory plugins` | 3 | -vvvv | No | inventory/manager.py |
| 16 | Inventory Parsed | `Parsed .* inventory source` | 2 | -vvv | No | inventory/manager.py |
| 17 | Inventory Declined | `declined parsing` | 2 | -vvv | No | inventory/manager.py |
| 18 | Local Connection | `ESTABLISH LOCAL CONNECTION FOR USER:` | 2 | -vvv | Yes | local.py |
| 19 | Local EXEC/PUT/FETCH | `EXEC` / `PUT` / `FETCH` | 2 | -vvv | Yes | local.py |
| 20 | Local User Detection | `Current user (uid=` | 1 | -vv | No | local.py |
| 21 | Vault Password Prompt | `Vault password` | none | always (interactive) | No | vault/__init__.py |
| 22 | Become/SSH Password Prompt | `SSH password:` / `BECOME password:` | none | always (interactive) | No | cli/__init__.py |
| 23 | Vault Decrypt Attempt | `Trying to use vault secret` | 4 | -vvvvv | No | vault/__init__.py |
| 24 | Vault Encrypt Details | `Encrypting with vault_id` | 4 | -vvvvv | No | vault/__init__.py |
| 25 | Vault Decrypt Success | `Decrypt.* successful with secret` | 4 | -vvvvv | No | vault/__init__.py |
| 26 | Vault ID Matching | `encrypt_vault_id=` | 4 | -vvvvv | No | vault/__init__.py |
| 27 | Vault Password File | `Reading vault password file:` | 4 | -vvvvv | No | cli/__init__.py |
| 28 | Vault Password Script | `The vault password file .* is a` | 4 | -vvvvv | No | vault/__init__.py |
| 29 | Plugin Loading Debug | `trying ` | debug | ANSIBLE_DEBUG | No | plugins/loader.py |
| 30 | Config File | `Using .* as config file` | 1 | -v | No | cli/__init__.py |
| 31 | Play Count | `\d+ plays in ` | 1 | -vv | No | playbook_executor.py |
| 32 | Collection Playbook | `running playbook inside collection` | 0 | -v | No | playbook_executor.py |
| 33 | WorkerProcess Warning | `WorkerProcess for [` | -2 | always | Yes (in msg) | executor/process/worker.py |
| 34 | Retry File | `to retry, use:` | none | always | No | playbook_executor.py |
| 35 | Syntax Check OK | `No issues encountered` | none | always | No | playbook_executor.py |
| 36 | Host Pattern Mismatch | `Could not match supplied host pattern` | varies | varies | No | inventory/manager.py |

---

## Section 3: Proposed `source` Enum for AOM Classifier

The classifier needs 10 source values. This balances granularity (distinguishing run-level from task-level) with simplicity (not having 36 separate values).

```python
class StderrSource(str, enum.Enum):
    WARNING = "warning"              # [WARNING]: lines
    DEPRECATION = "deprecation"      # [DEPRECATION WARNING]: lines
    ERROR = "error"                  # [ERROR]: lines (including preflight ERROR:)
    SSH_DEBUG = "ssh_debug"          # SSH: lines (vvvvv SSH arg explanations)
    SSH_INFO = "ssh_info"            # SSH: SSH_AGENT, Failed to connect, rc=, ssh_retry:, RETRYING
    CONNECTION = "connection"        # CONNECTION: pid, ESTABLISH LOCAL, EXEC, PUT, FETCH
    CONNECTION_LIFECYCLE = "connection_lifecycle"  # resetting persistent connection, reset call
    PLUGIN_LOADING = "plugin_loading"  # Loading callback plugin, setting up inventory plugins
    INVENTORY = "inventory"          # Parsed ... inventory source, declined parsing
    VAULT = "vault"                  # Vault password prompts, vault debug messages
    PROMPT = "prompt"                # SSH password:, BECOME password: prompts
    RUN_LEVEL = "run_level"          # Everything else: play count, config file, retry file, etc.
```

### Run-level vs Task-level Distinction

For the inspect TUI's `V` keybind filtering:

| Source | Level | Description |
|--------|-------|-------------|
| `warning` | run-level | Warnings about inventory, plugins, config |
| `deprecation` | run-level | Deprecation notices |
| `error` | run-level | Fatal errors |
| `ssh_debug` | task-level | Per-host SSH argument debugging |
| `ssh_info` | task-level | Per-host SSH connection info |
| `connection` | task-level | Per-host connection lifecycle |
| `connection_lifecycle` | task-level | Per-host persistent connection reset |
| `plugin_loading` | run-level | Plugin loading diagnostics |
| `inventory` | run-level | Inventory parsing diagnostics |
| `vault` | run-level | Vault operations |
| `prompt` | run-level | Interactive password prompts |
| `run_level` | run-level | Miscellaneous diagnostics |

---

## Section 4: Regex Table for the Classifier

The classifier should try these regexes in order. First match wins.

```python
CLASSIFIER_RULES: list[tuple[str, re.Pattern, bool]] = [
    # (source, regex, has_host)
    
    # 1. Warnings (most common, check first)
    ("warning", re.compile(r'^\[WARNING\]: '), False),
    
    # 2. Deprecation warnings
    ("deprecation", re.compile(r'^\[DEPRECATION WARNING\]: '), False),
    
    # 3. Errors
    ("error", re.compile(r'^\[ERROR\]: '), False),
    
    # 4. Preflight errors (unbracketed ERROR:)
    ("error", re.compile(r'^ERROR: '), False),
    
    # 5. SSH debug (vvvvv) — host-prefixed: <hostname> SSH: ...
    ("ssh_debug", re.compile(r'^(?:<([^>]+)> )?SSH: '), True),
    
    # 6. SSH agent operations
    ("ssh_info", re.compile(r'^(?:<([^>]+)> )?SSH: SSH_AGENT '), True),
    
    # 7. SSH connection errors
    ("ssh_info", re.compile(r'^(?:<([^>]+)> )?Failed to connect to the host via ssh:'), True),
    
    # 8. SSH retry messages
    ("ssh_info", re.compile(r'^(?:<([^>]+)> )?ssh_retry: attempt:'), True),
    
    # 9. SSH return code
    ("ssh_info", re.compile(r'^(?:<([^>]+)> )?rc='), True),
    
    # 10. ControlPersist broken pipe
    ("ssh_info", re.compile(r'^RETRYING BECAUSE OF CONTROLPERSIST BROKEN PIPE'), False),
    
    # 11. Connection lock messages
    ("connection", re.compile(r'^(?:<([^>]+)> )?CONNECTION: pid \d+ (?:waiting for|acquired|released) lock on \d+'), True),
    
    # 12. Local connection establishment
    ("connection", re.compile(r'^(?:<([^>]+)> )?ESTABLISH LOCAL CONNECTION FOR USER:'), True),
    
    # 13. Local EXEC/PUT/FETCH
    ("connection", re.compile(r'^(?:<([^>]+)> )?(?:EXEC |PUT .* TO |FETCH .* TO )'), True),
    
    # 14. Persistent connection reset
    ("connection_lifecycle", re.compile(r'^resetting persistent connection for socket_path'), False),
    ("connection_lifecycle", re.compile(r'^reset call on connection instance'), False),
    
    # 15. Callback loading
    ("plugin_loading", re.compile(r'^Loading callback plugin '), False),
    
    # 16. Inventory plugin setup
    ("plugin_loading", re.compile(r'^setting up inventory plugins'), False),
    
    # 17. Inventory parsed
    ("inventory", re.compile(r'^Parsed .* inventory source with .* plugin'), False),
    
    # 18. Inventory declined
    ("inventory", re.compile(r'^.* declined parsing .* as it did not pass its verify_file'), False),
    
    # 19. Vault password prompts
    ("vault", re.compile(r'^Vault password'), False),
    ("vault", re.compile(r'^New vault password'), False),
    
    # 20. Vault debug messages
    ("vault", re.compile(r'^(?:Trying to use vault secret|Encrypting with vault_id|Decrypt.* successful with secret|encrypt_vault_id=|Reading vault password file|The vault password file .* is a)'), False),
    
    # 21. Become/SSH password prompts
    ("prompt", re.compile(r'^(?:SSH|BECOME|sudo) password'), False),
    
    # 22. WorkerProcess warnings (host embedded in message)
    ("warning", re.compile(r'^\[WARNING\]: WorkerProcess for \['), False),
    
    # 23. Config file
    ("run_level", re.compile(r'^Using .* as config file'), False),
    ("run_level", re.compile(r'^No config file found'), False),
    
    # 24. Play count
    ("run_level", re.compile(r'^\d+ plays in '), False),
    
    # 25. Collection playbook
    ("run_level", re.compile(r'^running playbook inside collection '), False),
    
    # 26. Retry file
    ("run_level", re.compile(r'^\tto retry, use:'), False),
    
    # 27. Syntax check
    ("run_level", re.compile(r'^No issues encountered'), False),
    
    # 28. Host pattern mismatch
    ("run_level", re.compile(r'^Could not match supplied host pattern'), False),
    
    # 29. Current user detection
    ("run_level", re.compile(r'^Current user \(uid='), False),
    
    # 30. Plugin loading debug
    ("run_level", re.compile(r'^trying '), False),
]
```

### Host Extraction Logic

When `has_host` is `True` and the regex has a capture group `([^>]+)` after `<`:
- If the line starts with `<hostname>`, extract the hostname from the capture group
- If the line does NOT have a `<hostname>` prefix, the host is `None` (run-level)

The regex `^(?:<([^>]+)> )?` handles both cases:
- `<web1> SSH: ...` → host = `web1`
- `SSH: ...` (no prefix) → host = `None`

### Level Mapping

```python
LEVEL_MAP = {
    "warning": "warning",
    "deprecation": "warning",
    "error": "error",
    "ssh_debug": "debug",
    "ssh_info": "info",
    "connection": "debug",
    "connection_lifecycle": "debug",
    "plugin_loading": "debug",
    "inventory": "info",
    "vault": "info",
    "prompt": "info",
    "run_level": "info",
}
```

---

## Section 5: Open Questions

1. **`VERBOSE_TO_STDERR=False` edge case**: If a user sets `VERBOSE_TO_STDERR=False`, ALL verbose output (categories 6-20, 23-29) goes to stdout instead of stderr. AOM would miss these entirely. Should AOM document this assumption or handle it?

2. **`display.debug()` goes to stdout**: The `debug()` method (display.py line ~380) writes to stdout, not stderr. Debug messages like `trying /path/to/plugin` (category 29) would appear on stdout. But they're gated by `C.DEFAULT_DEBUG`, not verbosity. Should AOM capture debug messages from stdout?

3. **`banner()` goes to stdout**: The `banner()` method (display.py line ~400) writes to stdout. This includes `PLAY [name] ********` and `TASK [name] ********` headers. These are NOT on stderr. The JSONL callback handles these via `v2_playbook_on_play_start` and `v2_playbook_on_task_start` events.

4. **`screen_only` parameter**: Some `display()` calls use `screen_only=True` which means they go to screen but NOT to the log file. This doesn't affect stdout/stderr routing but is relevant for understanding what appears where.

5. **Deduplication**: `_warning()`, `_deprecated()`, and `_error()` all deduplicate their messages. The same warning text is only emitted once per run. This means the classifier may see fewer lines than the number of `warning()` calls.

6. **`error_as_warning()`**: This method (display.py line ~480) converts exceptions to `[WARNING]:` lines. The classifier cannot distinguish these from regular warnings — they share the same prefix.

7. **`system_warning()`**: This method (display.py line ~475) calls `warning()` only if `C.SYSTEM_WARNINGS` is True. Same prefix as regular warnings.

8. **Persistent connection reset host extraction**: The `resetting persistent connection` and `reset call on connection instance` messages (category 13) are queued via `queue_message()` and dispatched by the controller. The host is NOT in the message text. The classifier would need to track which host the connection instance belongs to, or accept that host is `None` for these lines.

9. **SSH debug lines from SSH client**: The SSH client's own debug output (lines starting with `debug1:`, `debug2:`, etc.) are filtered by ansible's `SSH_DEBUG` regex and NOT re-emitted. But if the SSH client writes other unexpected output to stderr, it could leak through. The classifier should have a catch-all `unknown` source for unclassifiable lines.

10. **JSONL callback output is on stdout**: The `ansible.posix.jsonl` callback writes all events to stdout via `self._display.display(json.dumps(...))`. This is the primary data stream AOM parses. The stderr stream is supplementary — it contains warnings, errors, and verbose debug output that the JSONL callback does NOT capture.

11. **`_run_is_verbose` in default callback**: The default callback uses `self._run_is_verbose(result)` which checks `self._display.verbosity > verbosity` (default verbosity=0). When `-v` is used, task results include the full result dump. This is a different mechanism from `Display.v*()` — it's the callback adding detail to its own output, not a separate verbose line on stderr.

12. **`--list-tasks` and `--list-hosts` output**: These go to stdout, not stderr. They are plain text (not JSON). AOM already handles these separately in the preflight phase.

13. **Password prompts are interactive**: The `getpass.getpass()` function writes the prompt to stderr and reads the password from `/dev/tty`. In a PTY context (which AOM uses), these prompts appear on the PTY's output stream. AOM's `PtyStreamParser` already has a `PRE_RUN_PROMPTS` phase for handling these. The stderr classifier should recognize them but may not need to emit `aom_stderr_line` events for them since they're handled by the prompt detection phase.

14. **The `@_proxy` decorator and worker processes**: When `_final_q` is set (in `WorkerProcess`), display calls are proxied through the queue. The parent process then executes the actual write to stderr. This means verbose lines from worker processes arrive asynchronously and may be interleaved with other output. AOM's PTY parser must handle this interleaving — but since AOM uses a single PTY, all output (from both parent and worker processes) arrives on the same stream in order.

---

## Appendix: Quick Reference — Host Extraction

| Source | Has Host? | Extraction Pattern |
|--------|-----------|-------------------|
| `warning` | No | N/A |
| `deprecation` | No | N/A |
| `error` | No | N/A |
| `ssh_debug` | Yes | `<([^>]+)> SSH:` |
| `ssh_info` | Yes | `<([^>]+)> (SSH: SSH_AGENT\|Failed to connect\|ssh_retry:\|rc=)` |
| `connection` | Yes | `<([^>]+)> (CONNECTION:\|ESTABLISH\|EXEC\|PUT\|FETCH)` |
| `connection_lifecycle` | No (indirect) | N/A — host not in message text |
| `plugin_loading` | No | N/A |
| `inventory` | No | N/A |
| `vault` | No | N/A |
| `prompt` | No | N/A |
| `run_level` | No | N/A |
