# Verbosity Research Findings (2026-06-29)

Empirical test: ran `/tmp/opencode/verbosity-test/test.yml` against `ANSIBLE_STDOUT_CALLBACK=ansible.posix.jsonl` at -v through -vvvvvv.

## Headline result

**The ansible.posix.jsonl callback emits the same events regardless of `-v` level.** Verbosity only changes the non-JSON boot/loader verbose lines printed before the playbook actually runs. It does NOT add/remove/gate any field inside JSONL events.

## Evidence

- 10 JSONL events emitted at every level (-v .. -vvvvvv) for the 4-task playbook.
- Event-by-event size in bytes is identical at every level (e.g. `v2_runner_on_failed` = 997 bytes at all six levels).
- Stripping `_timestamp`, `play.id`, `task.id`, and `*.duration.*` (run-dependent noise), the normalized event payloads are byte-identical across all six levels.
- No `verbosity`, `v`, or `level` field appears in any event (top-level or nested).

## Why the per-level file sizes differ

Stdout file size grows 4.6KB -> 13.7KB from -v to -vvvvv, but the JSONL count is unchanged. The growth is from ansible's *own* verbose boot logs (config file search, plugin loading messages, etc.) printed BEFORE the JSONL stream starts.

Practical filter: a consumer only has to keep lines that start with `{` and parse as JSON.

## Verbosity-gated fields (the answer the question was after)

There ARE no verbosity-gated fields inside the JSONL callback. The callback writes a fixed schema per event type.

What changes by verbosity is:
- Default Ansible display callback (jsonl inherits the standard `result._ansible_verbose_always`, `_ansible_no_log` flags, but those are properties of the task/module, not verbosity).
- `module_args` is included in `invocation` for every runner event regardless of level (already visible at -v in our run).
- `invocation.module_args` is stripped when `no_log: true` is set on the task — independent of verbosity.

## no_log behavior (verified)

- Without `no_log`: `hosts.localhost` includes `cmd`, `stdout`, `stderr`, `invocation.module_args`, `msg` (containing secrets) verbatim.
- With `no_log: true`: result replaced with single field `censored: "the output has been hidden due to the fact that 'no_log: true' was specified for this result"` plus `_ansible_no_log: true`. Even the `exception` field is included but the cmd/stdout are not.
- Verbosity level has NO effect on no_log redaction.

## Failure event shape

`v2_runner_on_failed` at -v includes: `_ansible_no_log, action, changed, cmd, delta, end, exception, failed, failed_when_result, invocation, msg, rc, start, stderr, stderr_lines, stdout, stdout_lines`. Identical at -vvvvv.

## Implications for AOM

1. AOM does NOT need to track `-v` separately from what JSONL exposes — there is no hidden content to discover.
2. The single source of truth for what happened is `invocation.module_args`, `result.*`, and the `_ansible_*` flags — all present at every verbosity level.
3. Filtering stdout to JSONL is trivial: `line.startswith('{')` then `json.loads`. Boot logs at -vvvvv produce dozens of non-JSON lines that must be discarded.
4. `no_log` redaction happens automatically in the callback; AOM does not need its own secret-pattern redaction for the JSONL stream.