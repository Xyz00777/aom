# Architecture Layering Tests

> 14 nodes · cohesion 0.21

## Key Concepts

- **test_layering.py** (9 connections) — `tests/unit/test_layering.py`
- **_violations()** (6 connections) — `tests/unit/test_layering.py`
- **_imports_in()** (5 connections) — `tests/unit/test_layering.py`
- **_module_name_for()** (3 connections) — `tests/unit/test_layering.py`
- **test_core_does_not_depend_on_infrastructure()** (3 connections) — `tests/unit/test_layering.py`
- **test_drivers_do_not_depend_on_concrete_renderers()** (3 connections) — `tests/unit/test_layering.py`
- **test_renderer_protocol_does_not_import_concrete_renderers()** (3 connections) — `tests/unit/test_layering.py`
- **_iter_modules()** (2 connections) — `tests/unit/test_layering.py`
- **test_concrete_renderers_do_not_cross_import()** (2 connections) — `tests/unit/test_layering.py`
- **Architecture layering enforcement (ARCHITECTURE.md §7.8).  These tests parse eve** (1 connections) — `tests/unit/test_layering.py`
- **``renderer/protocol.py`` is the port; it must stay abstract.** (1 connections) — `tests/unit/test_layering.py`
- **``drivers/`` couples to the Renderer Protocol, not to a concrete impl.      The** (1 connections) — `tests/unit/test_layering.py`
- **Return every ansible_aom.* module name imported by ``path``.      Walks the AST** (1 connections) — `tests/unit/test_layering.py`
- **``core/`` must not import any infrastructure package.      This is the load-bear** (1 connections) — `tests/unit/test_layering.py`

## Relationships

- [[Run Config Key Normalization]] (3 shared connections)

## Source Files

- `tests/unit/test_layering.py`

## Audit Trail

- EXTRACTED: 41 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*