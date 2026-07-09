# Throttle Investigation — Observations (2026-06-29)

## Question
Can aom detect Ansible playbook `throttle:` from the JSONL stream alone?

## Probe setup
- ansible-core 2.20.4, ansible.posix 2.2.0
- 6 hosts (`-i 'h1,h2,h3,h4,h5,h6,' -c local`)
- 1 task: `ansible.builtin.wait_for: timeout: 1` with `throttle: 2`
- Raw capture: `/tmp/opencode/throttle-probe/{raw.jsonl, raw_free.jsonl, OBSERVATIONS*.md}`

## Verdict from observation

**Ansible emits ZERO structured signal for `throttle:` in JSONL.** Every match
of the word "throttle" in the stream is in human labels (play name, task name,
playbook file path) — not in any structured field.

The throttle value (cap = 2) is **only visible indirectly** via the *timing
pattern* of host events: bursts of N close-together events separated by gaps
much larger than the within-burst gap.

## Observed event stream (linear strategy, 9 events)

| #  | event                          | timestamp offset (ms) | notes                                  |
|----|--------------------------------|-----------------------|----------------------------------------|
| 1  | v2_playbook_on_play_start      | 0                     | single event                           |
| 2  | v2_playbook_on_task_start      | +28                   | `hosts: {}` — empty, no per-host info  |
| 3  | v2_runner_on_ok (h2)           | +2784                 | wave 1                                 |
| 4  | v2_runner_on_ok (h1)           | +2853                 | wave 1 (+69ms)                         |
| 5  | v2_runner_on_ok (h3)           | +5091                 | wave 2 (+2238ms gap from prev)         |
| 6  | v2_runner_on_ok (h4)           | +5112                 | wave 2 (+21ms)                         |
| 7  | v2_runner_on_ok (h5)           | +7290                 | wave 3 (+2179ms gap from prev)         |
| 8  | v2_runner_on_ok (h6)           | +7325                 | wave 3 (+35ms)                         |
| 9  | v2_playbook_on_stats           | +7330                 | single event                           |

`v2_runner_on_start` count: **0** under linear.

## Observed event stream (free strategy, 14 events)

| #  | event                          | notes                                  |
|----|--------------------------------|----------------------------------------|
| 1  | v2_playbook_on_play_start      | single                                 |
| 2  | v2_runner_on_start             | `hosts: {}` — empty                    |
| 3  | v2_runner_on_start             |                                        |
| 4  | v2_runner_on_start             | wave 2 begins (3rd and 4th hosts queued)|
| 5  | v2_runner_on_ok (h2)           | wave 1                                 |
| 6  | v2_runner_on_ok (h1)           | wave 1                                 |
| 7  | v2_runner_on_start             | wave 2 second host starts              |
| 8  | v2_runner_on_ok (h3)           | wave 2                                 |
| 9  | v2_runner_on_start             | wave 3 first host starts               |
| 10 | v2_runner_on_ok (h4)           | wave 2                                 |
| 11 | v2_runner_on_start             | wave 3 second host starts              |
| 12 | v2_runner_on_ok (h5)           | wave 3                                 |
| 13 | v2_runner_on_ok (h6)           | wave 3                                 |
| 14 | v2_playbook_on_stats           |                                        |

`v2_runner_on_start` count: **6** under free (one per host, regardless of
throttle). `v2_playbook_on_task_start` count: **0** under free.

**Conclusion**: `v2_runner_on_start` is gated by the lockstep check in the
callback source (`jsonl.py:121-123` — `if self._is_lockstep: return`). Throttle
does not suppress it; strategy does.

## Key insights for aom

1. **No payload field carries throttle.** Detection must come from timing or
   from external knowledge (the playbook file itself).

2. **Wave structure is real and observable.** A 500ms gap threshold cleanly
   separates 2-host waves. Within a wave: ~20-70ms; between waves: ~2.2s.

3. **The wave size equals the throttle cap** under both strategies. (With
   `throttle: 2` and 6 hosts, every burst was exactly 2 events.) This is the
   *only* way to infer the cap value from the stream.

