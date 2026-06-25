# AOM JSONL Callback Plugin

> 31 nodes · cohesion 0.07

## Key Concepts

- **project_remaining()** (6 connections) — `docs/superpowers/specs/2026-06-16-run-duration-estimate-design.md`
- **aom_jsonl callback plugin** (5 connections) — `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- **CompactRenderer** (5 connections) — `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- **Item event envelope schema (v2_runner_item_on_ok/failed/skipped)** (4 connections) — `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- **find_previous_run()** (4 connections) — `docs/superpowers/specs/2026-06-16-run-duration-estimate-design.md`
- **RunEstimate dataclass** (4 connections) — `docs/superpowers/specs/2026-06-16-run-duration-estimate-design.md`
- **ansible.posix.jsonl (parent callback)** (2 connections) — `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- **_format_loop_item_line** (2 connections) — `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- **aom inspect replay** (2 connections) — `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- **loop_totals (task_key -> host -> item_count)** (2 connections) — `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- **PriorRun (with loop_totals)** (2 connections) — `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- **runner.py** (2 connections) — `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- **Session sink (event recorder)** (2 connections) — `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- **TreeProjection (TUI)** (2 connections) — `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- **compact/renderer.py** (2 connections) — `docs/superpowers/specs/2026-06-16-run-duration-estimate-design.md`
- **prior_wall_total_s** (2 connections) — `docs/superpowers/specs/2026-06-16-run-duration-estimate-design.md`
- **task_wall_s (per-task wall duration map)** (2 connections) — `docs/superpowers/specs/2026-06-16-run-duration-estimate-design.md`
- **Test playbook: free strategy (10)** (1 connections) — `tests/playbooks/10-free-strategy/site.yml`
- **Test playbook: no_log redaction (18)** (1 connections) — `tests/playbooks/18-no-log-redaction/site.yml`
- **Graceful fallback to ansible.posix.jsonl** (1 connections) — `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- **PtyStreamParser** (1 connections) — `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- **StatusCounts.add_event (ignores item events)** (1 connections) — `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- **_streamed_loop_items dedup set** (1 connections) — `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- **TaskRunState (per-host loop counter)** (1 connections) — `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- **covered_prior_s()** (1 connections) — `docs/superpowers/specs/2026-06-16-run-duration-estimate-design.md`
- *... and 6 more nodes in this community*

## Relationships

- No strong cross-community connections detected

## Source Files

- `docs/superpowers/specs/2026-06-02-live-loop-item-streaming-design.md`
- `docs/superpowers/specs/2026-06-16-run-duration-estimate-design.md`
- `molecule/default/molecule.yml`
- `tests/playbooks/10-free-strategy/site.yml`
- `tests/playbooks/18-no-log-redaction/site.yml`

## Audit Trail

- EXTRACTED: 60 (94%)
- INFERRED: 4 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*