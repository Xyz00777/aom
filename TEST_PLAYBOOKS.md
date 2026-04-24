# Test Playbooks for ansible-aom

This document lists every Ansible playbook scenario required to fully exercise
the test suite. Each playbook is designed to trigger specific event types,
state transitions, and features that the application monitors.

---

## How to Run These

Every playbook below should be run with the `ansible.posix.jsonl` callback
plugin enabled so that `ansible-aom` can parse the JSONL event stream:

```bash
ANSIBLE_CALLBACK_PLUGINS=/path/to/ansible.posix/plugins/callback \
ANSIBLE_STDOUT_CALLBACK=ansible.posix.jsonl \
aom playbook.yml -i inventory.ini
```

For `--list-tasks` and `--list-hosts` pre-parse:

```bash
ansible-playbook playbook.yml --list-tasks
ansible-playbook playbook.yml --list-hosts
```

---

## Inventory Setup

Create `inventory.ini` for all playbooks:

```ini
[webservers]
web1 ansible_host=127.0.0.1 ansible_connection=local
web2 ansible_host=127.0.0.1 ansible_connection=local
web3 ansible_host=127.0.0.1 ansible_connection=local

[dbservers]
db1 ansible_host=127.0.0.1 ansible_connection=local

[unreachable]
ghost ansible_host=192.0.2.1 ansible_timeout=1

[mixed]
ok-host ansible_host=127.0.0.1 ansible_connection=local
fail-host ansible_host=127.0.0.1 ansible_connection=local
skip-host ansible_host=127.0.0.1 ansible_connection=local
dead-host ansible_host=192.0.2.1 ansible_timeout=1

[all:vars]
ansible_python_interpreter={{ ansible_playbook_python }}
```

---

## 1. Minimal Single-Task Success

**Covers:** `v2_playbook_on_start`, `v2_playbook_on_play_start`,
`v2_playbook_on_task_start` (linear strategy), `v2_runner_on_ok` (changed=false),
`v2_playbook_on_stats`, Status.OK, exit code 0

**Existing fixture:** `tests/fixtures/single_task_ok.jsonl`

```yaml
---
- name: Setup webservers
  hosts: webservers
  gather_facts: false
  tasks:
    - name: Install nginx
      ansible.builtin.debug:
        msg: "nginx installed"
```

**Expected event sequence:**
1. `v2_playbook_on_start` — playbook begins
2. `v2_playbook_on_play_start` — play "Setup webservers" starts
3. `v2_playbook_on_task_start` — task "Install nginx" declared (linear strategy)
4. `v2_runner_on_ok` — host web1 succeeds, `changed: false`
5. `v2_runner_on_ok` — host web2 succeeds, `changed: false`
6. `v2_runner_on_ok` — host web3 succeeds, `changed: false`
7. `v2_playbook_on_stats` — playbook finishes, all ok

**Exit code:** 0

---

## 2. Single-Task with Changes

**Covers:** `v2_runner_on_ok` (changed=true), Status.CHANGED

```yaml
---
- name: Apply configuration
  hosts: webservers
  gather_facts: false
  tasks:
    - name: Create config file
      ansible.builtin.copy:
        dest: /tmp/aom-test-config.ini
        content: "test=true\n"
        mode: "0644"
```

**Expected event sequence:**
1. `v2_playbook_on_start`
2. `v2_playbook_on_play_start` — play "Apply configuration"
3. `v2_playbook_on_task_start` — task "Create config file"
4. `v2_runner_on_ok` — each host, `changed: true` (file created)

**Exit code:** 0

**Cleanup after test:**
```bash
rm -f /tmp/aom-test-config.ini
```

---

## 3. Task Failure

**Covers:** `v2_runner_on_failed`, Status.FAILED, exit code 1

**Existing fixture:** `tests/fixtures/playbook_failed.jsonl`

```yaml
---
- name: Configure servers
  hosts: webservers
  gather_facts: false
  tasks:
    - name: Succeed first
      ansible.builtin.debug:
        msg: "this works"

    - name: Fail on purpose
      ansible.builtin.fail:
        msg: "Configuration file syntax error at line 42"
```

**Expected event sequence:**
1. `v2_playbook_on_start`
2. `v2_playbook_on_play_start`
3. `v2_playbook_on_task_start` — "Succeed first"
4. `v2_runner_on_ok` — all hosts ok
5. `v2_playbook_on_task_start` — "Fail on purpose"
6. `v2_runner_on_failed` — all hosts, `failed: true, msg: "..."`
7. `v2_playbook_on_stats` — failures > 0

**Exit code:** 1

---

## 4. Failure with ignore_errors