4. **Per-host start time under linear** is *not* in the stream — there's only
   a single shared `task.duration.start` from `v2_playbook_on_task_start`.
   Under free, `v2_runner_on_start` events fire but `hosts: {}` is empty
   (host attribution must be inferred by ordering).

5. **False positive risk**: a "burst pattern" can also be produced by
   `serial: N` at the play level (which serializes plays in batches), or by a
   task whose underlying module just happens to be slow across all hosts.
   Pure timing-based detection will produce wrong badges in those cases.

## Decision space

| Approach                          | Cost         | Accuracy | When useful                          |
|-----------------------------------|--------------|----------|--------------------------------------|
| **YAML parse playbook file**      | new dep      | exact    | ground truth, no heuristics          |
| **Stream-infer from timing**      | none         | heuristic| fallback only — confusable w/ serial |
| **Hybrid: parse + live wave data**| new dep      | exact    | recommended — best of both           |

Recommend: hybrid. YAML parse at preflight populates `TaskDefinition.throttle`,
live event timing confirms wave progress at runtime.

## Red-bar TDD test landed (2026-06-29)

The failing test driving the implementation is
`tests/integration/test_throttle.py` — three test methods, all
intentionally failing on missing features:

- `test_throttle_cap_recorded_on_task_definition`: fails because
  `meta.json` does NOT persist `run_state`/`definitions`/`preflight`
  payloads — only the bare counts (`preflight_task_count`,
  `resolved_host_count`). Today the recorded keys are:
  `[playbook, ansible_args, start_time, version, session_id, status,
  end_time, duration_seconds, preflight_task_count, resolved_host_count]`.
  The implementation must extend meta.json to carry enough run state
  for inspection, or expose it another way.
- `test_wave_progress_records_three_waves`: fails because no
  `wave_progress` field exists anywhere in the session state.
- `test_wave_assignment_matches_host_bursts`: the burst-pattern sanity
  check PASSES on the captured stream (observed: 3 waves of 2 hosts);
  the test then fails on `wave_progress.per_host` being absent.

### Fixture placement

The probe playbook was promoted from `/tmp/opencode/throttle-probe/`
to the repo at `.sisyphus/test-fixtures/with_throttle.yml`. Trailing
newline stripped (last byte `0x32` = `2`, matches the probe).
Inventory: `-i 'h1,h2,h3,h4,h5,h6,' -c local` — same as the probe.

### Style and isolation

- Mirrors `test_real_ansible.py`'s helpers verbatim
  (`_NEEDS_ANSIBLE`, `_run_aom`, `_find_session`,
  `_parse_jsonl_through_core`) — kept local rather than imported so
  the test file reads standalone.
- `meta.json` probe under multiple keys
  (`run_state`/`definitions`/`preflight`) intentionally — the test
  asserts the contract, not the storage schema. Whichever key the
  implementation chooses satisfies it.
- Live-ansible skip gate works as expected: 3 tests run against real
  ansible-playbook, take ~30s end-to-end. Existing
  `test_real_ansible.py` still passes (3 passed in 27s).

### One subtle bug found mid-write

The `v2_runner_on_ok` events in the recorded stream carry the host
inside the `event["hosts"]` dict (`{"h1": {...}, "h2": {...}}`),
NOT in a top-level `event["host"]` field. The first draft of the
wave-assignment test assumed the latter; `ok_events` came back empty
and the burst-pattern sanity check tripped before reaching the real
contract assertion. Fixed by walking `hosts.items()` and emitting one
`(host, ts)` tuple per host per event. Worth noting because any
future wave-aware code will hit the same field-shape issue.

### Next step (green path)

Implementation must:
1. Add `throttle: int | None` to `TaskDefinition` (or equivalent on
   `PlayRunState.tasks[task_id]`).
2. Persist enough run state in `meta.json` to expose per-task defs
   (or expose them via `aom inspect` without changing meta.json).
3. Add a `WaveProgress` structure (or equivalent) carrying
   `wave_count` and `per_host: dict[str, int]`, populated either at
   preflight (YAML parse) or runtime (burst inference).
