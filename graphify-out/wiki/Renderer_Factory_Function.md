# Renderer Factory Function

> 23 nodes · cohesion 0.08

## Key Concepts

- **create_renderer()** (26 connections) — `src/ansible_aom/renderer/factory.py`
- **_resolve_mode()** (5 connections) — `src/ansible_aom/renderer/factory.py`
- **.test_factory_creates_compact_renderer_by_default()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_factory_creates_compact_renderer_when_tui_false()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **.test_factory_creates_tui_renderer_when_tui_true()** (3 connections) — `tests/integration/test_compact_renderer.py`
- **factory.py** (3 connections) — `src/ansible_aom/renderer/factory.py`
- **.test_factory_default_tui_mode_false()** (3 connections) — `tests/unit/test_cli.py`
- **.test_factory_forwards_is_tty_to_compact_renderer()** (3 connections) — `tests/unit/test_cli.py`
- **.test_factory_returns_renderer_for_compact_mode()** (3 connections) — `tests/unit/test_cli.py`
- **.test_factory_returns_renderer_for_tui_mode()** (3 connections) — `tests/unit/test_cli.py`
- **test_factory_tui_mode_still_wins_over_format()** (3 connections) — `tests/unit/test_json_renderer.py`
- **test_factory_compact_format_explicit_returns_compact_renderer()** (2 connections) — `tests/unit/test_json_renderer.py`
- **test_factory_default_format_is_compact()** (2 connections) — `tests/unit/test_json_renderer.py`
- **test_factory_returns_json_renderer_for_json_format()** (2 connections) — `tests/unit/test_json_renderer.py`
- **Default view mode is compact.** (1 connections) — `tests/integration/test_compact_renderer.py`
- **tui_mode=False creates CompactRenderer.** (1 connections) — `tests/integration/test_compact_renderer.py`
- **tui_mode=True creates Textual AOMApp.** (1 connections) — `tests/integration/test_compact_renderer.py`
- **Renderer factory.  One entry point — :func:`create_renderer` — that picks the co** (1 connections) — `src/ansible_aom/renderer/factory.py`
- **TC-005: create_renderer(tui_mode=True) returns AOMApp.** (1 connections) — `tests/unit/test_cli.py`
- **TC-005: create_renderer(tui_mode=False) returns CompactRenderer.** (1 connections) — `tests/unit/test_cli.py`
- **TC-005: create_renderer() defaults to compact renderer.** (1 connections) — `tests/unit/test_cli.py`
- **create_renderer(is_tty=False) constructs a non-TTY CompactRenderer.** (1 connections) — `tests/unit/test_cli.py`
- **tui_mode=True returns AOMApp regardless of format (CLI prevents this combo).** (1 connections) — `tests/unit/test_json_renderer.py`

## Relationships

- [[JSON Renderer]] (5 shared connections)
- [[CLI Interface Tests]] (4 shared connections)
- [[Compact Renderer Integration Tests]] (3 shared connections)
- [[CLI Main Entry Point]] (1 shared connections)
- [[Compact Renderer Implementation]] (1 shared connections)
- [[Replay CLI Subcommand]] (1 shared connections)
- [[Renderer Event Protocol]] (1 shared connections)
- [[AOM TUI Application]] (1 shared connections)
- [[Rerun CLI Entry]] (1 shared connections)

## Source Files

- `src/ansible_aom/renderer/factory.py`
- `tests/integration/test_compact_renderer.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_json_renderer.py`

## Audit Trail

- EXTRACTED: 42 (58%)
- INFERRED: 31 (42%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*