**Covers:** `v2_runner_on_failed` with `_ansible_verbose_always.ignore_errors`,
Status.OK (not FAILED) when ignore_errors=true

**Test reference:** TC-209, conftest `event_runner_failed_ignore`

```yaml
---
- name: Tolerant deployment
  hosts: webservers
  gather_facts: false
  tasks:
    - name: Optional check that may fail
      ansible.builtin.fail:
        msg: "This is acceptable"
      ignore_errors: true

    - name: Continue after ignored failure
      ansible.builtin.debug:
        msg: "Still running"
```

**Expected event sequence:**
1. `v2_playbook_on_start`
2. `v2_playbook_on_play_start`
3. `v2_playbook_on_task_start` — "Optional check"
4. `v2_runner_on_failed` — `ignore_errors: true` → app records Status.OK, NOT FAILED
5. `v2_playbook_on_task_start` — "Continue after ignored failure"
6. `v2_runner_on_ok` — still running
7. `v2_playbook_on_stats` — playbook completes (not FAILED)

**Key assertion:** The `RunState.status` must NOT transition to FAILED.
The `HostRunState.status` must be OK (not FAILED) when ignore_errors is true.

**Exit code:** 0 (because all failures were ignored)

---

## 5. Skipped Tasks

**Covers:** `v2_runner_on_skipped`, Status.SKIPPED, `skip_reason` field

**Existing fixture:** `tests/fixtures/multi_host_mixed.jsonl` (web3 entry)

```yaml
---
- name: Conditional tasks
  hosts: webservers
  gather_facts: false
  vars:
    deploy_app: false
  tasks:
    - name: Always runs
      ansible.builtin.debug:
        msg: "running"

    - name: Skip this task
      ansible.builtin.debug:
        msg: "skipped"
      when: deploy_app | bool
```

**Expected event sequence:**
1. `v2_playbook_on_start`
2. `v2_playbook_on_play_start`
3. `v2_playbook_on_task_start` — "Always runs"
4. `v2_runner_on_ok` — all hosts ok
5. `v2_playbook_on_task_start` — "Skip this task"
6. `v2_runner_on_skipped` — all hosts, `skipped: true, skip_reason: "Conditional result was False"`
7. `v2_playbook_on_stats`

**Exit code:** 0

---

## 6. Unreachable Host

**Covers:** `v2_runner_on_unreachable`, Status.UNREACHABLE, exit code 1 or 4

**Existing fixture:** `tests/fixtures/multi_host_mixed.jsonl` (web1 deploy task)

```yaml
---
- name: Deploy to mixed hosts
  hosts: unreachable
  gather_facts: false
  tasks:
    - name: Try to connect
      ansible.builtin.ping:
```

**Expected event sequence:**
1. `v2_playbook_on_start`
2. `v2_playbook_on_play_start`
3. `v2_playbook_on_task_start` — "Try to connect"
4. `v2_runner_on_unreachable` — host ghost, `unreachable: true, msg: "SSH connection timed out"`
5. `v2_playbook_on_stats` — unreachable > 0

**Exit code:** 4 (unreachable hosts)

**Note:** The `unreachable` group uses a TEST-NET address (192.0.2.1) that will
never respond. Adjust `ansible_timeout=1` to keep tests fast.

---

## 7. Multi-Host Mixed Results

**Covers:** All 5 host result statuses in a single playbook (OK, CHANGED, FAILED,
SKIPPED, UNREACHABLE). Tests that the renderer displays correct status icons
and colors for each host.

**Existing fixture:** `tests/fixtures/multi_host_mixed.jsonl`

```yaml
---
- name: Setup webservers
  hosts: mixed
  gather_facts: false
  tasks:
    - name: Install common packages
      ansible.builtin.debug:
        msg: "installed"

    - name: Configure firewall
      ansible.builtin.shell: |
        if [ "$(hostname)" = "fail-host" ]; then exit 1; fi
        echo "configured"
      changed_when: true
      when: inventory_hostname != "skip-host"

    - name: Deploy application
      ansible.builtin.debug:
        msg: "deployed"
```

**Expected per-host results:**

| Host        | Task 1 (Install) | Task 2 (Firewall)                | Task 3 (Deploy) |
|-------------|-------------------|----------------------------------|-----------------|
| ok-host     | OK                | CHANGED                          | OK              |
| fail-host   | OK                | FAILED                           | skipped*        |
| skip-host   | OK                | SKIPPED (when: false)            | OK              |
| dead-host   | OK                | UNREACHABLE                      | UNREACHABLE*    |

*Ansible may skip further tasks for failed/unreachable hosts depending on
`any_errors_fatal` and strategy settings.

**Exit code:** depends on configuration (1 or 4)

---

