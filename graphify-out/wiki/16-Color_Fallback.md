# 16-Color Fallback

> 25 nodes · cohesion 0.09

## Key Concepts

- **_safe_loads()** (10 connections) — `src/ansible_aom/core/parser.py`
- **.feed_line()** (9 connections) — `src/ansible_aom/core/parser.py`
- **._handle_plaintext()** (7 connections) — `src/ansible_aom/core/parser.py`
- **._parse_and_return()** (5 connections) — `src/ansible_aom/core/parser.py`
- **.feed_line()** (4 connections) — `src/ansible_aom/core/parser.py`
- **._handle_connection_event()** (4 connections) — `src/ansible_aom/core/parser.py`
- **._is_json()** (4 connections) — `src/ansible_aom/core/parser.py`
- **._is_jsonl_start_event()** (4 connections) — `src/ansible_aom/core/parser.py`
- **._is_jsonl_stats_event()** (4 connections) — `src/ansible_aom/core/parser.py`
- **_has_surrogate_codepoint()** (3 connections) — `src/ansible_aom/core/parser.py`
- **._parse_json()** (3 connections) — `src/ansible_aom/core/parser.py`
- **._resolve_connection()** (3 connections) — `src/ansible_aom/core/parser.py`
- **Any** (1 connections)
- **Parse a line and return zero or more events.** (1 connections) — `src/ansible_aom/core/parser.py`
- **Parse JSON line and return events.** (1 connections) — `src/ansible_aom/core/parser.py`
- **Classify and handle non-JSON lines from PTY stream.          Real ansible-playbo** (1 connections) — `src/ansible_aom/core/parser.py`
- **Update connection tracking state from a connection event.          Intercepts ``** (1 connections) — `src/ansible_aom/core/parser.py`
- **Resolve connection_id and attribution_confidence for a stderr line.          Arg** (1 connections) — `src/ansible_aom/core/parser.py`
- **Check if line is a JSONL start event.          Accepts both v2_playbook_on_start** (1 connections) — `src/ansible_aom/core/parser.py`
- **Check if line is a v2_playbook_on_stats event.** (1 connections) — `src/ansible_aom/core/parser.py`
- **Check if line is valid JSON.** (1 connections) — `src/ansible_aom/core/parser.py`
- **Parse a JSON line into a dict.** (1 connections) — `src/ansible_aom/core/parser.py`
- **True if ``s`` contains any surrogate codepoint (U+D800..U+DFFF).      R6: pexpec** (1 connections) — `src/ansible_aom/core/parser.py`
- **Parse one JSONL line, picking orjson or stdlib json by content.      R6: orjson** (1 connections) — `src/ansible_aom/core/parser.py`
- **Parse a line and return zero or more JSON events.          Returns empty list fo** (1 connections) — `src/ansible_aom/core/parser.py`

## Relationships

- [Run State Completion Recap](Run_State_Completion_Recap.md) (9 shared connections)
- [Status Icon Animation Tests](Status_Icon_Animation_Tests.md) (5 shared connections)
- [Role Group Task Models](Role_Group_Task_Models.md) (2 shared connections)
- [Three-Pane Inspect App](Three-Pane_Inspect_App.md) (1 shared connections)
- [AOM TUI Application](AOM_TUI_Application.md) (1 shared connections)
- [Prompt Detection Heuristics](Prompt_Detection_Heuristics.md) (1 shared connections)

## Source Files

- `src/ansible_aom/core/parser.py`

## Audit Trail

- EXTRACTED: 72 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*