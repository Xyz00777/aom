# Connection ID Feasibility Report

**Date**: 2026-06-30
**Source**: ansible-core v2.20.4 (tag `v2.20.4`)
**Purpose**: Determine whether `pid` + lock counter from `CONNECTION:` messages can serve as a `connection_id` for grouping stderr lines in AOM.

---

## 1. Are `CONNECTION: pid X acquired lock on Y` messages always paired with `pid X released lock on Y`?

**Answer: No, not guaranteed.** There are several scenarios where a lock is acquired but never released.

### Evidence

The lock/unlock methods are defined in `ConnectionBase`:

- **`connection_lock()`** — calls `fcntl.lockf(f, fcntl.LOCK_EX)` then emits `CONNECTION: pid %d acquired lock on %d`
- **`connection_unlock()`** — calls `fcntl.lockf(f, fcntl.LOCK_UN)` then emits `CONNECTION: pid %d released lock on %d`

Source: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/__init__.py#L131-L140

### Where are they called?

**CRITICAL FINDING**: `connection_lock()` and `connection_unlock()` are **NOT called anywhere in ansible-core v2.20.4**. They are defined as public methods on `ConnectionBase` but have zero call sites in the core codebase. They appear to be vestigial or intended for third-party connection plugins.

The lock file descriptor (`connection_lockfd`) is set in `PlayContext.__init__()` from `TaskQueueManager._connection_lockfile`:

Source: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/playbook/play_context.py#L80-L81
Source: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/executor/task_queue_manager.py#L131-L132

But nothing ever calls `connection_lock()` or `connection_unlock()` on the connection object.

### Scenarios where lock would be lost

Even if a caller did use these methods:

1. **Worker process crash** — `WorkerProcess._hard_exit()` calls `os._exit(1)` directly, which does not run any cleanup. Any held lock is released by the OS (file descriptor is closed on process exit), but the `released lock on` message would never be emitted.

2. **Exception in task execution** — `TaskExecutor.run()` has a `finally` block that calls `self._connection.close()`, but `close()` does NOT call `connection_unlock()`. The lock is released by the OS when the fd closes, but no `released` message is emitted.

3. **`os._exit()` in worker** — `WorkerProcess._hard_exit()` and `WorkerProcess._term()` both call `os._exit(1)`, which bypasses all Python cleanup.

### Verdict
The `CONNECTION:` lock messages are **not reliable as a pairing mechanism**. The `acquired` message may appear without a matching `released` message. Furthermore, since the methods are never called in core, these messages may not appear at all in standard ansible-playbook runs.

---

## 2. Is the lock counter Y unique within a run?

**Answer: Yes, it is unique within a single playbook run.** But the mechanism is simpler than expected.

### Evidence

The lock counter is the **file descriptor number** of the connection lockfile. It is created once in `TaskQueueManager.__init__()`:

```python
self._connection_lockfile = tempfile.TemporaryFile()
```

Source: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/executor/task_queue_manager.py#L131-L132

This single `TemporaryFile` is opened **once** in the parent process. Its file descriptor is then passed to `PlayContext`:

```python
play_context = PlayContext(new_play, self.passwords, self._connection_lockfile.fileno())
```

Source: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/executor/task_queue_manager.py#L175

The `PlayContext` stores it as `connection_lockfd`:

```python
self.connection_lockfd = connection_lockfd
```

Source: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/playbook/play_context.py#L80-L81

### Key implications

- The lock counter is a **single file descriptor number** (e.g., `3`, `4`, `5`), not a per-connection counter.
- It is the **same fd number** for all connections in the run, because `PlayContext` is copied (via `copy()`) to each worker, and the fd is inherited across `fork()`.
- The fd number is **not unique per connection** — it's the same value for every `CONNECTION:` message in the entire run.
- The fd number is **not unique across runs** — it depends on which fds are open when `TemporaryFile()` is created.

