# Integration Test Playbooks Plan for ansible-aom

> Version 1.0 — 2026-04-24
> Companion document to SPECIFICATION.md v1.8

## Overview

This document defines **12 integration test playbooks** that exercise ALL features of the AOM (Ansible Output Monitor) tool. Each playbook is designed to trigger specific event types, state transitions, and edge cases documented in SPECIFICATION.md.

Each playbook is a **YAML design outline** — actual playbook files would be created separately during implementation testing.

---

## Coverage Matrix

| Playbook | Primary Events | States Tested | Exit Code | Key Features |
|----------|----------------|---------------|-----------|--------------|
| 1. Happy Path | `v2_runner_on_ok` | IDLE→RUNNING→COMPLETED | 0 | Basic flow, completed state |
| 2. Multi-Play Multi-Host | `v2_runner_on_ok`, `v2_runner_on_changed` | Multi-play transitions | 0 | Multiple hosts, changed detection |
| 3. Failure Scenarios | `v2_runner_on_failed` | RUNNING→FAILED | 1 | Failure handling, `ignore_errors` |
| 4. Unreachable Host | `v2_runner_on_unreachable` | RUNNING→FAILED | 2 | Unreachable state detection |
| 5. Role-Based | `v2_playbook_on_task_start` | Role grouping display | 0 | RoleGroup creation (5+ tasks) |
| 6. Handlers & Conditionals | `v2_playbook_on_handler_task_start`, `v2_runner_on_skipped` | Handler lifecycle | 0 | Handlers, `when`, loops |
| 7. Vault & Become | Password prompts | PRE_RUN_PROMPTS phase | 0 | Password handling, vault |
| 8. Deprecation & Warnings | Plaintext warnings | Warning classification | 0 | WarningEntry detection |
| 9. Large Scale | All events | Memory bounds (50K lines) | 0 | Performance, MAX_LOG_LINES |
| 10. Syntax Error | None (pre-run) | LOADING_TASKS→CRASHED | 4 | Syntax error handling |
| 11. Include/Import | Dynamic tasks | Task expansion | 0 | `include_tasks`, dynamic tasks |
| 12. Interrupt & Signals | Signal handling | RUNNING→IDLE (SIGTERM) | 130 | SIGINT forwarding, SIGTERM |

---

## Playbook 1: Happy Path - Simple Single Play

### Purpose
Test the basic success flow with a single play, single host, and all successful tasks.

### YAML Structure (Outline)
```yaml
---
- name: Happy Path Play
  hosts: localhost
  gather_facts: false
  
  tasks:
    - name: Task 1 - Debug message
      ansible.builtin.debug:
        msg: "This task always succeeds"
      
    - name: Task 2 - Create temp file
      ansible.builtin.tempfile:
        state: file
      register: temp_file
      
    - name: Task 3 - Write to file
      ansible.builtin.copy:
        dest: "{{ temp_file.path }}"
        content: "Test content"
        
    - name: Task 4 - Stat file
      ansible.builtin.stat:
        path: "{{ temp_file.path }}"
        
    - name: Task 5 - Cleanup
      ansible.builtin.file:
        path: "{{ temp_file.path }}"
        state: absent
```

### Expected AOM Events (In Order)
1. `v2_playbook_on_start` — Playbook begins
2. `v2_playbook_on_play_start` — Play starts (play.id=UUID, name="Happy Path Play")
3. `v2_playbook_on_task_start` — Each task (5 events, linear strategy detected)
4. `v2_runner_on_ok` — Each task completes successfully (5 events, one per task)
5. `v2_playbook_on_stats` — Final statistics

### Expected Final State
- `RunState.status = COMPLETED`
- 5 tasks with status `OK`
- 1 host (`localhost`) with all tasks `ok`
- Final stats: `{"localhost": {"ok": 5, "changed": 3, "failures": 0, "skipped": 0, "unreachable": 0}}`

### Expected Exit Code
`0` — Successful playbook execution

### Features Tested (SPEC Mapping)
| Feature | Spec Section |
|---------|-------------|
| JSONL event parsing | 5.1 |
| Task matching by UUID | 5.2, 6.1 |
| Status `OK` | 6.1 |
| `v2_runner_on_ok` handler | 6.2 |
| State `COMPLETED` | 6.4 |
| Exit code 0 | 3.4 |
| `--list-tasks` pre-parse | 5.2, 5.3 |
| `--list-hosts` resolution | 5.2.1 |