## 8. Multiple Plays

**Covers:** Multiple `v2_playbook_on_play_start` events, play-by-play tracking,
play definitions, `--list-tasks` and `--list-hosts` parsing with multiple plays

**Test reference:** conftest `list_tasks_output`, `list_hosts_output`

```yaml
---
- name: Setup web servers
  hosts: webservers
  gather_facts: false
  tags: [web]
  tasks:
    - name: Install nginx
      ansible.builtin.debug:
        msg: "nginx installed"
      tags: [web]

    - name: Configure nginx
      ansible.builtin.debug:
        msg: "nginx configured"
      tags: [web]

    - name: Deploy site
      ansible.builtin.debug:
        msg: "site deployed"
      tags: [deploy]

- name: Setup database
  hosts: dbservers
  gather_facts: false
  tags: [db]
  tasks:
    - name: Install postgres
      ansible.builtin.debug:
        msg: "postgres installed"
      tags: [db]

    - name: Configure postgres
      ansible.builtin.debug:
        msg: "postgres configured"
      tags: [db]
```

**Expected `--list-tasks` output format:**
```
playbook: site.yml

  play #1 (webservers): Setup web servers	TAGS: []
    install nginx	TAGS: [web]
    configure nginx	TAGS: [web]
    deploy site	TAGS: [deploy]

  play #2 (dbservers): Setup database	TAGS: []
    install postgres	TAGS: [db]
    configure postgres	TAGS: [db]
```

Note: TAB character (0x09) separates task name from `TAGS:`.

**Expected `--list-hosts` output format:**
```
playbook: site.yml

  play #1 (webservers): Setup web servers	TAGS: []
    pattern: ['webservers']
    hosts (3):
      web1
      web2
      web3

  play #2 (dbservers): Setup database	TAGS: []
    pattern: ['dbservers']
    hosts (1):
      db1
```

**Exit code:** 0

---

## 9. Handler Tasks

**Covers:** `v2_playbook_on_handler_task_start`, handler execution tracking

```yaml
---
- name: Handler test
  hosts: webservers
  gather_facts: false
  tasks:
    - name: Trigger handler
      ansible.builtin.copy:
        dest: /tmp/aom-handler-test
        content: "triggered\n"
        mode: "0644"
      notify: Restart service

  handlers:
    - name: Restart service
      ansible.builtin.debug:
        msg: "service restarted"
```

**Expected event sequence:**
1. `v2_playbook_on_start`
2. `v2_playbook_on_play_start`
3. `v2_playbook_on_task_start` — "Trigger handler"
4. `v2_runner_on_ok` — hosts changed=true
5. `v2_playbook_on_handler_task_start` — "Restart service" handler declared
6. `v2_runner_on_ok` — handler runs
7. `v2_playbook_on_stats`

**Cleanup:**
```bash
rm -f /tmp/aom-handler-test
```

---

## 10. Free Strategy

**Covers:** `v2_runner_on_start` events (free/host_pinned strategy detection),
strategy=`free` vs strategy=`linear`

```yaml
---
- name: Free strategy execution
  hosts: webservers
  gather_facts: false
  strategy: free
  tasks:
    - name: Task A
      ansible.builtin.debug:
        msg: "A on {{ inventory_hostname }}"

    - name: Task B
      ansible.builtin.debug:
        msg: "B on {{ inventory_hostname }}"
```

**Expected behavior:**
With `strategy: free`, hosts proceed independently. The app should detect
`v2_runner_on_start` events arriving before (or without) prior
`v2_playbook_on_task_start`, and set `detected_strategy = "free"`.

With `strategy: linear` (default), `v2_playbook_on_task_start` fires first,
and the app sets `detected_strategy = "linear"`.

---

## 11. Role-Based Tasks (Role Grouping)

**Covers:** RoleGroupDefinition, role grouping (5+ consecutive same-role tasks),
role prefix display

```yaml
---
- name: Role grouping test
  hosts: webservers
  gather_facts: false
  roles:
    - role: nginx
```

Where the `nginx` role has 7+ tasks in `roles/nginx/tasks/main.yml`:

```yaml
# roles/nginx/tasks/main.yml
- name: Install nginx package
  ansible.builtin.debug: { msg: "install" }
- name: Configure nginx main
  ansible.builtin.debug: { msg: "main config" }
- name: Configure nginx vhost
  ansible.builtin.debug: { msg: "vhost config" }
- name: Configure nginx ssl
  ansible.builtin.debug: { msg: "ssl config" }
- name: Configure nginx logging
  ansible.builtin.debug: { msg: "logging config" }
- name: Start nginx service
  ansible.builtin.debug: { msg: "start" }
- name: Verify nginx running
  ansible.builtin.debug: { msg: "verify" }
```

