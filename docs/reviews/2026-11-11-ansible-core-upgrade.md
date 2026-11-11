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

These initial checks were scoped compatibility probes. The follow-up below
records full-suite results and their limits.

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

## Follow-up: 2.22 readiness checklist

Decision: retain `>=2.21.6,<2.22`. Defer the callback transport decision and
2.22 support. No dependency, callback or event-schema change is included in
this follow-up.

The follow-up used application-stack commit
`e3b77a936718191459475c57c99b49c91b18aa30` (PR #68), Python 3.14.8,
ansible.posix 2.2.2 and separate temporary environments for each core version.
`NO_COLOR` was unset consistently. The independent test-quality PR #61 is not
part of this base, so these totals differ from the combined review branch.

| Gate | Observed result | Remaining work |
|---|---|---|
| Full suite | Both 2.21.6 and 2.22.0: 3,569 passed, 7 skipped, 3 xfailed, 1 xpassed. | Green existing tests do not qualify registered-secret behavior. |
| Free and serial strategies | Both versions: two hosts, six loop-item events, three named tasks including a dynamic include, correct per-host recaps. | Preserve these semantics in a future callback change. |
| Check/diff and no-log | Both versions: two visible diffs, two censored results, unchanged original files, expected changed/ok counts. | Add registered-secret and mixed visible/censored-item cases. |
| Ordinary live/record/replay/inspect | All commands exit zero on both versions and retain expected outcomes. | Assert the same event census and outcomes with secret registration. |
| Registered-secret transport | 2.22 fails with a public dummy numeric value: 11 valid raw JSON lines, one invalid recap line, only two recognized events. | Replace the whole-serialized-text masking boundary. |
| Masked result keys | On 2.22, registering `changed` makes genuinely changed hosts appear OK; registering `results` loses loop total 3 even though all six task loop-item events arrive. Both playbooks assert the correct underlying Ansible result successfully. The 2.21 baseline retains the expected state. | Preserve control fields independently of masked payload keys. A writer-only fix is insufficient. |
| Colliding host labels | On 2.22, registering the synthetic host names `first` and `second` collapses both to the same label. The recap has duplicate JSON keys and decoding loses a host. The 2.21 baseline preserves both identities. | Choose an identity/label policy before changing the output boundary. |
| Recorded masked run | AOM reports 0/2 hosts and 0/2 tasks. The malformed recap is dropped; replay and inspect also exit zero, without host statistics. | Detect event loss; command exit status and parseable recordings are insufficient oracles. |
| Python and collection loading | Both isolated full suites collect and run with the normal installed collection. | Add a 2.22 CI job only after the masking gates pass. |
| Real inventory compatibility | Not checked; probes use synthetic local playbooks. | Review inventory-specific removals and collection requirements before an operational upgrade. |

Both full-suite logs also contain an ignored interpreter-finalization
`OSError: Bad file descriptor`. Both processes exit zero; its cause was not
diagnosed, so these runs are not described as warning-free.

### Regression tests to prepare before enabling 2.22

Use only public dummy strings. Assert complete, recognizable events and correct
state, rather than merely valid JSON, absence of a dummy string, or exit zero.

- Register a short numeric dummy; preserve event kinds, IDs, timestamps and
  recap counters while masking user payloads. Check retry counters without
  assuming their masked values are numeric.
- Register dummy strings matching result keys, such as `changed` and `results`.
  The public result mapping is already masked and may lose those keys. Pin
  changed/failed/skipped/unreachable outcomes and loop counts. The public
  status methods expose operational state independently of masked payloads;
  do not recover it through private unmasked result data.
- Cover quotes, backslashes, Unicode, diffs, warnings, task names and paths;
  check task no-log and mixed visible/censored loop items.
- Exercise two host labels that mask to the same text. They must remain two
  distinct hosts with correct counts in live, replay and inspect views.
- Keep the existing free/serial/include/check/diff cases and compare their
  live, recorded and inspected semantics under masking.

Assertions must distinguish protocol metadata from user content. For example,
registering the dummy `2` does not justify asserting that the byte `2` is
absent from timestamps, event names and counters. Use field-specific checks,
plus a distinctive long dummy for whole-artifact absence checks.

### Decisions deliberately left open

The smallest transport candidate is an AOM-owned stdout writer that masks
selected user content before serialization. A dedicated event channel is an
alternative with additional process-lifecycle, ordering and buffering work.
Neither is implemented or approved here. Moving the channel alone does not
solve masking or preserve operational fields.

Host names currently serve as both visible labels and executable inventory
identities for rerun `--limit`. Keeping raw names would require an explicit
exception when a name matches a registered secret. Masking names can collapse
distinct hosts and break reruns; separating identities from labels would
require an event/storage design. Do not silently choose either policy.

The independent review refined the initial suggestion that every host name
must be masked: upstream permits selective masking, but does not grant host
names an automatic exception. That review added a verification requirement
and identified a policy choice; it did not authorize a schema change.

Recording protection also needs an explicit scope. Source inspection shows
that session metadata retains original CLI arguments for reruns, generic
interactive answers are recorded, and preflight runs before runtime secret
registration. No real secret was read or tested. Fixing the callback alone
must not be described as guaranteeing secret-free recordings; changing these
other paths can affect rerun behavior and is separate work.

The [2.22 developer guide](https://docs.ansible.com/projects/ansible-core/2.22/dev_guide/developing_secret_masking.html)
documents selective pre-serialization masking and the invalid-JSON hazard.
The [user guide](https://docs.ansible.com/projects/ansible-core/2.22/playbook_guide/playbooks_secret_masking.html)
documents callback responsibilities and best-effort limits. The
[public callback result implementation](https://github.com/ansible/ansible/blob/v2.22.0/lib/ansible/executor/task_result.py)
separates masked payload access from status methods.

Local reproducibility evidence from this session lives under
`/tmp/aom-upgrade-probe/`: `readiness-full-v222.log`, and
`workflows-v221/` / `workflows-v222/`. The final 2.21.6 verification log is
`/tmp/aom-final-readiness-v221.log`.
The supported registered-key and host-collision playbooks, raw output and
semantic summaries are in `key-probes-v221/` and `key-probes-v222/`.
These temporary artifacts are not shipped and may be deleted; the observations
and required regression cases above are the durable record.
