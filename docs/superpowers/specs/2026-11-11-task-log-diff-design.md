# Task-log diff display

Show module-provided changes alongside live compact task results, similar to
Ansible's default callback. Existing Ansible `--diff`/`-D`, task-level diff
configuration, and check mode determine whether modules supply diffs; AOM
renders supplied payloads rather than testing startup arguments. This also
makes recorded diffs visible during replay, whose renderer starts with no
original CLI arguments.

## Scope and behavior

- Print unified hunks immediately below each changed host/item result.
- Support Ansible dict/list diffs with before/after, optional headers, prepared
  output, mapping contents, binary/oversize notices, plus recorded string diffs.
- Preserve unchanged context; use red removed lines, green added lines and cyan
  hunk headers when the renderer enables ANSI colors. Plain output stays plain.
- Respect hidden states and existing streamed-item duplicate suppression.
- Suppress diff content for no-log/censored parent results or items. This
  formatter does not claim to repair the separate unused AOM redaction pipeline.
- Keep task-log result lines and batching behavior intact. No new controls,
  interactive widgets, or changes to inspect's existing changes command.

## Implementation boundaries

Pure diff normalization/unified-hunk generation belongs in `core/diff.py` and
uses Python's standard library. Compact renderer owns indentation/colors and
inserts those lines into existing host/item paths. Both live and replay use
the same renderer. No storage format/index schema changes are needed for this
feature: recorded events already contain module diff payloads.

## Verification

Use exact output assertions for unified hunks, equal input, headers, prepared
text, lists/mappings, missing final newlines, binary/oversize notices and input
immutability. Renderer tests use distinct multi-host and loop-item payloads,
verify attribution/order and exactly-once output, hidden-state suppression,
no-log parent/item suppression, ANSI/plain parity and replay-style empty args.
Run a real check+diff playbook in a temporary directory and the full suite.

## Evidence and decisions

The read-only design researcher recommended the pure formatter plus compact
wiring. Reusing it in inspect immediately would broaden the change; an
interactive diff browser adds navigation state unnecessary for streaming logs.
The initial scope assumes the user means the live compact task log, with the
same display available in replay.

Sources: [Ansible diff mode](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_checkmode.html),
[upstream callback diff formatter](https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/callback/__init__.py),
[JSONL callback](https://github.com/ansible-collections/ansible.posix/blob/main/plugins/callback/jsonl.py).