**Expected behavior:**
When 5+ consecutive tasks share the same role, they should be grouped:
`"Role: nginx (7 tasks)"` with expandable children.

The `--list-tasks` output shows role prefixes:
```
    nginx : Install nginx package	TAGS: [...]
    nginx : Configure nginx main	TAGS: [...]
```

---

## 12. Vault-Encrypted Playbook

**Covers:** Password prompt patterns — `Vault password: ` and
`Vault password (ID): ` variants

```bash
# Create a vault-encrypted variable file
echo 'secret_api_key: "super-secret-value"' > vars/secrets.yml
ansible-vault encrypt vars/secrets.yml --ask-vault-pass
# Enter vault password: testvault
```

```yaml
---
- name: Vault-encrypted playbook
  hosts: webservers
  gather_facts: false
  vars_files:
    - vars/secrets.yml
  tasks:
    - name: Use secret
      ansible.builtin.debug:
        msg: "{{ secret_api_key }}"
```

**Run with:**
```bash
aom playbook.yml -i inventory.ini --ask-vault-pass
# Expected: "Vault password: " prompt appears before execution
```

**For vault ID variant:**
```bash
ansible-vault encrypt vars/secrets.yml --vault-id dev@prompt
# Expected: "Vault password (dev): " prompt
```

**Expected prompt detection:**
- `Vault password: ` — standard vault
- `Vault password (dev): ` — vault with ID label

---

## 13. SSH Password Authentication

**Covers:** Password prompt pattern — `SSH password: `

```ini
# inventory_ssh.ini
[ssh_hosts]
ssh-target ansible_host=127.0.0.1 ansible_connection=ssh ansible_user=testuser ansible_password_prompt=true
```

**Run with:**
```bash
aom playbook.yml -i inventory_ssh.ini --ask-pass
# Expected: "SSH password: " prompt
```

**Alternative:** Use `ansible_ssh_password: "{{ prompt('SSH password') }}"` in
host variables (requires ansible 2.18+ or custom setup).

**Note:** Testing SSH password prompts against local connections requires
a real SSH server or mock. For unit tests, the PTY stream fixture provides
the prompt string directly.

---

## 14. Become (Privilege Escalation)

**Covers:** Password prompt patterns — `BECOME password: ` and
`BECOME password[defaults to SSH password]: `

```yaml
---
- name: Become test
  hosts: webservers
  gather_facts: false
  become: true
  tasks:
    - name: Root-only task
      ansible.builtin.debug:
        msg: "running as {{ ansible_effective_user_id }}"
```

**Run with:**
```bash
aom playbook.yml -i inventory.ini --ask-become-pass
# Expected: "BECOME password: " prompt
```

**For the "defaults to SSH password" variant:**
```bash
aom playbook.yml -i inventory.ini --ask-pass --ask-become-pass
# Expected: "BECOME password[defaults to SSH password]: " prompt
```

---

## 15. Vault Password Change

**Covers:** Password prompt patterns — `New Vault password: ` and
`Confirm New Vault password: `

```bash
# Re-key an existing vault-encrypted file
ansible-vault rekey vars/secrets.yml
# Expected prompts:
#   "New Vault password: "
#   "Confirm New Vault password: "
```

**Note:** This is an `ansible-vault` CLI operation, not an `ansible-playbook`
run. The app only needs to detect these prompt patterns if they appear during
playbook execution (rare, but possible with vault rekey callbacks).

---

## 16. Ansible Warnings

**Covers:** `[WARNING]:` pattern detection, WarningType.WARNING classification

**Trigger warnings by:**
- Using an invalid host pattern: `hosts: nonexistentgroup`
- Using deprecated features (see playbook 17)
- Running with `-v` and having undefined variables

```yaml
---
- name: Warning-producing playbook
  hosts: nonexistentgroup
  gather_facts: false
  tasks:
    - name: Wont run
      ansible.builtin.debug:
        msg: "never reached"
```

**Expected PTY output:**
```
[WARNING]: Could not match supplied host pattern, ignoring: nonexistentgroup
```

**App behavior:** Classifies as `WarningType.WARNING`, increments `_warnings_count`.

---

## 17. Deprecation Warnings

**Covers:** `[DEPRECATION WARNING]:` and `[DEPRECATED]:` pattern detection,
WarningType.DEPRECATION classification

```yaml
---
- name: Deprecation test
  hosts: webservers
  gather_facts: false
  tasks:
    # Use an old-style include (deprecated in favor of include_tasks)
    - name: Old-style include
      ansible.builtin.include: tasks/subtask.yml
```

Or trigger by using deprecated module parameters:

