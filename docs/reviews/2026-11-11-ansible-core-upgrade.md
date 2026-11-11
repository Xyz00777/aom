# Ansible-core 2.21 and 2.22 compatibility audit

Recommendation: a 2.21 patch update is reasonable; do not describe 2.22 as
fully supported yet. Normal smoke tests pass on 2.22, but its new secret
masking can corrupt the JSONL transport AOM inherits from ansible.posix.

## Current state and release changes

At the start of the audit, `uv.lock` and the shared environment used 2.21.5,
Python is 3.14.8, and CI tests 2.20/2.21. The integration extra initially allowed
`ansible-core>=2.16`; AOM shells out to the user's Ansible executable.

The chosen development/integration range is now `>=2.21.6,<2.22`, so a normal
sync cannot accidentally select 2.22. Existing 2.20 runtime compatibility smoke
coverage remains useful; the integration extra selects the development version.

The patch releases were reviewed individually in the tagged changelog:

| Release | Relevant changes |
|---|---|
| 2.21.1 | Skipped-meta callbacks, free-strategy unreachable handling, role-install security. |
| 2.21.2 | Parallel fact-gathering hangs/timeouts; musl bcrypt formatting. |
| 2.21.3 | Collection downloads/discovery; PowerShell and RPM-key fixes. |
| 2.21.4 | URL-credential masking and tempfile path traversal. |
| 2.21.5 | Connection-directory permissions; DNF5 download destination. |
| 2.21.6 | Galaxy/Git security; run-once facts, URL errors, sudo-rs and BusyBox fixes. |

Only the final row is new relative to the starting checkout. No callback,
preflight, diff or retry API change is listed for that patch. Entries repeated
in the 2.22 changelog are not all new changes from 2.21.5.

[2.21 changelog](https://github.com/ansible/ansible/blob/v2.21.6/changelogs/CHANGELOG-v2.21.rst):
2.21.0 was released May 18, 2026; 2.21.6 on November 2. Notable changes include
registered-result projections and `_task` expressions, stricter collection
compatibility requirements, PowerShell 7 support, removal of the paramiko
connection plugin, and password hashing through libcrypt/libxcrypt. The patch
release includes collection/role installation security fixes. AOM already
supports the 2.21 minor line; isolated checks found no required API changes for
2.21.6.

[2.22 changelog](https://github.com/ansible/ansible/blob/v2.22.0/changelogs/CHANGELOG-v2.22.rst):
2.22.0 was released November 2, 2026. It introduces automatic secret masking
in callback results and Display output. Numeric result values can become
redaction strings. Controller Python support is now 3.13–3.15, dropping 3.12;
AOM's Python 3.14 baseline remains compatible. It also warns about implicit
failure inference from nonzero `rc` and removes older plugin/config options.
Check playbook-specific removals in the changelog before upgrading an inventory.

## Executed checks

A web-enabled research agent used isolated environments, Python 3.14.8 and
ansible.posix 2.2.2, without changing the project lockfile or shared environment.
On both 2.21.6 and 2.22.0:

- 25 selected existing integration cases passed: real-Ansible smoke, callback
  behavior, loop/ignored results, meta tasks, includes/imports/roles, host starts.
- Real preflight found the expected play/host definitions.
- Normal and `--check --diff` probes retained diff payloads and task no-log
  censorship.
- After the narrow retry fix, seven direct callback checks passed.

These are scoped compatibility checks, not full-suite qualification for either
new version.

## Why 2.22 needs more work

A controlled real playbook registered a public dummy secret through the
supported `ansible.builtin.register_secret` filter, then performed a retrying
command. The task run succeeded, but two callback integration defects appeared:

1. The upstream JSONL callback serializes an event, then sends the complete
   string through `Display.display`. On 2.22 that masks the serialized text,
   changing protocol event names/timestamps/identifiers and potentially turning
   unquoted numeric values into invalid JSON. Without registration both tested
   versions emitted eight valid recognized events. With registration on 2.22,
   only two events remained recognizable and one line was invalid JSON.
2. Masked retry counters are strings, so AOM's subtraction raised `TypeError`.
   This independent defect is fixed by retaining the event and emitting a null
   remaining-count hint when either counter is nonnumeric. Integer hints keep
   their existing behavior.

The [official masking developer guide](https://docs.ansible.com/projects/ansible-core/2.22/dev_guide/developing_secret_masking.html)
explicitly describes the invalid-JSON hazard and requires masking values before
serialization. Changing `_result` to `result` does not fix it: `_result` remains
an alias for already-masked results. `Display.display` has no supported masking
bypass argument in 2.22.0, and the beta `ANSIBLE_SUPPORTS_MASKING` escape hatch
was removed. Do not work around this through private Display internals.

Before adding 2.22 to the supported CI matrix, choose a structured-safe output
boundary with upstream JSONL support or a dedicated callback transport, then
add real registered-secret regressions. The retry fix alone does not establish
2.22 support. AOM's separate redaction module is not currently wired into the
production `hosts` event stream and must not be claimed as protection here.

Additional primary sources: [support matrix](https://docs.ansible.com/projects/ansible-core/2.22/reference_appendices/release_and_maintenance.html),
[JSONL callback 2.2.2](https://github.com/ansible-collections/ansible.posix/blob/2.2.2/plugins/callback/jsonl.py),
[Display implementation](https://github.com/ansible/ansible/blob/v2.22.0/lib/ansible/utils/display.py),
[2.22 porting guide](https://docs.ansible.com/projects/ansible-core/devel/porting_guides/porting_guide_core_2.22.html).

## Gates before enabling 2.22

1. Repair the structured-output boundary with a supported mechanism: secrets
   remain masked while serialized event names, IDs, timestamps and numeric
   fields remain valid. Avoid a second whole-text masking pass.
2. Add real registered-secret regressions using public dummy values: short and
   numeric matches, quoted/escaped strings, task no-log, and masked counters.
   Require complete recognizable events and absence of the dummy secret from
   results, diffs, warnings and recordings.
3. Exercise retries, loops, free/serial strategies, includes, and check/diff;
   verify record/replay/inspect preserve their observable results and counts.
4. Verify Python/controller and collection compatibility, and review applicable
   removals against the actual inventories. Run the complete suite under 2.22,
   then add it to CI alongside the retained 2.21 job.

Passing the ordinary smoke tests is insufficient: the current blocker appears
only after secret registration. Retry arithmetic is already guarded, but the
JSONL transport gate remains open work.

## Verified 2.21 patch update

After reviewing the intervening patch notes, the project selected 2.21.6 and
bounded its integration extra below 2.22. Observed full-suite result on 2.21.6:
**3,577 passed, 7 skipped, 3 xfailed, 1 xpassed**; Ruff and mypy pass.

The collection is now installed in the normal Ansible user location. Direct
callback tests initialize Ansible's collection loader as the CLI does, fixing
the push-time collection import failure without requiring temporary PYTHONPATH
settings. The same test collection failed before that bootstrap fix and passes
afterward.