### Verdict
The lock counter Y is **not useful as a connection identifier**. It is a single global fd number, not a per-connection counter. Two different connections on the same host will show the same lock counter.

---

## 3. Are SSH debug lines (`<hostname> SSH: ...`) emitted from the same process as `CONNECTION:` lock messages?

**Answer: Yes, they are emitted from the same process — the WorkerProcess.** But the `CONNECTION:` messages are never actually emitted in v2.20.4 (see Q1).

### Evidence

Both message types go through the same `Display` singleton, which is proxied via `_final_q` in worker processes.

**SSH debug lines** come from `Connection._add_args()` in `ssh.py`:

```python
def _add_args(self, b_command, b_args, explanation):
    display.vvvvv(u'SSH: %s: (%s)' % (explanation, ')('.join(to_text(a) for a in b_args)), host=self.host)
    b_command += b_args
```

Source: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/ssh.py#L283-L291

This is called from `_build_command()` (same file, lines ~300-450), which is called from `exec_command()`, `put_file()`, and `fetch_file()`.

**CONNECTION lines** would come from `ConnectionBase.connection_lock()` and `connection_unlock()` in `__init__.py`:

```python
def connection_lock(self):
    f = self._play_context.connection_lockfd
    display.vvvv('CONNECTION: pid %d waiting for lock on %d' % (os.getpid(), f), host=self._play_context.remote_addr)
    fcntl.lockf(f, fcntl.LOCK_EX)
    display.vvvv('CONNECTION: pid %d acquired lock on %d' % (os.getpid(), f), host=self._play_context.remote_addr)
```

Source: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/__init__.py#L131-L135

### Process boundary

Both are called from within the **WorkerProcess** (not the main process). The call chain is:

```
StrategyBase._queue_task()
  -> WorkerProcess.start()          # fork happens here
    -> WorkerProcess.run()
      -> WorkerProcess._run()
        -> TaskExecutor.run()
          -> TaskExecutor._execute()
            -> TaskExecutor._execute_internal()
              -> self._handler.run()   # ActionBase subclass
                -> self._connection.exec_command()  # ssh.py
                  -> self._build_command()
                    -> self._add_args()     # emits SSH: lines
```

Source: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/executor/process/worker.py#L97-L120
Source: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/executor/task_executor.py#L1-L50

### Display proxy mechanism

In `WorkerProcess.run()`, `display.set_queue(self._final_q)` is called:

```python
def run(self):
    display.set_queue(self._final_q)
    ...
```

Source: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/executor/process/worker.py#L112

This sets `Display._final_q`, which causes all `display.vvvvv()` and `display.vvvv()` calls to be **proxied over the queue** to the parent process, where `results_thread_main()` in `StrategyBase` processes them:

```python
elif isinstance(result, DisplaySend):
    dmethod = getattr(display, result.method)
    dmethod(*result.args, **result.kwargs)
```

Source: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/strategy/__init__.py#L72-L74

### The `pid` in CONNECTION messages

The `pid` is `os.getpid()` called from within the WorkerProcess. This is the **worker process PID**, not the main ansible-playbook PID. The `_proxy` decorator on `Display.vvvvv()` and `Display.vvvv()` means the display call is serialized into a `DisplaySend` object and put on the queue. The actual `display.vvvvv()` call happens in the parent's `results_thread_main()`, but the `pid` was already captured in the message string by the worker.

### Verdict
Both `SSH:` and `CONNECTION:` lines are emitted from the same WorkerProcess. The `pid` in both cases is `os.getpid()` from the worker. They are in the **same process boundary**.

---

## 4. Is the `pid` consistent within a connection's lifetime?

**Answer: Yes, within a single task execution.** But a connection may be reused across multiple tasks, and the pid is the worker PID, not the connection PID.

### Evidence

Each `WorkerProcess` is a single OS process (forked from the main process). Its PID is fixed for its lifetime. A single `WorkerProcess` can execute multiple tasks sequentially (the strategy reuses workers).

