# CLI Framework Architecture

> 10 nodes · cohesion 0.22

## Key Concepts

- **Runner (pexpect spawn)** (8 connections) — `.sisyphus/notepads/implementation/learnings.md`
- **AOMApp TUI Application** (7 connections) — `.sisyphus/notepads/implementation/learnings.md`
- **CLI Main Entry** (3 connections) — `.sisyphus/notepads/implementation/learnings.md`
- **Click CLI Framework** (2 connections) — `.sisyphus/notepads/new-spec/cli-tui-implementation.md`
- **Renderer Protocol** (2 connections) — `.sisyphus/notepads/implementation/learnings.md`
- **Typer CLI Framework** (1 connections) — `.sisyphus/notepads/new-spec/cli-tui-implementation.md`
- **Keybindings Module** (1 connections) — `.sisyphus/notepads/implementation/learnings.md`
- **Preflight --list-tasks/--list-hosts** (1 connections) — `.sisyphus/notepads/implementation/learnings.md`
- **SessionManager** (1 connections) — `.sisyphus/notepads/implementation/learnings.md`
- **Session Recording (.aom/sessions)** (1 connections) — `.sisyphus/notepads/implementation/learnings.md`

## Relationships

- [[TUI Widget Framework]] (2 shared connections)
- [[Rich Display Backend]] (2 shared connections)
- [[Parser Dependencies]] (2 shared connections)
- [[State Machine Architecture]] (1 shared connections)

## Source Files

- `.sisyphus/notepads/implementation/learnings.md`
- `.sisyphus/notepads/new-spec/cli-tui-implementation.md`

## Audit Trail

- EXTRACTED: 22 (81%)
- INFERRED: 5 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*