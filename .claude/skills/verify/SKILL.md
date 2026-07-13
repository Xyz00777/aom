---
name: verify
description: How to verify aom compact-renderer changes end-to-end — run aom on a real playbook under a PTY, capture raw bytes, count DEC-2026 frames and log lines.
---

# Verifying aom at the terminal surface

The compact renderer's surface is raw stdout bytes on a TTY. Unit tests
capture strings; real verification needs a PTY with a controlled size
and a capture of the raw escape-sequence stream.

## Recipe

```bash
# 1. A storm playbook (loop → rapid v2_runner_item_on_* events):
cat > /tmp/storm.yml <<'EOF'
- hosts: localhost
  gather_facts: false
  tasks:
    - name: storm
      ansible.builtin.debug: {msg: "item {{ item }}"}
      loop: "{{ range(0, 120) | list }}"
EOF

# 2. Run under a PTY with forced size, capture raw bytes.
#    `script` gives a real PTY; stty inside sets the winsize (without it
#    the size is 0x0 → aom falls into degraded plain-log mode).
cd /tmp && script -qec "stty rows 40 cols 120; \
  uv run --project /path/to/ansible-aom aom --no-record -y /tmp/storm.yml" \
  /tmp/aom_raw.bin >/dev/null 2>&1

# 3. Analyze: frames = count of BSU (\x1b[?2026h); log lines via regex.
python3 -c "
data = open('/tmp/aom_raw.bin', 'rb').read().decode(errors='replace')
print('frames:', data.count('\x1b[?2026h'))
print('cursor restored:', '\x1b[?25h' in data)
"
```

## What to check

- **Frame budget**: log-batching caps repaints at ~30 Hz. A 120-item
  storm finishing in ~1s should produce **~15–30 frames**, not 120+.
- **No lost/reordered lines**: every loop item appears exactly once, in
  order. Items render as `ok: [localhost] => (item=N)`.
- **Cursor restored** (`\x1b[?25h`) and final status line present after
  both clean completion and Ctrl-C.
- **Degraded mode**: `stty rows 10 cols 60` → "terminal too small"
  warning, zero BSU frames, all log lines still printed plainly.

## Gotchas

- **Ctrl-C probe**: send SIGINT to the *aom python process only*
  (`ps -ef | grep bin/aom`), never `pkill -f` a pattern matching the
  `uv run` wrapper — killing the wrapper skips aom's cleanup AND leaks
  orphaned `ansible-playbook` children that keep running. Expect exit
  130 + `✖ cancelled by user` + cursor restore.
- `script` must run with cwd outside the repo or it happily works either
  way, but the capture file lands wherever you point it; use /tmp.
- Known pre-existing quirks (don't blame your diff): loop item `0`
  renders as `(item=)` (falsy-zero formatting), and localhost runs emit
  a `[WARNING]: Callback dispatch 'v2_runner_on_start' failed for
  plugin 'aom_connection'` warning.
