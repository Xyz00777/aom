# View Mode Selection

> 21 nodes · cohesion 0.15

## Key Concepts

- **test_redaction_redteam_fixture.py** (13 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **Any** (8 connections)
- **_build_config()** (6 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **_load_fixture()** (5 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **test_fixture_does_not_leak_plaintext_secrets()** (5 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **test_redaction_redteam_row()** (5 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **redteam_cases()** (4 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **test_fixture_covers_required_categories()** (3 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **test_fixture_has_at_least_30_rows()** (3 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **test_fixture_iter()** (3 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **_id_from_row()** (2 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **RedactionConfig** (1 connections)
- **Table-driven red-team fixture test for the QC-002 redaction rewrite.  This file** (1 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **Defense-in-depth: every SHOULD_REDACT row must end with the literal     ``REDACT** (1 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **Sanity: the fixture loads as a list (ad-hoc debugging entry point).** (1 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **Load and parse the red-team JSONL fixture.** (1 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **Build a RedactionConfig from the row's ``config`` field.** (1 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **Module-scoped fixture: parse the JSONL once for the whole module.** (1 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **Each fixture row is a full redaction contract test.** (1 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **Sanity: the red-team corpus must be a real corpus, not a stub.** (1 connections) — `tests/unit/test_redaction_redteam_fixture.py`
- **Sanity: the corpus must include at least the four QC-002 categories.      - exac** (1 connections) — `tests/unit/test_redaction_redteam_fixture.py`

## Relationships

- [TUI Tree View Tests](TUI_Tree_View_Tests.md) (2 shared connections)
- [Task Definition Live Refresh](Task_Definition_Live_Refresh.md) (1 shared connections)
- [Inspect TUI Widget Data](Inspect_TUI_Widget_Data.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `tests/unit/test_redaction_redteam_fixture.py`

## Audit Trail

- EXTRACTED: 65 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*