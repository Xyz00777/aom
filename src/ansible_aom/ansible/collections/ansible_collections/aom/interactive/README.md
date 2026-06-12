# aom.interactive

Per-host interactive prompt actions that cooperate with the AOM monitor.

## confirm

Prompts once per host (does not bypass the host loop). Under AOM the prompt is
shown by AOM and the answer routed over a control channel; run bare it falls back
to reading stdin like `ansible.builtin.pause`.
