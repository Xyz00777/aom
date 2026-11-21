# Delegated review follow-ups

The user authorized serial timing, damaged-index recovery, a focused failure
mutation pass, live task-log diffs, and Ansible upgrade research. Work stayed
in the existing checkout with explicit file ownership and parent integration.

## Fixed behavior

- Serial task IDs now accumulate per-occurrence execution windows, excluding
  gaps between batches. Earlier measured time survives unfinished or untimed
  later occurrences. Each occurrence uses the latest host terminal timestamp;
  out-of-order earlier results cannot subtract elapsed time. Zero durations and
  repeated accumulator snapshots remain valid. Runner-start-only free tasks
  keep their existing untimed behavior.
- Index schema version 2 invalidates cached durations. Invalid failed-task
  counts in derived metadata now invalidate freshness and return loader
  fallback results. Inspect rebuilds the disposable index, preserves event
  bytes/mtime, and uses the repaired index rather than parsing the whole log
  on every request.
- A recurring rerun round-trip failure was traced to actual PTY data loss:
  after death, a buffered newline could cause AOM to stop before reading the
  kernel tail. Drainage now continues within one existing short absolute
  deadline. Continuous descendant output cannot rearm it. TIMEOUT fragments
  flush once. A deadline reached after a password-like string inside JSON
  preserves both the saved prefix and unread suffix without prompting.
- Masked retry counters no longer raise subtraction errors. Retry events retain
  the original counters with a null derived remainder when nonnumeric.
- Supplied module diffs appear beneath the owning changed host or item in the
  compact log and replay. No-log/censored payloads stay suppressed, hidden
  states stay hidden, and aggregate results do not repeat streamed item diffs.

## Test-quality evidence

Two failure mutations survived the complete pre-existing suite, each with
3,504 passes and a clean baseline in isolated source copies:

1. Returning UNREACHABLE immediately before finding a later FAILED host.
2. Applying the first host's ignore-errors flag to every host in an event.

Five new mixed-result cases fail these through exact status/message/exit
assertions, including both host orders and host/task/play traversal boundaries.
No production change was needed for these two contracts.

The PTY bug was reproduced with real child processes (three recorded events
from eight emitted), then pinned with deterministic persisted-stream tests.
Each regression was seen failing before the fix. The real reproducer completed
100/100 recordings after the fix. A fresh reviewer added the JSON-password
prefix/deadline regression; that finding changed the implementation.

Five isolated diff mutations failed assertions: missing hunks, ignored result
no-log, ignored aggregate-parent no-log, bypassed hidden state, and repeated
streamed aggregate items. Fresh reviewers also checked 48 synthetic censoring
combinations; their extra failed-host/failed-aggregate cases were added to the
suite. Formatting includes exact hunks/headers/context, mapping order, final
newlines and CRLF normalization.

## Verification and limitations

Observed stable combined suite: **3,577 passed, 7 skipped, 3 xfailed, 1 xpassed**.
Ruff and mypy pass. A real localhost `--check --diff` loop showed each of two
file diffs exactly once while preserving both source files. No coverage ratchet
or project mutation-score gate was added.

Two early worker full runs had missing-collection/environment failures and one
was overlapped by a temporary shared-source mutation. That run was discarded;
subsequent mutation experiments used isolated copies, and the final combined
run followed a stable tree. The real recording failure was investigated rather
than labeled flaky or unrelated.

No cross-model conclusions were available: Claude authentication had failed on
both sandbox and host attempts earlier in the session; fresh-context reviewers
provided the independent checks. Graph and graphify executable are absent.

Ansible 2.21.6 and 2.22.0 each passed 25 selected compatibility cases. Full 2.22
support remains blocked by JSONL whole-text secret masking, despite the retry
counter fix. See [the compatibility audit](https://github.com/Xyz00777/aom/blob/e3b77a936718191459475c57c99b49c91b18aa30/docs/reviews/2026-11-11-ansible-core-upgrade.md).

Remaining decision: successful rescue can leave historical failed results in
JSON's normalized exit/failure projection even when the subprocess succeeds.
Current helper documentation and unsupported-rescued-count notes conflict with
an intuitive process-exit interpretation; this pass did not invent a new
contract for it.
