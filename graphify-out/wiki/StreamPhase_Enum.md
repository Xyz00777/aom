# StreamPhase Enum

> 17 nodes · cohesion 0.13

## Key Concepts

- **json.py** (66 connections) — `src/ansible_aom/formats/json.py`
- **test_no_eof_hang.py** (5 connections) — `tests/integration/test_no_eof_hang.py`
- **test_rerun.py** (4 connections) — `tests/integration/test_rerun.py`
- **_fake_ansible_hangs_after_stats()** (3 connections) — `tests/integration/test_no_eof_hang.py`
- **test_runner_finishes_promptly_on_clean_eof()** (3 connections) — `tests/integration/test_no_eof_hang.py`
- **test_runner_returns_within_bounded_time_when_child_hangs_after_stats()** (3 connections) — `tests/integration/test_no_eof_hang.py`
- **test_aom_rerun_failed_spawns_with_correct_limit()** (3 connections) — `tests/integration/test_rerun.py`
- **test_aom_rerun_no_failures_exits_1_without_spawning()** (3 connections) — `tests/integration/test_rerun.py`
- **Path** (2 connections)
- **JSON output renderer for AOM (F6).  Implements the Renderer Protocol but produce** (1 connections) — `src/ansible_aom/formats/json.py`
- **Batch E item #10c — R8 no-EOF hang protection.  A misbehaved (or hung) ansible-p** (1 connections) — `tests/integration/test_no_eof_hang.py`
- **Sanity baseline: when the child cleanly exits after emitting all     events, the** (1 connections) — `tests/integration/test_no_eof_hang.py`
- **Build a fake-ansible command that emits events then sleeps without     closing s** (1 connections) — `tests/integration/test_no_eof_hang.py`
- **R8 regression marker: the runner must not wait indefinitely on a     hung child** (1 connections) — `tests/integration/test_no_eof_hang.py`
- **End-to-end integration test for `aom rerun`.  Wires the real ``run_playbook`` ag** (1 connections) — `tests/integration/test_rerun.py`
- **`aom rerun --failed --yes` spawns ansible-playbook with --limit web2,web3.** (1 connections) — `tests/integration/test_rerun.py`
- **When the session has no failures, `--failed` exits 1 and never spawns.** (1 connections) — `tests/integration/test_rerun.py`

## Relationships

- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (3 shared connections)
- [Terminal Row Counting](Terminal_Row_Counting.md) (2 shared connections)
- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (2 shared connections)
- [JSON Renderer](JSON_Renderer.md) (2 shared connections)
- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (2 shared connections)
- [Hide State Normalization](Hide_State_Normalization.md) (2 shared connections)
- [Community 602](Community_602.md) (2 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (1 shared connections)
- [Loop Item Line Tests](Loop_Item_Line_Tests.md) (1 shared connections)
- [RunSummary Schema Contract](RunSummary_Schema_Contract.md) (1 shared connections)
- [ASCII Status Icon Fallback](ASCII_Status_Icon_Fallback.md) (1 shared connections)
- [Test Event Fixtures](Test_Event_Fixtures.md) (1 shared connections)

## Source Files

- `src/ansible_aom/formats/json.py`
- `tests/integration/test_no_eof_hang.py`
- `tests/integration/test_rerun.py`

## Audit Trail

- EXTRACTED: 99 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*