# Rerun CLI Parser

> 18 nodes · cohesion 0.20

## Key Concepts

- **test_inspect_debug.py** (14 connections) — `tests/unit/test_inspect_debug.py`
- **format_diagnostics_section()** (7 connections) — `src/ansible_aom/inspect/formatters.py`
- **Path** (7 connections)
- **_write_session()** (7 connections) — `tests/unit/test_inspect_debug.py`
- **test_inspect_debug_json_emits_raw_record()** (4 connections) — `tests/unit/test_inspect_debug.py`
- **test_inspect_debug_json_legacy_session_outputs_null()** (3 connections) — `tests/unit/test_inspect_debug.py`
- **test_inspect_debug_on_legacy_session_prints_fallback()** (3 connections) — `tests/unit/test_inspect_debug.py`
- **test_inspect_debug_prints_histogram()** (3 connections) — `tests/unit/test_inspect_debug.py`
- **test_inspect_debug_with_specific_session_id()** (3 connections) — `tests/unit/test_inspect_debug.py`
- **test_format_diagnostics_recording_disabled_surfaces_reason()** (2 connections) — `tests/unit/test_inspect_debug.py`
- **test_format_diagnostics_section_with_full_record()** (2 connections) — `tests/unit/test_inspect_debug.py`
- **test_format_diagnostics_section_with_none_returns_fallback()** (2 connections) — `tests/unit/test_inspect_debug.py`
- **test_inspect_debug_no_sessions()** (2 connections) — `tests/unit/test_inspect_debug.py`
- **Any** (1 connections)
- **Render the ``diagnostics.json`` payload as a plain-text section.      Returns a** (1 connections) — `src/ansible_aom/inspect/formatters.py`
- **Phase 6: ``aom inspect --debug`` prints diagnostics.json contents.  Spec: docs/s** (1 connections) — `tests/unit/test_inspect_debug.py`
- **``--debug --json`` writes the diagnostics record as a single JSON     object for** (1 connections) — `tests/unit/test_inspect_debug.py`
- **_reset()** (1 connections) — `tests/unit/test_inspect_debug.py`

## Relationships

- [Status Bar Widget](Status_Bar_Widget.md) (1 shared connections)
- [Color ASCII Fallback](Color_ASCII_Fallback.md) (1 shared connections)
- [Frame Parameter Handling](Frame_Parameter_Handling.md) (1 shared connections)
- [StreamPhase Enum](StreamPhase_Enum.md) (1 shared connections)

## Source Files

- `src/ansible_aom/inspect/formatters.py`
- `tests/unit/test_inspect_debug.py`

## Audit Trail

- EXTRACTED: 57 (89%)
- INFERRED: 7 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*