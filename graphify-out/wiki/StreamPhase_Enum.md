# StreamPhase Enum

> 18 nodes · cohesion 0.14

## Key Concepts

- **json.py** (81 connections) — `src/ansible_aom/formats/json.py`
- **HostCounts** (8 connections) — `src/ansible_aom/formats/json.py`
- **TaskFailure** (8 connections) — `src/ansible_aom/formats/json.py`
- **.handle_completion()** (7 connections) — `src/ansible_aom/formats/json.py`
- **test_rerun.py** (4 connections) — `tests/integration/test_rerun.py`
- **test_run_summary_model_has_pinned_schema()** (4 connections) — `tests/unit/test_json_renderer.py`
- **BaseModel** (3 connections)
- **test_aom_rerun_failed_spawns_with_correct_limit()** (3 connections) — `tests/integration/test_rerun.py`
- **test_aom_rerun_no_failures_exits_1_without_spawning()** (3 connections) — `tests/integration/test_rerun.py`
- **Path** (2 connections)
- **JSON output renderer for AOM (F6).  Implements the Renderer Protocol but produce** (1 connections) — `src/ansible_aom/formats/json.py`
- **Build the RunSummary from accumulated RunState and print as JSON.          ``exi** (1 connections) — `src/ansible_aom/formats/json.py`
- **Per-host status counts aggregated across every task in every play.** (1 connections) — `src/ansible_aom/formats/json.py`
- **One (host, task) pair that ended in FAILED or UNREACHABLE.** (1 connections) — `src/ansible_aom/formats/json.py`
- **End-to-end integration test for `aom rerun`.  Wires the real ``run_playbook`` ag** (1 connections) — `tests/integration/test_rerun.py`
- **`aom rerun --failed --yes` spawns ansible-playbook with --limit web2,web3.** (1 connections) — `tests/integration/test_rerun.py`
- **When the session has no failures, `--failed` exits 1 and never spawns.** (1 connections) — `tests/integration/test_rerun.py`
- **RunSummary captures every field the schema spec requires.** (1 connections) — `tests/unit/test_json_renderer.py`

## Relationships

- [Role Group Task Models](Role_Group_Task_Models.md) (4 shared connections)
- [CLI Interface Tests](CLI_Interface_Tests.md) (4 shared connections)
- [Duration Formatting Helpers](Duration_Formatting_Helpers.md) (4 shared connections)
- [Heartbeat Liveness Tracker](Heartbeat_Liveness_Tracker.md) (3 shared connections)
- [Terminal Row Counting](Terminal_Row_Counting.md) (2 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (2 shared connections)
- [Play Definition Tree Population](Play_Definition_Tree_Population.md) (2 shared connections)
- [Inspect Data Model Builders](Inspect_Data_Model_Builders.md) (2 shared connections)
- [Include Role Discovery](Include_Role_Discovery.md) (2 shared connections)
- [StatusBarConfig Model](StatusBarConfig_Model.md) (2 shared connections)
- [Run Config Key Normalization](Run_Config_Key_Normalization.md) (2 shared connections)
- [test_replay_determinism.py](test_replay_determinism.py.md) (2 shared connections)

## Source Files

- `src/ansible_aom/formats/json.py`
- `tests/integration/test_rerun.py`
- `tests/unit/test_json_renderer.py`

## Audit Trail

- EXTRACTED: 119 (91%)
- INFERRED: 12 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*