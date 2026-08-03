# Psutil Safe Probe

> 9 nodes · cohesion 0.31

## Key Concepts

- **_renderer_with_running_task()** (10 connections) — `tests/compact/test_preserve_tree_on_cancel.py`
- **test_preserve_tree_on_cancel.py** (7 connections) — `tests/compact/test_preserve_tree_on_cancel.py`
- **test_tree_not_duplicated_on_clean_exit()** (3 connections) — `tests/compact/test_preserve_tree_on_cancel.py`
- **test_tree_printed_after_cancel()** (3 connections) — `tests/compact/test_preserve_tree_on_cancel.py`
- **test_tree_printed_after_failure()** (3 connections) — `tests/compact/test_preserve_tree_on_cancel.py`
- **On Ctrl-C / failure exit, the compact panel's tree + host overview must persist** (1 connections) — `tests/compact/test_preserve_tree_on_cancel.py`
- **Exit 130 (Ctrl-C) → tree + host snapshot lands in scrollback.** (1 connections) — `tests/compact/test_preserve_tree_on_cancel.py`
- **Non-zero exit on a "failed" state preserves the panel too.** (1 connections) — `tests/compact/test_preserve_tree_on_cancel.py`
- **A clean exit omits the tree snapshot — the host table still prints     for per-h** (1 connections) — `tests/compact/test_preserve_tree_on_cancel.py`

## Relationships

- [HostRunState](HostRunState.md) (4 shared connections)
- [renderer.py](renderer.py.md) (1 shared connections)
- [CompactRenderer](CompactRenderer.md) (1 shared connections)
- [TaskDefinition](TaskDefinition.md) (1 shared connections)
- [PlayDefinition](PlayDefinition.md) (1 shared connections)

## Source Files

- `tests/compact/test_preserve_tree_on_cancel.py`

## Audit Trail

- EXTRACTED: 30 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*