```yaml
    - name: Deprecated syntax
      ansible.builtin.command: echo test
      warn: true  # deprecated parameter
```

**Expected PTY output:**
```
[DEPRECATION WARNING]: Using 'include' for task inclusion is deprecated. Use 'include_tasks' instead.
```

**For `[DEPRECATED]:` (removed feature):**
Triggered by using features removed in the current ansible-core version.

**App behavior:**
- `[DEPRECATION WARNING]: ...` → `WarningType.DEPRECATION`
- `[DEPRECATED]: ...` → `WarningType.DEPRECATION`
- Increments `_deprecations_count`

---

## 18. no_log Tasks (Secret Redaction Layer 1)

**Covers:** `_ansible_no_log` flag handling, entire result replaced with
`{"censored": "(no_log)"}`

```yaml
---
- name: Secret operations
  hosts: webservers
  gather_facts: false
  tasks:
    - name: Hidden command
      ansible.builtin.shell: echo "super-secret-api-key-12345"
      no_log: true

    - name: Visible command
      ansible.builtin.debug:
        msg: "this is visible"
```

**Expected behavior:**
- Task "Hidden command": `res` is completely replaced with `{"censored": "(no_log)"}`
- Task "Visible command": normal output displayed
- Loop items with per-item `_ansible_no_log` are individually censored

---

## 19. Password Field Redaction (Secret Redaction Layer 2)

**Covers:** PASSWORD_MATCH regex, ANSIBLE_PASSWORD_FIELDS, GENERIC_SECRET_FIELDS,
PASSWORD_WHITELIST

```yaml
---
- name: Password field redaction
  hosts: webservers
  gather_facts: false
  vars:
    ansible_ssh_pass: "secret_ssh_pass"     # ANSIBLE_PASSWORD_FIELDS → redacted
    ansible_become_pass: "secret_become"    # ANSIBLE_PASSWORD_FIELDS → redacted
    api_key: "secret_api_key"              # GENERIC_SECRET_FIELDS → redacted
    secret_key: "secret_key_value"         # GENERIC_SECRET_FIELDS → redacted
    access_token: "secret_token"           # GENERIC_SECRET_FIELDS → redacted
    passenger_version: "6.0.2"             # WHITELIST → NOT redacted
    bypass: "allowed_value"                # WHITELIST → NOT redacted
  tasks:
    - name: Show all vars
      ansible.builtin.debug:
        msg: |
          ssh_pass={{ ansible_ssh_pass }}
          become_pass={{ ansible_become_pass }}
          api_key={{ api_key }}
          secret_key={{ secret_key }}
          token={{ access_token }}
          passenger={{ passenger_version }}
          bypass={{ bypass }}
```

**Redaction expectations:**

| Variable             | Category                | Redacted? |
|----------------------|-------------------------|-----------|
| `ansible_ssh_pass`   | ANSIBLE_PASSWORD_FIELDS | YES       |
| `ansible_become_pass`| ANSIBLE_PASSWORD_FIELDS | YES       |
| `api_key`            | GENERIC_SECRET_FIELDS   | YES       |
| `secret_key`         | GENERIC_SECRET_FIELDS   | YES       |
| `access_token`       | GENERIC_SECRET_FIELDS   | YES       |
| `passenger_version`  | PASSWORD_WHITELIST      | NO        |
| `bypass`             | PASSWORD_WHITELIST       | NO        |
| `compass`            | PASSWORD_WHITELIST      | NO        |
| `underpass`           | PASSWORD_WHITELIST      | NO        |
| `overpass`            | PASSWORD_WHITELIST      | NO        |

---

## 20. URL and CLI Credential Redaction (Secret Redaction Layer 3)

**Covers:** URL credential pattern `user:pass@host`, CLI credential pattern
`--password=secret`

```yaml
---
- name: Credential redaction
  hosts: webservers
  gather_facts: false
  tasks:
    - name: URL with credentials
      ansible.builtin.debug:
        msg: "Connecting to https://admin:s3cret@api.example.com/v1/data"

    - name: CLI with password
      ansible.builtin.shell: |
        curl --password secret123 https://example.com
        mysql --password=dbpass -u root -e "SELECT 1"
```

**Redaction expectations:**
- `https://admin:s3cret@api.example.com` → `https://admin:********@api.example.com`
- `--password secret123` → `--password ********`
- `--password=dbpass` → `--password=********`
- `--pass secret123` → `--pass ********`
- `--token mytoken` → `--token ********`
- `--secret mysecret` → `--secret ********`

---

## 21. Module Args Redaction (Secret Redaction Layer 4)

**Covers:** `invocation.module_args` recursive redaction