### Edge Cases Covered
- Single host (localhost)
- No roles, no handlers
- All tasks succeed
- Changed vs OK detection (some tasks change, some don't)

---

## Playbook 2: Multi-Play Multi-Host

### Purpose
Test multi-play execution with different host groups and mixed task statuses.

### YAML Structure (Outline)
```yaml
---
- name: Play 1 - Webserver Setup
  hosts: web1,web2
  gather_facts: false
  
  tasks:
    - name: Install package (changed)
      ansible.builtin.package:
        name: nginx
        state: present
      # First run: changed, subsequent: ok
      
    - name: Start service (ok)
      ansible.builtin.service:
        name: nginx
        state: started
        
    - name: Create config (changed)
      ansible.builtin.copy:
        dest: /tmp/nginx.conf
        content: "server { listen 80; }"
        
- name: Play 2 - Database Setup  
  hosts: db1
  gather_facts: false
  
  tasks:
    - name: Install database
      ansible.builtin.package:
        name: postgresql
        state: present
        
    - name: Initialize database
      ansible.builtin.command:
        cmd: echo "initialized"
      changed_when: true
      
- name: Play 3 - Finalization
  hosts: all
  gather_facts: false
  
  tasks:
    - name: Gather facts (skipped on some)
      ansible.builtin.setup:
      when: inventory_hostname in ['web1', 'db1']
      
    - name: Final task (all hosts)
      ansible.builtin.debug:
        msg: "Playbook complete"
```

### Inventory Required
```ini
[webservers]
web1 ansible_host=127.0.0.1 ansible_connection=local
web2 ansible_host=127.0.0.1 ansible_connection=local

[databases]
db1 ansible_host=127.0.0.1 ansible_connection=local
```

### Expected AOM Events (In Order)
1. `v2_playbook_on_start`
2. `v2_playbook_on_play_start` — Play 1 (web1,web2)
3. `v2_playbook_on_task_start` × 3 — Tasks for Play 1
4. `v2_runner_on_ok` × 6 — 3 tasks × 2 hosts (web1, web2)
5. `v2_playbook_on_play_start` — Play 2 (db1)
6. `v2_playbook_on_task_start` × 2 — Tasks for Play 2
7. `v2_runner_on_ok` × 4 — 2 tasks × 2 possible status (db1)
8. `v2_playbook_on_play_start` — Play 3 (all)
9. `v2_playbook_on_task_start` × 2 — Tasks for Play 3
10. `v2_runner_on_skipped` × 2 — Skipped on web2 (conditional failed), ok on web1, db1
11. `v2_runner_on_ok` × 3 — Final task on all 3 hosts
12. `v2_playbook_on_stats`

### Expected Final State
- `RunState.status = COMPLETED`
- 3 plays in `RunState.plays`
- Multiple hosts per play
- Mix of `OK`, `CHANGED`, `SKIPPED` statuses
- Strategy detection: `linear` for all plays

### Expected Exit Code
`0`

### Features Tested (SPEC Mapping)
| Feature | Spec Section |
|---------|-------------|
| Multi-play execution | 5.1, 6.2 |
| Multiple hosts per play | 5.2.1 |
| `v2_runner_on_skipped` | 5.1, 6.2 |
| Conditional execution (`when:`) | 6.2 |
| Strategy detection (linear) | 5.1 |
| Host patterns (groups, `all`) | 5.2.1 |
| Play transitions | 6.4 |
| Exit code 0 | 3.4 |

### Edge Cases Covered
- Host overlap between plays
- Conditional tasks that skip on some hosts
- `changed_when` for explicit changed status
- Mixed `ok`/`changed` results

---

## Playbook 3: Failure Scenarios

### Purpose
Test failure handling with both `ignore_errors: true` (continues) and hard failures (stops).

### YAML Structure (Outline)
```yaml
---
- name: Failure Handling Play
  hosts: localhost
  gather_facts: false
  
  tasks:
    - name: Task 1 - Success
      ansible.builtin.debug:
        msg: "This succeeds"
        
    - name: Task 2 - Failure with ignore_errors
      ansible.builtin.command:
        cmd: /bin/false
      ignore_errors: true
      register: failed_result
      
    - name: Task 3 - Continues after ignored failure
      ansible.builtin.debug:
        msg: "This runs despite Task 2 failing"
        
    - name: Task 4 - Hard failure
      ansible.builtin.command:
        cmd: /bin/false
      # Will stop execution here
        
    - name: Task 5 - Never reached
      ansible.builtin.debug:
        msg: "This should not run"
```

### Expected AOM Events (In Order)
1. `v2_playbook_on_start`
2. `v2_playbook_on_play_start`
3. `v2_playbook_on_task_start` — Task 1
4. `v2_runner_on_ok` — Task 1 completes
5. `v2_playbook_on_task_start` — Task 2
6. `v2_runner_on_failed` — Task 2 fails with `ignore_errors: true`
7. `v2_playbook_on_task_start` — Task 3
8. `v2_runner_on_ok` — Task 3 completes
9. `v2_playbook_on_task_start` — Task 4
10. `v2_runner_on_failed` — Task 4 fails **without** `ignore_errors`
11. `v2_playbook_on_stats` — Final stats with 1 failure

### Expected Final State
- `RunState.status = FAILED`
- Task 2 status: `OK` (because `ignore_errors: true` → `_ansible_verbose_always.ignore_errors = True`)
- Task 4 status: `FAILED` (hard failure)
- Final stats show `failures: 1`

### Expected Exit Code
`1` — Playbook execution failed

### Features Tested (SPEC Mapping)
| Feature | Spec Section |
|---------|-------------|
| `v2_runner_on_failed` | 5.1, 6.2 |
| `ignore_errors` handling | 6.2 |
| State transition RUNNING→FAILED | 6.4 |
| Exit code 1 | 3.4 |
| Failure detection | 5.1 |
| HostRunState with `FAILED` status | 6.1 |

### Edge Cases Covered
- Failure with `ignore_errors: true` continues execution
- Hard failure stops playbook
- `msg` field capture in failed event
- State machine correctly transitions to `FAILED`

---

## Playbook 4: Unreachable Host

### Purpose
Test the `v2_runner_on_unreachable` event and state transition.

### YAML Structure (Outline)
```yaml
---
- name: Unreachable Host Test
  hosts: reachable_host, unreachable_host, another_reachable
  gather_facts: false
  
  tasks:
    - name: Task that runs on reachable hosts
      ansible.builtin.debug:
        msg: "Hello from {{ inventory_hostname }}"
```

### Inventory Required
```ini
[reachable]
reachable_host ansible_host=127.0.0.1 ansible_connection=local
another_reachable ansible_host=127.0.0.1 ansible_connection=local

[unreachable]
unreachable_host ansible_host=192.0.2.1 ansible_connection=ssh ansible_ssh_common_args="-o ConnectTimeout=2"
```

### Expected AOM Events (In Order)
1. `v2_playbook_on_start`
2. `v2_playbook_on_play_start`
3. `v2_playbook_on_task_start` — Single task
4. `v2_runner_on_unreachable` — For `unreachable_host`
5. `v2_runner_on_ok` — For `reachable_host` and `another_reachable`
6. `v2_playbook_on_stats` — Shows unreachable count

### Expected Final State
- `RunState.status = FAILED` (unreachable triggers failure)
- 2 hosts with status `OK`
- 1 host with status `UNREACHABLE`
- Final stats include `unreachable: 1`

### Expected Exit Code
`2` — Unreachable hosts (Ansible convention)

### Features Tested (SPEC Mapping)
| Feature | Spec Section |
|---------|-------------|
| `v2_runner_on_unreachable` | 5.1, 6.2 |
| `UNREACHABLE` status | 6.1 |
| State transition to FAILED (unreachable) | 6.4 |
| Exit code 2 | 3.4 |
| Unreachable host handling | 5.1 |

### Edge Cases Covered
- Connection timeout
- Mixed reachable/unreachable hosts
- Unreachable state icon display (⊝)
- Error message capture in `msg` field

---

## Playbook 5: Role-Based Playbook

### Purpose
Test RoleGroup creation (5+ consecutive same-role tasks) and role display in tree.

### Directory Structure
```
roles/
  nginx/
    tasks/
      main.yml
  postgresql/
    tasks/
      main.yml
```

### YAML Structure (Outline)
```yaml
---
- name: Role-Based Execution
  hosts: localhost
  gather_facts: false
  roles:
    - role: nginx
    - role: postgresql
```

### roles/nginx/tasks/main.yml
```yaml
---
- name: Install nginx
  ansible.builtin.package:
    name: nginx
    state: present
    
- name: Configure nginx
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
    
- name: Create directories
  ansible.builtin.file:
    path: "{{ item }}"
    state: directory
  loop:
    - /etc/nginx/sites-available
    - /etc/nginx/sites-enabled
    
- name: Enable service
  ansible.builtin.service:
    name: nginx
    state: started
    enabled: true
    
- name: Verify nginx
  ansible.builtin.uri:
    url: http://localhost
    status_code: 200
```

### roles/postgresql/tasks/main.yml
```yaml
---
- name: Install PostgreSQL
  ansible.builtin.package:
    name: postgresql
    state: present
    
- name: Initialize database cluster
  ansible.builtin.command:
    cmd: postgresql-initdb
  changed_when: true
```

### Expected AOM Events
- 5+ `v2_playbook_on_task_start` events from nginx role
- Grouped into `RoleGroup` by AOM (5+ consecutive same-role tasks)
- 2 `v2_playbook_on_task_start` events from postgresql role (NOT grouped, <5 tasks)
- All tasks fire `v2_runner_on_ok`

### Expected Final State
- `RunState.definitions[0].tasks` contains:
  - One `RoleGroupDefinition(role="nginx", tasks=[...5 tasks...])`
  - Two individual `TaskDefinition` objects (postgresql role)
- Role grouping displayed in tree view:
  ```
  ▼ ● Role: nginx (5 tasks)
    ● Install nginx
    ● Configure nginx
    ● Create directories
    ● Enable service
    ● Verify nginx
  □ Task: Install PostgreSQL
  □ Task: Initialize database cluster
  ```

### Expected Exit Code
`0`

### Features Tested (SPEC Mapping)
| Feature | Spec Section |
|---------|-------------|
| RoleGroupDefinition creation | 5.4, 6.1 |
| Grouping threshold (5+ tasks) | 5.4 |
| Role prefix parsing (`role : task`) | 5.3 |
| `--list-tasks` role expansion | 5.3 |
| Tree view role display | 7.1 |

### Edge Cases Covered
- Exactly 5 tasks (minimum grouping threshold)
- Fewer than 5 tasks (no grouping)
- Multiple roles in sequence
- Role task grouping algorithm

---

## Playbook 6: Handlers and Conditional Tasks

### Purpose
Test handler task start events, skipped status, and loop handling.

### YAML Structure (Outline)
```yaml
---
- name: Handlers and Conditionals
  hosts: localhost
  gather_facts: false
  
  tasks:
    - name: Install package
      ansible.builtin.package:
        name: nginx
        state: present
      notify: Restart nginx
      
    - name: Create config only when enabled
      ansible.builtin.copy:
        dest: /tmp/config.conf
        content: "enabled=true"
      when: config_enabled | default(true)
      
    - name: Skip this task
      ansible.builtin.debug:
        msg: "This will be skipped"
      when: false
      
    - name: Loop over items
      ansible.builtin.debug:
        msg: "Item: {{ item }}"
      loop:
        - alpha
        - beta
        - gamma
        
    - name: Never notifies
      ansible.builtin.debug:
        msg: "No handler triggered"
      # This never runs or changes
      
  handlers:
    - name: Restart nginx
      ansible.builtin.service:
        name: nginx
        state: restarted
      listen: "Restart nginx"
```

### Expected AOM Events (In Order)
1. `v2_playbook_on_start`
2. `v2_playbook_on_play_start`
3. `v2_playbook_on_task_start` — Install package
4. `v2_runner_on_ok` — Installs package (changed=true → triggers notify)
5. `v2_playbook_on_task_start` — Create config
6. `v2_runner_on_ok` — Creates config (when condition true)
7. `v2_playbook_on_task_start` — Skip this task
8. `v2_runner_on_skipped` — Task skipped (when: false)
9. `v2_playbook_on_task_start` — Loop over items
10. `v2_runner_on_ok` — Loop task (may have multiple results)
11. `v2_playbook_on_task_start` — Never notifies
12. `v2_runner_on_ok` — Debug (ok)
13. `v2_playbook_on_handler_task_start` — Handler: Restart nginx
14. `v2_runner_on_ok` — Handler completes
15. `v2_playbook_on_stats`

### Expected Final State
- 6 regular tasks (5 + 1 handler)
- 2 skipped events
- Handler task marked separately (handler type vs regular task)
- Status `COMPLETED`

### Expected Exit Code
`0`

### Features Tested (SPEC Mapping)
| Feature | Spec Section |
|---------|-------------|
| `v2_playbook_on_handler_task_start` | 5.1 |
| `v2_runner_on_skipped` | 5.1, 6.2 |
| Handler lifecycle | 5.1 |
| Conditional execution (`when:`) | — |
| Loop handling (`loop:`) | — |
| `skip_reason` capture | 6.1 |

### Edge Cases Covered
- Handler only triggers on change
- `when: false` produces skip
- Loop iteration handling
- Handler as separate task type

---

## Playbook 7: Vault and Become (Password Prompts)

### Purpose
Test password prompt detection and handling in `PRE_RUN_PROMPTS` phase.

### YAML Structure (Outline)
```yaml
---
- name: Vault and Become Test
  hosts: localhost
  gather_facts: false
  become: true
  
  vars_files:
    - secrets.vault  # Requires vault password
    
  tasks:
    - name: Task requiring become
      ansible.builtin.package:
        name: nginx
        state: present
```

### Encrypted Vault File
```bash
# secrets.vault (encrypted)
# Contains: secret_api_key: "super_secret_value"

ansible-vault create secrets.vault
# (enter vault password)
```

### Execution Command
```bash
aom playbook.yml --ask-vault-pass --ask-become-pass
```

### Expected AOM Behavior
1. `StreamPhase.PRE_RUN_PROMPTS` active
2. Password prompts detected:
   - `Vault password: `
   - `BECOME password: `
3. `PtyStreamParser._pending_password_prompt` populated
4. Terminal pass-through for password input (compact mode)
   or
   Textual modal for password input (TUI mode)
5. After passwords entered, transition to `EXECUTION` phase

### Expected Events
- No events until passwords provided
- `v2_playbook_on_start` only after password prompts resolved
- Normal execution continues

### Expected Exit Code
`0` (if passwords provided correctly) or user cancellation

### Features Tested (SPEC Mapping)
| Feature | Spec Section |
|---------|-------------|
| Password prompt detection | 5.6, 5.10 |
| PASSWORD_PATTERNS | 5.6 |
| `PRE_RUN_PROMPTS` phase | 5.6 |
| Compact pass-through | 5.10 |
| TUI modal handling | 5.10 |
| Phase transitions | 5.6 |

### Edge Cases Covered
- Multiple password prompts in sequence
- Password prompt timeout (60s default)
- Masked input in TUI mode
- Pass-through in compact mode
- `Vault password (id): ` variant pattern

---

## Playbook 8: Deprecation and Warning Output

### Purpose
Test WarningEntry detection and classification from plaintext stderr.

### YAML Structure (Outline)
```yaml
---
- name: Warning and Deprecation Test
  hosts: localhost
  gather_facts: false
  
  tasks:
    - name: Task with deprecated module
      ansible.builtin.command:
        cmd: echo "test"
      # command module shows deprecation banner in newer Ansible
      
    - name: Task with debug warning
      ansible.builtin.debug:
        msg: "This is informational"
      warn: false  # Suppress expected warning
      
    - name: Task that triggers warning
      ansible.builtin.shell:
        cmd: echo "test"
      # shell module may show warnings about security
      
    - name: Task with explicit warning
      ansible.builtin.debug:
        msg: "[WARNING]: This is a custom warning message"
```

### Expected AOM Behavior
1. During `EXECUTION` phase, plaintext lines interleaved with JSONL
2. `PtyStreamParser._handle_plaintext()` classifies warnings:
   - Pattern `^\[WARNING\]:` → `WarningType.WARNING`
   - Pattern `^\[DEPRECATION WARNING\]:` → `WarningType.DEPRECATION`
   - Pattern `^\[DEPRECATED\]:` → `WarningType.DEPRECATION`
3. `PtyStreamParser.warnings` list populated
4. Compact status line shows: `⚠ X ✱ Y`
5. Filter panel shows warning/deprecation counts

### Expected Events
- Normal JSONL events proceed
- Warnings appended to `_plaintext_lines` AND `_warnings` list
- Display shows warning icons in status line

### Expected Exit Code
`0`

### Features Tested (SPEC Mapping)
| Feature | Spec Section |
|---------|-------------|
| WarningEntry classification | 5.6, 6.1 |
| WARNING_PATTERNS matching | 5.6 |
| Plaintext interleaving | 5.6 |
| Status line warning count | 4.1 |
| Filter panel | 7.6 |
| Warning icon display (⚠) | 11.1 |

### Edge Cases Covered
- `[WARNING]:` prefix detection
- `[DEPRECATION WARNING]:` vs `[DEPRECATED]:` distinction
- Multi-line warnings
- Warnings from controller vs task result

---

## Playbook 9: Large Scale - Stress Test

### Purpose
Test memory bounds and performance with 50+ tasks across 10+ hosts.

### YAML Structure (Outline)
```yaml
---
- name: Stress Test Play 1
  hosts: web1,web2,web3,web4,web5,db1,db2,db3,cache1,cache2
  gather_facts: false
  
  tasks:
    # Repeat this block 30 times
    {{# 30 iterations }}
    - name: "Iteration {{ item }} - Debug"
      ansible.builtin.debug:
        msg: "Task {{ item }} on {{ inventory_hostname }}"
      loop: "{{ range(1, 31) | list }}"
    {{/ end }}
```

### Inventory
```ini
[webservers]
web{1..5} ansible_host=127.0.0.1 ansible_connection=local

[databases]
db{1..3} ansible_host=127.0.0.1 ansible_connection=local

[cache]
cache{1..2} ansible_host=127.0.0.1 ansible_connection=local
```

### Expected Scale
- 10 hosts
- 30 tasks × 10 hosts = 300 task-host executions per play
- ~300 `v2_runner_on_ok` events
- Tests `MAX_LOG_LINES: 50000` handling

### Expected AOM Behavior
1. Memory usage stays bounded
2. Log panel does not exceed `max_lines: 50000`
3. Status panel updates smoothly (throttled to 4 FPS)
4. No UI blocking or slowdown
5. Event count tracks properly
6. Session recording works correctly

### Expected Events
- 300+ `v2_runner_on_ok` events processed
- State tree maintains 10 hosts × 30 tasks
- Memory stays within limits

### Expected Exit Code
`0`

### Features Tested (SPEC Mapping)
| Feature | Spec Section |
|---------|-------------|
| Memory bounds | 6.5 |
| `max_lines: 50000` | 7.2, 8.2 |
| Refresh throttling | 4.5 |
| Event count tracking | 7.5 |
| Session artifact creation | 6.3 |
| Performance at scale | — |

### Edge Cases Covered
- Large host counts (10+)
- Large task counts (50+)
- Log line limit enforcement
- Memory limit safeguards
- Throttled rendering

---

## Playbook 10: Syntax Error Playbook

### Purpose
Test CRASHED state handling for invalid YAML/Ansible syntax.

### YAML Structure (Outline)
```yaml
---
- name: Syntax Error Play
  hosts: localhost
  gather_facts: false
  
  tasks:
    - name: Valid task
      ansible.builtin.debug:
        msg: "This is valid"
        
    - name: Invalid YAML
      ansible.builtin.debug
        msg: "Missing colon"  # Invalid YAML syntax (missing colon)
        invalid_key: true
      
    - name: Never reached
      ansible.builtin.debug:
        msg: "Won't execute"
```

Or alternative: Invalid inventory reference:
```yaml
---
- name: Invalid Reference Play
  hosts: "{{ undefined_variable }}"
  gather_facts: false
  
  tasks:
    - name: Task
      ansible.builtin.debug:
        msg: "Test"
```

### Expected AOM Behavior
1. `LOADING_TASKS` state starts
2. `ansible-playbook --list-tasks` exits non-zero (code 4 for syntax error)
3. State transition: `LOADING_TASKS` → `CRASHED`
4. Error message captured from stderr
5. No JSONL events processed
6. Exit code 4 returned

### Expected Events
- None (playbook never runs)
- Only `--list-tasks` failure captured

### Expected Exit Code
`4` — Syntax error in playbook (Ansible convention)

### Features Tested (SPEC Mapping)
| Feature | Spec Section |
|---------|-------------|
| `LOADING_TASKS` → `CRASHED` | 6.4 |
| `--list-tasks` exit code 4 | 5.3 |
| Syntax error handling | 3.4 |
| Exit code 4 | 3.4 |
| Session artifact (partial) | 6.3 |

### Edge Cases Covered
- Invalid YAML syntax
- Missing required keys
- Undefined variable in `hosts:`
- Malformed task structure

---

## Playbook 11: Include/Import Tasks (Dynamic)

### Purpose
Test dynamic task list expansion from `include_tasks` and `import_playbook`.

### Directory Structure
```
playbook.yml
included_tasks.yml
imported_play.yml
```

### YAML Structure (Outline)
```yaml
# playbook.yml
---
- name: Main Play
  hosts: localhost
  gather_fasks: false
  
  tasks:
    - name: Direct task
      ansible.builtin.debug:
        msg: "Direct task"
        
    - name: Include tasks
      ansible.builtin.include_tasks:
        file: included_tasks.yml
        
    - name: Post-include task
      ansible.builtin.debug:
        msg: "After include"

# included_tasks.yml
---
- name: Included task 1
  ansible.builtin.debug:
    msg: "Included 1"
    
- name: Included task 2
  ansible.builtin.debug:
    msg: "Included 2"

# (Optional: import_playbook)
- import_playbook: imported_play.yml
```

### Expected AOM Behavior
1. `--list-tasks` shows `include_tasks` as SINGLE task entry (NOT expanded)
2. During execution, JSONL events arrive for tasks NOT in `--list-tasks` output
3. AOM creates **dynamic TaskDefinition** nodes:
   - `is_dynamic = True`
   - `task_order = -1` (placed after pre-parsed siblings)
   - `parent_task = include_tasks node`
4. Dynamic tasks rendered under `include_tasks` parent in tree

### Expected Events (In Order)
1. `v2_playbook_on_start`
2. `v2_playbook_on_play_start`
3. `v2_playbook_on_task_start` — Direct task (in --list-tasks)
4. `v2_runner_on_ok` — Direct task complete
5. `v2_playbook_on_task_start` — Include tasks (parent)
6. `v2_runner_on_ok` — Include tasks (parent)
7. **Dynamic events** — Included task 1 (NOT in --list-tasks)
8. **Dynamic events** — Included task 2 (NOT in --list-tasks)
9. `v2_playbook_on_task_start` — Post-include task
10. `v2_runner_on_ok` — Post-include complete
11. `v2_playbook_on_stats`

### Key Observation
Dynamic tasks (`Included task 1`, `Included task 2`) do NOT appear in `--list-tasks` output but DO appear in JSONL events. AOM must create them dynamically with `is_dynamic=True`.

### Expected Exit Code
`0`

### Features Tested (SPEC Mapping)
| Feature | Spec Section |
|---------|-------------|
| `include_tasks` NOT expanded | 5.3 |
| Dynamic task creation | 5.2 |
| `is_dynamic=True` flag | 6.1 |
| `task_order=-1` for dynamic | 6.1 |
| Parent-child relationship | 5.2 |
| Task matching fallback | 5.2, 6.1 |

### Edge Cases Covered
- `include_tasks` dynamic expansion
- `import_playbook` (different behavior)
- Tasks appearing dynamically during run
- Parent-child relationship in tree

---

## Playbook 12: Interrupt and Signal Handling

### Purpose
Test SIGINT forwarding and SIGTERM graceful exit.

### YAML Structure (Outline)
```yaml
---
- name: Long-Running Playbook
  hosts: localhost
  gather_facts: false
  
  tasks:
    - name: Sleep for 60 seconds
      ansible.builtin.command:
        cmd: sleep 60
        
    - name: Second sleep
      ansible.builtin.command:
        cmd: sleep 60
        
    - name: Third sleep
      ansible.builtin.command:
        cmd: sleep 60
```

### Test Scenarios

#### Scenario A: First SIGINT (Ctrl+C)
1. Run playbook
2. Wait for `v2_runner_on_start` on first task
3. Send `SIGINT` (Ctrl+C) once
4. **Expected:** Signal forwarded to `ansible-playbook` subprocess
5. **Expected:** AOM continues running (does NOT exit)
6. **Expected:** Subprocess may exit early or continue

#### Scenario B: Second SIGINT (within 2 seconds)
1. Run playbook
2. Send `SIGINT` (Ctrl+C) first time
3. Within 2 seconds, send `SIGINT` again
4. **Expected:** AOM kills everything immediately
5. **Expected:** Exit code 130

#### Scenario C: SIGTERM
1. Run playbook
2. Send `SIGTERM` to AOM process
3. **Expected:** AOM saves session state
4. **Expected:** Terminal cleanup (cursor restore, colors reset)
5. **Expected:** Exit code 0

#### Scenario D: SIGWINCH (Terminal Resize)
1. Run playbook in TUI mode
2. Resize terminal during execution
3. **Expected:** Re-render panels appropriately

### Expected Events
- For SIGINT: Depends on subprocess response (may or may not exit)
- For SIGTERM: `v2_playbook_on_stats` may be partial or missing
- No specific JSONL events for signals

### Expected Exit Codes
- SIGINT (1st): Subprocess exit code (varies)
- SIGINT (2nd): `130` — User cancelled
- SIGTERM: `0` — Graceful shutdown
- SIGHUP: `0` — Graceful shutdown

### Features Tested (SPEC Mapping)
| Feature | Spec Section |
|---------|-------------|
| SIGINT forwarding | 4.4 |
| SIGINT kill (double) | 4.4 |
| SIGTERM graceful exit | 4.4 |
| SIGHUP graceful exit | 4.4 |
| SIGWINCH re-render | 4.4 |
| Exit code 130 | 3.4 |
| Terminal cleanup | 4.4 |

### Edge Cases Covered
- Single SIGINT (forward to subprocess)
- Double SIGINT (kill immediately)
- SIGTERM while running
- Terminal resize during execution
- Process already terminating when signal received

---

## Minimum Viable Set

For comprehensive coverage with minimal playbooks, use these **4 playbooks**:

| Playbook | Coverage Rationale |
|----------|-------------------|
| **1. Happy Path** | Basic success flow, all major events, COMPLETED state |
| **3. Failure Scenarios** | FAILED state, `ignore_errors`, `v2_runner_on_failed` |
| **5. Role-Based** | RoleGroup creation, multi-task display, role grouping |
| **12. Interrupt** | Signal handling, terminal cleanup, exit codes |

**Why this set:**
- Covers all 10 JSONL event types
- Tests all state transitions (IDLE→STARTING→LOADING→READY→RUNNING→COMPLETED/FAILED)
- Tests exit codes 0, 1, 130
- Tests role grouping and dynamic task handling
- Tests signal handling and terminal cleanup
- Tests password prompts indirectly (if `become: true` added)

**Additional coverage with these 4:**
- Event parsing (all JSONL events)
- State transitions (all states except CRASHED)
- Exit codes (0, 1, 130)
- Role grouping
- Signal handling
- Terminal cleanup

---

## Prerequisites for Testing

### Ansible Collections
```bash
ansible-galaxy collection install ansible.posix
```

### System Requirements
- `ansible-core >= 2.14` (for JSONL callback)
- `ansible.posix >= 1.5.0` (for JSONL callback with path field)

### Inventory
Most playbooks use `localhost` or dummy hosts. For unreachable testing:
```ini
# inventory.ini
[local]
localhost ansible_connection=local

[unreachable]
badhost ansible_host=192.0.2.1 ansible_connection=ssh ansible_ssh_common_args="-o ConnectTimeout=1"
```

### Roles
Playbook 5 requires roles in `roles/` directory:
```
roles/
  nginx/tasks/main.yml
  postgresql/tasks/main.yml
```

### Vault Files
Playbook 7 requires encrypted vault:
```bash
ansible-vault create secrets.vault
# Password: test_password
```

---

## Summary Table

| Playbook | Primary Purpose | Key JSONL Events | Key State |
|----------|----------------|------------------|-----------|
| 1 | Basic success | `v2_runner_on_ok` | COMPLETED |
| 2 | Multiple plays/hosts | `v2_runner_on_skipped` | COMPLETED |
| 3 | Failure handling | `v2_runner_on_failed` | FAILED |
| 4 | Unreachable hosts | `v2_runner_on_unreachable` | FAILED |
| 5 | Role grouping | `v2_playbook_on_task_start` | COMPLETED |
| 6 | Handlers/loops | `v2_playbook_on_handler_task_start`, `v2_runner_on_skipped` | COMPLETED |
| 7 | Password prompts | (No JSONL) | PRE_RUN_PROMPTS |
| 8 | Warnings | (Plaintext) | EXECUTION |
| 9 | Large scale | All events | COMPLETED |
| 10 | Syntax error | (None) | CRASHED |
| 11 | Dynamic tasks | (Dynamic) | COMPLETED |
| 12 | Signal handling | (Depends) | RUNNING→IDLE |

---

## Appendix: Full JSONL Event Coverage

All 10 event types from `ansible.posix.jsonl`:

| Event | Playbook(s) Testing |
|-------|---------------------|
| `v2_playbook_on_start` | All (1-11) |
| `v2_playbook_on_play_start` | All multi-play (2, 11) |
| `v2_playbook_on_task_start` | All (1-6, 8-12) |
| `v2_playbook_on_handler_task_start` | 6 |
| `v2_runner_on_start` | Non-lockstep strategies |
| `v2_runner_on_ok` | All success (1-2, 5-9, 11) |
| `v2_runner_on_failed` | 3 |
| `v2_runner_on_skipped` | 2, 6 |
| `v2_runner_on_unreachable` | 4 |
| `v2_playbook_on_stats` | All (1-11) |

---

## Appendix: State Transition Coverage

| Transition | Playbook(s) Testing |
|------------|---------------------|
| IDLE → STARTING | All (1-11) |
| STARTING → LOADING_TASKS | All (1-11) |
| LOADING_TASKS → READY | All success (1-9, 11) |
| LOADING_TASKS → CRASHED | 10 (syntax error) |
| READY → RUNNING | All success (1-9, 11) |
| RUNNING → COMPLETED | All success (1-2, 5-9, 11) |
| RUNNING → FAILED | 3 (failure), 4 (unreachable) |
| RUNNING → CRASHED | (Manual test: kill subprocess) |
| COMPLETED/FAILED → IDLE | All (user exit) |

---

*End of Integration Test Playbooks Plan*