However, the connection object is **not necessarily reused** across tasks. In `TaskExecutor._execute_internal()`:

```python
if (not self._connection or
        not getattr(self._connection, 'connected', False) or
        not self._connection.matches_name([current_connection]) or
        self._play_context.remote_addr != self._connection._play_context.remote_addr):
    self._connection = self._get_connection(cvars, templar, current_connection)
else:
    # if connection is reused...
    self._connection._play_context = self._play_context
```

Source: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/executor/task_executor.py#L340-L350

The connection is reused only if:
1. It's still connected
2. The connection type matches
3. The remote address matches

For SSH connections, `_connect()` is a no-op (returns `self`), so the connection is "always connected" once created. This means the same `Connection` object can be reused across multiple tasks on the same host within the same worker.

### The `pid` is the worker PID

Since `os.getpid()` is called in the worker, and the worker PID is constant, the `pid` in `CONNECTION:` messages would be the same for all tasks executed by that worker. But since `connection_lock()` is never called (see Q1), this is moot.

### Verdict
The `pid` is consistent within a worker's lifetime, but it identifies the **worker process**, not the connection instance. Multiple connections (e.g., different hosts) handled by the same worker would show the same pid.

---

## 5. For the local connection plugin, what does the connection lifecycle look like?

**Answer**: The local connection plugin (`local.py`) has a trivial lifecycle. It does NOT emit any `CONNECTION:` lines because `connection_lock()` is never called.

### Evidence

`local.py` `_connect()`:

```python
def _connect(self):
    self._play_context.remote_user = self.default_user
    if not self._connected:
        display.vvv(u"ESTABLISH LOCAL CONNECTION FOR USER: %s" % self._play_context.remote_user, host=self._play_context.remote_addr)
        self._connected = True
    return self
```

Source: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/local.py#L56-L62

`local.py` `close()`:

```python
def close(self):
    self._connected = False
```

Source: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/local.py#L175-L177

The local connection:
- Does NOT call `connection_lock()` or `connection_unlock()`
- Does NOT emit any `CONNECTION:` messages
- Does NOT emit any `SSH:` messages (it has no `_add_args()` method)
- Emits `ESTABLISH LOCAL CONNECTION FOR USER:` at `vvv` level (caplevel 2)
- Emits `EXEC` at `vvv` level for each command
- Emits `PUT` / `FETCH` at `vvv` level for file transfers

### Verdict
For `connection: local`, there are no `CONNECTION:` or `SSH:` debug lines at any verbosity level. The local connection is trivially "connected" on first use and "disconnected" on close.

---

## 6. For persistent connections (ControlPersist), does the SSH debug line come from the ansible process or the SSH client process?

**Answer**: The SSH debug lines come from the **ansible WorkerProcess**, not from the SSH client process. The `SSH:` prefix is added by ansible's `_add_args()` method, which runs in the Python process before `subprocess.Popen()` is called.

### Evidence

The `_add_args()` method in `ssh.py`:

```python
def _add_args(self, b_command, b_args, explanation):
    display.vvvvv(u'SSH: %s: (%s)' % (explanation, ')('.join(to_text(a) for a in b_args)), host=self.host)
    b_command += b_args
```

Source: https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/ssh.py#L283-L291

This is called from `_build_command()`, which builds the argument list for `subprocess.Popen()`. The `SSH:` line is emitted **before** the SSH subprocess is spawned. It documents what arguments ansible is adding to the SSH command.

The actual SSH client process (started by `subprocess.Popen()`) may emit its own debug lines (e.g., `debug1: ...`) if `-v` flags are passed, but those come from the SSH client's stderr, not from ansible's display system. Those raw SSH client debug lines would appear in the stderr output captured by `pexpect`/`subprocess`, not as `SSH:` prefixed lines.

### ControlPersist implications