```yaml
---
- name: Module args redaction
  hosts: webservers
  gather_facts: false
  tasks:
    - name: Module with password arg
      ansible.builtin.uri:
        url: "https://api.example.com/auth"
        user: "admin"
        password: "s3cret"
        method: POST
        body_format: json
```

**Expected behavior:**
The `invocation.module_args` dict in the JSONL event is recursively redacted.
Any field matching PASSWORD_MATCH or in ANSIBLE_PASSWORD_FIELDS/GENERIC_SECRET_FIELDS
within `module_args` is replaced with `"********"`.

---

## 22. PLAY RECAP Parsing

**Covers:** POST_RUN_RECAP phase, `PLAY RECAP ****...` pattern detection,
recap line collection after `v2_playbook_on_stats`

Any playbook that completes will produce a PLAY RECAP. Run any of the above
playbooks with the default callback and observe the recap output:

```
PLAY RECAP *********************************************************************
web1                       : ok=2    changed=1    failed=0    skipped=0    unreachable=0
web2                       : ok=1    changed=0    failed=1    skipped=0    unreachable=0
web3                       : ok=1    changed=0    failed=0    skipped=1    unreachable=0
```

**Note:** With the `ansible.posix.jsonl` callback, the PLAY RECAP appears as
plaintext AFTER the `v2_playbook_on_stats` JSONL event. The app must parse
this in the POST_RUN_RECAP phase.

---

## 23. ansible-playbook Command Not Found

**Covers:** Exit code 127, CRASHED state transition

```bash
# Temporarily rename ansible-playbook
sudo mv /usr/bin/ansible-playbook /usr/bin/ansible-playbook.bak
aom playbook.yml -i inventory.ini
# Expected: exit code 127, RunState transitions to CRASHED
sudo mv /usr/bin/ansible-playbook.bak /usr/bin/ansible-playbook
```

Or use a nonexistent playbook path that causes ansible-playbook to not be found
(in PATH).

**Expected behavior:**
- App detects exit code 127
- `RunState.status` → CRASHED
- Error message displayed

---

## 24. User Cancellation (Ctrl+C)

**Covers:** Exit code 130 (SIGINT), CRASHED state transition

Run any playbook that takes time, then press Ctrl+C during execution:

```yaml
---
- name: Long-running playbook
  hosts: webservers
  gather_facts: false
  tasks:
    - name: Slow task
      ansible.builtin.shell: sleep 60
```

**Test procedure:**
1. Start `aom playbook.yml`
2. Press Ctrl+C while running
3. Ansible sends SIGINT, exits with code 130

**Expected behavior:**
- App detects exit code 130
- `RunState.status` → CRASHED (or specific "cancelled" handling)
- Quit confirmation not needed (already terminated)

---

## 25. ansible-playbook Syntax Error

**Covers:** `--list-tasks` exit code 4, syntax error handling

```yaml
---
- name: Broken syntax
  hosts: webservers
  gather_facts: false
  tasks:
    - name: Missing colon
      ansible.builtin.debug
        msg: "this yaml is broken"
# Missing colon after ansible.builtin.debug
```

**Run:**
```bash
ansible-playbook broken.yml --list-tasks
# Expected: exit code 4 (syntax error)
```

**Expected behavior:**
- `--list-tasks` returns exit code 4
- App detects syntax error, transitions to CRASHED
- Error message shown to user

---

## 26. Empty Playbook

**Covers:** Edge case — playbook with no plays

```yaml
---
```

**Expected behavior:**
- `v2_playbook_on_start` fires
- No `v2_playbook_on_play_start` events
- `v2_playbook_on_stats` fires with empty stats
- Exit code 0

---

## 27. Single Host (localhost)

**Covers:** `hosts: localhost`, minimal single-host execution,
`--list-hosts` with localhost pattern

```yaml
---
- name: Local test
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Local task
      ansible.builtin.debug:
        msg: "hello from localhost"
```

**Expected `--list-hosts` output:**
```
playbook: local.yml

  play #1 (localhost): Local test	TAGS: []
    pattern: ['localhost']
    hosts (1):
      localhost
```

---

## 28. Host Pattern Filtering

**Covers:** `--list-hosts` pattern resolution, `--limit` flag,
pattern like `webservers:!db_primary`

```yaml
---
- name: Filtered play
  hosts: webservers:!ghost
  gather_facts: false
  tasks:
    - name: Ping
      ansible.builtin.ping:
```

**Run:**
```bash
ansible-playbook filtered.yml --list-hosts
# Expected: pattern resolved, excluding 'ghost'
```

**Also test with --limit:**
```bash
ansible-playbook filtered.yml --list-hosts --limit web1
# Expected: only web1 shown
```

