# Build Rerun Command

> 15 nodes · cohesion 0.13

## Key Concepts

- **Critical gotchas (confirmed in practice)** (7 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **Decisions** (5 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **v1 Verbosity — Learnings (Phase 3: config_layer)** (5 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **1. `deep_merge=True` is REQUIRED on multi-file `YamlConfigSettingsSource`** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **2. `nested_model_default_partial_update=True` is REQUIRED for partial overrides** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **3. `_yaml_file` is a non-model kwarg — must be read from `init_settings.init_kwargs`** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **4. Module-level path constants defeat monkeypatching** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **5. `AOM_*` env var with nested delimiter is `__` not `.`** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **6. The 2.x `migrate_legacy_config` is a verbatim copy, not a schema translate** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **D1: Ship default_config.yaml inside the wheel (lowest layer)** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **D2: `_yaml_file` is the test escape hatch, not a public API** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **D3: `extra="ignore"` on AomSettings** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **D4: Migration is auto, silent, and never re-runs** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **Verification log** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`
- **What was built** (1 connections) — `.sisyphus/notepads/v1-verbosity/learnings.md`

## Relationships

- [Runtime Event Handlers](Runtime_Event_Handlers.md) (1 shared connections)

## Source Files

- `.sisyphus/notepads/v1-verbosity/learnings.md`

## Audit Trail

- EXTRACTED: 29 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*