With ControlPersist, the SSH client process may connect to an existing control master socket. The `SSH:` debug lines from ansible are still emitted by the WorkerProcess before the SSH command is constructed. The actual SSH client's debug output (if any) would be mixed into the command's stderr.

### Verdict
The `SSH:` prefixed lines are always from the ansible WorkerProcess, never from the SSH client. The `pid` in any `CONNECTION:` message would match the WorkerProcess PID, not the SSH client PID.

---

## 7. Overall Feasibility Assessment

### Can `pid` + lock counter serve as a `connection_id`?

**No.** Here's why:

1. **`connection_lock()` / `connection_unlock()` are never called** in ansible-core v2.20.4. The `CONNECTION:` messages will not appear in standard playbook runs. They are defined but have zero call sites.

2. **The lock counter is a single global fd number**, not a per-connection counter. All connections in a run share the same fd.

3. **The `pid` identifies the worker process**, not the connection instance. A single worker can handle multiple connections (different hosts, or reconnections to the same host).

### Alternative approaches for `connection_id`

Since the `CONNECTION:` messages are unreliable/absent, here are alternatives:

| Approach | Pros | Cons |
|----------|------|------|
| **Worker PID** (`os.getpid()` from stderr line context) | Available; stable per worker | Doesn't distinguish multiple connections in same worker; not in stderr text itself |
| **Task UUID** (`task._uuid`) | Unique per task; available in JSONL events | Not in stderr text; requires cross-referencing JSONL events |
| **Host + timestamp window** | Simple; no code changes | Imprecise; overlapping connections ambiguous |
| **Inject a connection ID into the SSH command** | Would appear in SSH debug output | Requires patching ansible-core; fragile |
| **Parse SSH ControlPath from stderr** | ControlPath is host+port+user unique | Not always present; format varies |

### Recommendation

**Do not add `connection_id` to the v1 schema.** The `CONNECTION:` messages are not emitted by ansible-core, so there is no reliable signal to extract a connection identifier from stderr text alone.

If connection grouping is critical, the most viable approach is to **cross-reference stderr lines with JSONL events** using timestamps and host names. Each `aom_stderr_line` event already carries `host` and `_timestamp`. The JSONL event stream provides `task._uuid` and `host`. A heuristic that groups stderr lines by `(host, task_uuid)` would work for most cases, though it would fail for `strategy: free` where multiple tasks on the same host overlap in time.

For a future v2, consider:
- Adding a `connection_id` to the JSONL callback output (requires ansible-core patch or custom callback)
- Using `task._uuid` as a proxy for connection identity (imperfect but better than nothing)
- Documenting the limitation for `strategy: free` + `async:` combinations

---

## Source Code References

| File | URL | Key Lines |
|------|-----|-----------|
| `connection/__init__.py` | https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/__init__.py | L131-140 (connection_lock/unlock) |
| `connection/ssh.py` | https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/ssh.py | L283-291 (_add_args), L300-450 (_build_command) |
| `connection/local.py` | https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/connection/local.py | L56-62 (_connect), L175-177 (close) |
| `executor/task_queue_manager.py` | https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/executor/task_queue_manager.py | L131-132 (lockfile creation), L175 (pass to PlayContext) |
| `executor/process/worker.py` | https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/executor/process/worker.py | L97-120 (run/_run), L112 (set_queue) |
| `executor/task_executor.py` | https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/executor/task_executor.py | L340-350 (connection reuse logic) |
| `playbook/play_context.py` | https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/playbook/play_context.py | L80-81 (connection_lockfd) |
| `utils/display.py` | https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/utils/display.py | L200-230 (_proxy decorator), L112 (set_queue) |
| `plugins/strategy/__init__.py` | https://github.com/ansible/ansible/blob/v2.20.4/lib/ansible/plugins/strategy/__init__.py | L72-74 (results_thread_main DisplaySend handling) |