---

## 29. Tags

**Covers:** TAGS parsing in `--list-tasks` output, tag-based filtering

```yaml
---
- name: Tagged playbook
  hosts: webservers
  gather_facts: false
  tasks:
    - name: Install base
      ansible.builtin.debug:
        msg: "base"
      tags: [install]

    - name: Install app
      ansible.builtin.debug:
        msg: "app"
      tags: [install, app]

    - name: Configure
      ansible.builtin.debug:
        msg: "config"
      tags: [configure]

    - name: Deploy
      ansible.builtin.debug:
        msg: "deploy"
      tags: [deploy]
```

**Run:**
```bash
ansible-playbook tagged.yml --list-tasks
# Expected: TAB-separated TAGS: [...] for each task

ansible-playbook tagged.yml --list-tasks --tags install
# Expected: only "Install base" and "Install app" shown
```

---

## 30. include_tasks vs import_tasks

**Covers:** `--list-tasks` behavior: `include_tasks` NOT expanded,
`import_tasks` IS expanded

```yaml
---
# site.yml
- name: Test include vs import
  hosts: webservers
  gather_facts: false
  tasks:
    - name: Dynamic include
      ansible.builtin.include_tasks: tasks/dynamic.yml

    - name: Static import
      ansible.builtin.import_tasks: tasks/static.yml
```

```yaml
# tasks/dynamic.yml
- name: Dynamic task A
  ansible.builtin.debug:
    msg: "dynamic A"
- name: Dynamic task B
  ansible.builtin.debug:
    msg: "dynamic B"
```

```yaml
# tasks/static.yml
- name: Static task A
  ansible.builtin.debug:
    msg: "static A"
- name: Static task B
  ansible.builtin.debug:
    msg: "static B"
```

**Expected `--list-tasks` output:**
```
playbook: site.yml

  play #1 (webservers): Test include vs import	TAGS: []
    Dynamic include	TAGS: []        ← NOT expanded (single entry)
    Static task A	TAGS: []         ← IS expanded (inline)
    Static task B	TAGS: []         ← IS expanded (inline)
```

---

## 31. Block Tasks (Flattened)

**Covers:** Blocks are flattened in `--list-tasks` output (no block container)

```yaml
---
- name: Block test
  hosts: webservers
  gather_facts: false
  tasks:
    - name: Regular task
      ansible.builtin.debug:
        msg: "normal"

    - block:
        - name: Block task 1
          ansible.builtin.debug:
            msg: "block 1"

        - name: Block task 2
          ansible.builtin.debug:
            msg: "block 2"

      rescue:
        - name: Rescue task
          ansible.builtin.debug:
            msg: "rescued"

      always:
        - name: Always task
          ansible.builtin.debug:
            msg: "always"

    - name: After block
      ansible.builtin.debug:
        msg: "after"
```

**Expected `--list-tasks` output:**
```
  Regular task       TAGS: []
  Block task 1       TAGS: []
  Block task 2       TAGS: []
  Rescue task        TAGS: []
  Always task        TAGS: []
  After block        TAGS: []
```

Block/rescue/always are flattened — no nesting or block headers.

---

## 32. Large Playbook (Memory Bounds)

**Covers:** Memory bound enforcement (MAX_PLAYS=1000, MAX_TASKS_PER_PLAY=10000,
MAX_HOSTS_PER_TASK=10000, MAX_TOTAL_HOST_RUN_STATES=1000000, MAX_LOG_LINES=50000)

For a real test, generate a playbook with many plays/tasks:

```python
# generate_large_playbook.py
plays = 50
tasks_per_play = 200
print("---")
for p in range(plays):
    print(f"- name: Play {p}")
    print("  hosts: webservers")
    print("  gather_facts: false")
    print("  tasks:")
    for t in range(tasks_per_play):
        print(f"    - name: Task {p}-{t}")
        print("      ansible.builtin.debug:")
        print(f'        msg: "play {p} task {t}"')
```

**Expected behavior:**
- App must not crash or consume unbounded memory
- Bounds are enforced by the state machine (oldest entries evicted or capped)
- Logs beyond `MAX_LOG_LINES` are trimmed (deque with maxlen)

---

## 33. Mixed Warnings + Execution

**Covers:** Warning detection interleaved with JSONL events in EXECUTION phase

```yaml
---
- name: Mixed output
  hosts: webservers
  gather_facts: false
  tasks:
    - name: Task 1
      ansible.builtin.debug:
        msg: "{{ undefined_var }}"
      ignore_errors: true
      # This produces a [WARNING]: about undefined variable

    - name: Task 2
      ansible.builtin.debug:
        msg: "normal task"
```

