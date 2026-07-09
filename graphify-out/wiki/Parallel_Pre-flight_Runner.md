# Parallel Pre-flight Runner

> 29 nodes · cohesion 0.12

## Key Concepts

- **test_rerun_roundtrip.py** (12 connections) — `tests/integration/test_rerun_roundtrip.py`
- **_make_capture_build_command()** (8 connections) — `tests/integration/test_rerun_roundtrip.py`
- **Path** (8 connections)
- **_record_live_session()** (8 connections) — `tests/integration/test_rerun_roundtrip.py`
- **_read_argv()** (6 connections) — `tests/integration/test_rerun_roundtrip.py`
- **.test_changes_only_limit_is_just_changed_hosts()** (6 connections) — `tests/integration/test_rerun_roundtrip.py`
- **.test_failed_limit_contains_only_failed_hosts()** (6 connections) — `tests/integration/test_rerun_roundtrip.py`
- **.test_unreachable_limit_includes_failed_and_unreachable()** (6 connections) — `tests/integration/test_rerun_roundtrip.py`
- **_mixed_outcome_events()** (4 connections) — `tests/integration/test_rerun_roundtrip.py`
- **TestRerunRoundtripRefusal** (4 connections) — `tests/integration/test_rerun_roundtrip.py`
- **.test_null_ansible_args_also_refused()** (4 connections) — `tests/integration/test_rerun_roundtrip.py`
- **_fake_ansible_command()** (3 connections) — `tests/integration/test_rerun_roundtrip.py`
- **TestRerunRoundtripChangesOnly** (3 connections) — `tests/integration/test_rerun_roundtrip.py`
- **TestRerunRoundtripFailed** (3 connections) — `tests/integration/test_rerun_roundtrip.py`
- **.test_missing_ansible_args_refuses_without_spawning()** (3 connections) — `tests/integration/test_rerun_roundtrip.py`
- **TestRerunRoundtripUnreachable** (3 connections) — `tests/integration/test_rerun_roundtrip.py`
- **_unreachable_events()** (3 connections) — `tests/integration/test_rerun_roundtrip.py`
- **End-to-end round-trip for ``aom rerun`` (Item #4).  Exercises the full pipeline:** (1 connections) — `tests/integration/test_rerun_roundtrip.py`
- **Read the captured argv lines emitted by the capture-shim.      When CPython is i** (1 connections) — `tests/integration/test_rerun_roundtrip.py`
- **Events flagging web2/web3 as failed, web1 as changed, web4 as ok.** (1 connections) — `tests/integration/test_rerun_roundtrip.py`
- **Events flagging web5 as unreachable plus web2/web3 as failed.** (1 connections) — `tests/integration/test_rerun_roundtrip.py`
- **Record → rerun --failed → assert spawn argv.** (1 connections) — `tests/integration/test_rerun_roundtrip.py`
- **``--unreachable`` returns failed ∪ unreachable hosts.** (1 connections) — `tests/integration/test_rerun_roundtrip.py`
- **``--changes-only`` requires runner_on_ok events with changed=true.** (1 connections) — `tests/integration/test_rerun_roundtrip.py`
- **Old-format session (no ansible_args) → exit 2, no spawn.** (1 connections) — `tests/integration/test_rerun_roundtrip.py`
- *... and 4 more nodes in this community*

## Relationships

- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)
- [Tree Block Animation](Tree_Block_Animation.md) (1 shared connections)

## Source Files

- `tests/integration/test_rerun_roundtrip.py`

## Audit Trail

- EXTRACTED: 101 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*