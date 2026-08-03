# TestFormatFlag

> 10 nodes · cohesion 0.20

## Key Concepts

- **TestFormatFlag** (15 connections) — `tests/unit/test_cli.py`
- **.test_format_flag_does_not_appear_in_ansible_args()** (3 connections) — `tests/unit/test_cli.py`
- **.test_main_dispatches_json_renderer_when_format_json()** (3 connections) — `tests/unit/test_cli.py`
- **.test_format_flag_accepts_compact_explicit()** (2 connections) — `tests/unit/test_cli.py`
- **.test_format_flag_accepts_json()** (2 connections) — `tests/unit/test_cli.py`
- **.test_format_flag_defaults_to_compact()** (2 connections) — `tests/unit/test_cli.py`
- **.test_format_flag_rejects_unknown_value()** (2 connections) — `tests/unit/test_cli.py`
- **Tests for F6: --format {compact,json} flag.** (1 connections) — `tests/unit/test_cli.py`
- **--format is consumed by argparse, not forwarded to ansible-playbook.** (1 connections) — `tests/unit/test_cli.py`
- **`aom --format json playbook.yml` constructs a JsonRenderer.** (1 connections) — `tests/unit/test_cli.py`

## Relationships

- [HostRunState](HostRunState.md) (7 shared connections)
- [create_parser](create_parser.md) (5 shared connections)
- [CompactRenderer](CompactRenderer.md) (1 shared connections)
- [RunState](RunState.md) (1 shared connections)

## Source Files

- `tests/unit/test_cli.py`

## Audit Trail

- EXTRACTED: 19 (59%)
- INFERRED: 13 (41%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*