**Expected PTY output sequence:**
1. JSONL: `v2_playbook_on_start`
2. JSONL: `v2_playbook_on_play_start`
3. Plaintext: `[WARNING]: ...` (interleaved warning)
4. JSONL: `v2_playbook_on_task_start`
5. JSONL: `v2_runner_on_failed` (ignore_errors)
6. JSONL: `v2_playbook_on_task_start`
7. JSONL: `v2_runner_on_ok`
8. JSONL: `v2_playbook_on_stats`
9. Plaintext: `PLAY RECAP ***...`

---

## Summary: Coverage Matrix

| # | Playbook Scenario                          | Events/Features Covered                                    |
|---|--------------------------------------------|------------------------------------------------------------|
| 1 | Single-Task Success                        | start, play_start, task_start, runner_ok(changed=false), stats |
| 2 | Single-Task with Changes                   | runner_ok(changed=true), Status.CHANGED                    |
| 3 | Task Failure                               | runner_failed, Status.FAILED, exit 1                      |
| 4 | Failure with ignore_errors                 | runner_failed+ignore_errors, Status.OK (not FAILED)        |
| 5 | Skipped Tasks                              | runner_skipped, Status.SKIPPED, skip_reason                |
| 6 | Unreachable Host                            | runner_unreachable, Status.UNREACHABLE, exit 4            |
| 7 | Multi-Host Mixed Results                   | All 5 host statuses in one run                             |
| 8 | Multiple Plays                             | Multiple play_start, list-tasks, list-hosts                |
| 9 | Handler Tasks                              | handler_task_start event                                   |
|10 | Free Strategy                              | runner_start (free), strategy detection                     |
|11 | Role-Based Tasks                            | Role grouping (5+ same role), role prefix                   |
|12 | Vault-Encrypted                            | Vault password prompt (standard + ID variant)             |
|13 | SSH Password                               | SSH password prompt                                        |
|14 | Become (Privilege Escalation)               | BECOME password prompt, default variant                    |
|15 | Vault Password Change                       | New/Confirm Vault password prompts                         |
|16 | Ansible Warnings                            | [WARNING]: pattern, WarningType.WARNING                    |
|17 | Deprecation Warnings                        | [DEPRECATION WARNING]: [DEPRECATED]: patterns              |
|18 | no_log Tasks                               | _ansible_no_log redaction (Layer 1)                       |
|19 | Password Field Redaction                    | PASSWORD_MATCH, ANSIBLE/GENERIC fields, whitelist (Layer 2)|
|20 | URL/CLI Credential Redaction                | URL creds, CLI --password (Layer 3)                       |
|21 | Module Args Redaction                       | invocation.module_args recursion (Layer 4)                 |
|22 | PLAY RECAP Parsing                          | POST_RUN_RECAP phase, recap line collection                |
|23 | Command Not Found                           | Exit 127, CRASHED state                                   |
|24 | User Cancellation                           | Exit 130 (SIGINT), CRASHED state                          |
|25 | Syntax Error                                | --list-tasks exit 4, CRASHED state                        |
|26 | Empty Playbook                              | No plays, minimal events                                   |
|27 | Single Host (localhost)                     | localhost pattern resolution                               |
|28 | Host Pattern Filtering                      | Pattern resolution, --limit                              |
|29 | Tags                                        | TAGS parsing, --tags filtering                           |
|30 | include_tasks vs import_tasks               | Include not expanded, import expanded                     |
|31 | Block Tasks (Flattened)                     | Block/rescue/always flattened                             |
|32 | Large Playbook                              | Memory bounds (MAX_PLAYS, MAX_TASKS, etc.)                |
|33 | Mixed Warnings + Execution                  | Warnings interleaved with JSONL                           |

---

## Minimal Set for CI

If you need to run only the most critical playbooks to verify the core pipeline,
use this minimal set:

| # | Playbook          | Why                                    |
|---|-------------------|----------------------------------------|
| 1 | Single-Task Success | Happy path, basic event parsing       |
| 3 | Task Failure       | Failure detection and state transition |
| 4 | ignore_errors      | Critical edge case (OK vs FAILED)     |
| 5 | Skipped Tasks      | SKIPPED status                         |
| 6 | Unreachable Host   | UNREACHABLE status, exit code 4       |
| 7 | Multi-Host Mixed   | All statuses in one run               |
| 8 | Multiple Plays     | Multi-play tracking                   |
|12 | Vault-Encrypted    | Password prompt detection             |
|16 | Ansible Warnings   | Warning classification                |
|18 | no_log Tasks       | Redaction Layer 1                     |
|19 | Password Fields    | Redaction Layer 2                     |
|24 | User Cancellation  | SIGINT handling                       |