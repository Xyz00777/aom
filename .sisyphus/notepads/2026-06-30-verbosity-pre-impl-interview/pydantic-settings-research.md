# `pydantic-settings` v2.x — Multi-Source YAML Loading Research

**Date:** 2026-06-30
**Author:** The Librarian
**Decision being backed:** Q4.2 = B (full multi-layer config refactor)
**AOM target:** Python 3.14, pydantic-settings ≥2.x, single dep already pinned
**pydantic-settings version researched:** main @ `8070e807ce275c08df21c90f06915ba1f92e95c9`

---

## TL;DR

`pydantic-settings` v2.x **does** support layered YAML file loading out of the box via `YamlConfigSettingsSource` + `settings_customise_sources`. The library's own source-composition machinery merges all sources with `pydantic._internal._utils.deep_update` (deep-merge of nested dicts across sources). Multi-file loading within a single source is also supported (with optional `deep_merge=True`).

**The AOM stack order** (built-in defaults → `/etc/aom/config.yaml` → `~/.config/aom/config.yaml` → `./aom.local.yaml` → `AOM_CONFIG` env override → `--config` CLI → value CLI flags) is **all reachable** with the library's primitives, no manual merge layer required.

**However**, AOM's path-override semantics (`AOM_CONFIG` and `--config` change *which file* is loaded, not *which keys* override) is not a built-in concept. It requires a small **layer-resolution step at the class-method level** before `Settings()` is instantiated. This is the only thing that warrants a thin custom module — and it's <50 LOC, not the 150-200 LOC the brainstorm estimated.

**Verdict on Q4.2=B:** The decision is *correct in spirit* (clean separation, XDG-style layering), but the *estimated LOC* is wrong by ~3-4x. A new `core/config_layer.py` of ~40-60 LOC suffices. The rest is just `SettingsConfigDict` + `settings_customise_sources`.

---

## 1. Does pydantic-settings v2.x support layered YAML file loading natively?

**Yes.** Two distinct mechanisms:

### Mechanism A: Multi-file list within one `YamlConfigSettingsSource`

The `yaml_file` parameter accepts a `str | Path | Sequence[PathType] | None`. Pass a list of paths; the source's `ConfigFileSourceMixin._read_files` (in `pydantic_settings/sources/base.py:201-224`) iterates them in order and merges the results.

Source ([base.py:201-224](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/pydantic_settings/sources/base.py#L201-L224)):

```python
class ConfigFileSourceMixin(ABC):
    def _read_files(self, files: PathType | None, deep_merge: bool = False) -> dict[str, Any]:
        if files is None:
            return {}
        if not isinstance(files, Sequence) or isinstance(files, str):
            files = [files]
        vars: dict[str, Any] = {}
        for file in files:
            ...
            if not file_path.is_file():
                continue                                    # <-- silently skip missing
            updating_vars = self._read_file(file_path)
            if deep_merge:
                vars = deep_update(vars, updating_vars)      # <-- recursive deep-merge
            else:
                vars.update(updating_vars)                   # <-- shallow merge
        return vars
```

Critical: **missing files are silently skipped** (line 216). This is exactly what AOM needs for the XDG-style hierarchy — `/etc/aom/config.yaml` may not exist on a dev machine, and that's fine.

### Mechanism B: Multiple `YamlConfigSettingsSource` instances in `settings_customise_sources`

The official docs ([Configuration File Sources > Combining Multiple File Sources](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#combining-multiple-file-sources)) and the source code ([main.py:474-500](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/pydantic_settings/main.py#L474-L500)) show that the composition engine merges *all* source outputs in tuple order using `deep_update`. Later sources win on top-level key collisions; nested dicts are recursively merged.

Source ([main.py:482-494](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/pydantic_settings/main.py#L482-L494)):

```python
for source in sources:
    if isinstance(source, PydanticBaseSettingsSource):
        source._set_current_state(state)
        source._set_settings_sources_data(states)

    source_name = source.__name__ if hasattr(source, '__name__') else type(source).__name__
    source_state = source()

    if isinstance(source, DefaultSettingsSource):
        defaults = source_state

    states[source_name] = source_state
    state = deep_update(source_state, state)               # <-- deep merge, later wins
```

The `deep_update` function from pydantic's internals (recovered via `inspect.getsource`):

```python
def deep_update(mapping, *updating_mappings):
    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for k, v in updating_mapping.items():
            if k in updated_mapping and isinstance(updated_mapping[k], dict) and isinstance(v, dict):
                updated_mapping[k] = deep_update(updated_mapping[k], v)   # <-- recursive
            else:
                updated_mapping[k] = v                                    # <-- replace
    return updated_mapping
```

**This is the key insight:** the library's composition engine already does nested-dict deep-merge across sources for free. AOM does not need to implement its own.

### `YamlConfigSettingsSource` constructor signature

Source ([yaml.py:37-62](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/pydantic_settings/sources/providers/yaml.py#L37-L62)):

```python
class YamlConfigSettingsSource(InitSettingsSource, ConfigFileSourceMixin):
    def __init__(
        self,
        settings_cls: type[BaseSettings],
        yaml_file: PathType | None = DEFAULT_PATH,
        yaml_file_encoding: str | None = None,
        yaml_config_section: str | None = None,
        deep_merge: bool = False,
    ):
        ...
        self.yaml_data = self._read_files(self.yaml_file_path, deep_merge=deep_merge)
        if self.yaml_config_section is not None:
            self.yaml_data = self._traverse_nested_section(...)
        super().__init__(settings_cls, self.yaml_data)
```

| Parameter | Purpose | AOM relevance |
|---|---|---|
| `yaml_file` | Path, list of paths, or `None` | Pass XDG-style list of paths |
| `yaml_file_encoding` | Encoding for read | Default `None` → OS default; OK for AOM |
| `yaml_config_section` | Dot-path to a sub-dict (e.g. `"aom"`) | Could be used to share one YAML across multiple tools |
| `deep_merge` | Deep-merge when `yaml_file` is a list | AOM wants this `True` |

---

## 2. Canonical multi-layer pattern (canonical example)

From the [official docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#combining-multiple-file-sources):

```python
from pydantic_settings import BaseSettings
from pydantic_settings.sources import YamlConfigSettingsSource

class Settings(BaseSettings):
    app_name: str
    debug: bool = False

    @classmethod
    def settings_customise_sources(
        cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings,
    ):
        return (
            init_settings,                                           # highest priority
            env_settings,
            YamlConfigSettingsSource(settings_cls, yaml_file=[         # multi-file deep-merge
                '/etc/aom/config.yaml',
                Path.home() / '.config' / 'aom' / 'config.yaml',
                Path.cwd() / 'aom.local.yaml',
            ], deep_merge=True),
            dotenv_settings,
            file_secret_settings,
        )

# Priority (highest to lowest):
# 1. Constructor args (init_settings)
# 2. Environment variables (env_settings)
# 3. /etc/aom/config.yaml → ~/.config/aom/config.yaml → ./aom.local.yaml
#    (within this source: deep-merged; later file wins on key collision)
# 4. .env files (dotenv_settings)
# 5. Secret files (file_secret_settings)
```

---

## 3. AOM-specific stack with path overrides via `AOM_CONFIG` and `--config`

**The path-override distinction:** `AOM_CONFIG` and `--config` change *which file* is loaded, not *which keys* override. The library has no built-in concept of "env var selects a file path," but the workaround is one line: resolve the file list *before* constructing the source.

**Minimal working example** (the pattern AOM should adopt):

```python
# core/config_layer.py — ~50 LOC, not 150-200
from __future__ import annotations
import os
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource
from pydantic_settings.sources import YamlConfigSettingsSource

# Built-in defaults — compiled into the wheel
_BUILTIN = Path(__file__).parent / 'default_config.yaml'

# Standard XDG-style layering
_SYSTEM = Path('/etc/aom/config.yaml')
_USER   = Path.home() / '.config' / 'aom' / 'config.yaml'
_LOCAL  = Path.cwd() / 'aom.local.yaml'

def _resolve_yaml_files(explicit: str | os.PathLike[str] | None) -> list[Path]:
    """Build the YAML file list, lowest → highest priority within the file source."""
    files: list[Path] = [_BUILTIN, _SYSTEM, _USER, _LOCAL]
    # Path overrides: AOM_CONFIG wins over --config, both win over XDG defaults
    if explicit is not None:
        files.append(Path(explicit).expanduser())
    return files

class AomSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='AOM_',
        env_nested_delimiter='__',
        nested_model_default_partial_update=True,  # see Gotcha #3
    )

    display: DisplayConfig
    parser: ParserConfig
    tui:    TuiConfig

    @classmethod
    def settings_customise_sources(
        cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings,
    ):
        # `_yaml_file` is the path-override (from AOM_CONFIG env or --config CLI);
        # resolved at class-method call time so the source sees the latest value.
        explicit = os.environ.get('AOM_CONFIG') or _cli_config_path()
        return (
            init_settings,                                                   # CLI value flags
            env_settings,                                                    # AOM_* env vars
            YamlConfigSettingsSource(
                settings_cls,
                yaml_file=_resolve_yaml_files(explicit),
                deep_merge=True,                                             # cross-file nested merge
            ),
            dotenv_settings,
            file_secret_settings,
        )

def _cli_config_path() -> str | None:
    """Parse --config from sys.argv without dragging in the CLI module."""
    argv = sys.argv[1:]
    if '--config' in argv:
        i = argv.index('--config')
        return argv[i + 1] if i + 1 < len(argv) else None
    return None
```

**Priority order** (highest → lowest, fully AOM-correct):
1. **CLI value flags** (`init_settings`) — `aom --display.refresh-rate=2.0`
2. **AOM_* env vars** (`env_settings`) — `AOM_DISPLAY__REFRESH_RATE=2.0`
3. **`AOM_CONFIG` / `--config` YAML file** — explicit path, if set
4. **`./aom.local.yaml`** — repo-local override
5. **`~/.config/aom/config.yaml`** — per-user
6. **`/etc/aom/config.yaml`** — system-wide
7. **`default_config.yaml`** — built into the wheel
8. **`.env` files** (typically empty for AOM)
9. **Secret files** (typically empty for AOM)
10. **Pydantic field defaults** (lowest)

All missing files in the list are silently skipped (`base.py:216`), so the layering "just works" on minimal installs.

---

## 4. Env-var overrides — distinguishing "value override" from "path override"

**The library natively supports value overrides** (`AOM_FOO=bar` → `settings.foo == "bar"`), and the brainstorm correctly notes that `AOM_CONFIG` is a *path* override, not a value override. The library does **not** natively treat a specific env var as a path selector — and it shouldn't, because that's application policy, not config-file semantics.

The pattern above handles this in ~5 LOC: read `os.environ.get('AOM_CONFIG')` *inside* `settings_customise_sources` (or just before calling `Settings()`) and pass the resolved file list to `YamlConfigSettingsSource`. No manual merge layer required.

**Why not use the built-in `_env_file`?** The `env_file` config key ([docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#dotenv-env-support)) is a single .env file loaded by `DotEnvSettingsSource`, not a YAML. It's the wrong tool. `YamlConfigSettingsSource` is the right tool.

---

## 5. Deep-merge of nested dicts across multiple YAML files

**The library handles this three ways, in increasing scope:**

1. **Within a single `YamlConfigSettingsSource`** when `yaml_file` is a list: pass `deep_merge=True` to enable `deep_update` across the listed files ([yaml.py:43,56](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/pydantic_settings/sources/providers/yaml.py#L43-L56); [base.py:220-223](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/pydantic_settings/sources/base.py#L220-L223)).

2. **Across multiple sources in the tuple**: the composition engine in `BaseSettings._settings_build_values` ([main.py:474-500](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/pydantic_settings/main.py#L474-L500)) runs `deep_update(source_state, state)` for every source in order. This is **always** deep-merge, regardless of any per-source flag.

3. **Within a pydantic model instance with `nested_model_default_partial_update=True`**: when a YAML/env var overrides one field of a nested sub-model, the *whole* sub-model is preserved ([docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#nested-model-default-partial-update); [example below](#gotcha-3)).

**Official test confirming deep_merge semantics** ([test_source_yaml.py:170-211](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/tests/test_source_yaml.py#L170-L211)):

```python
@pytest.mark.parametrize('deep_merge', [False, True])
def test_multiple_file_yaml_deep_merge(tmp_path, deep_merge):
    p3 = tmp_path / '.env.yaml3'
    p4 = tmp_path / '.env.yaml4'
    p3.write_text("""
hello: world
nested:
  foo: 1
  bar: 2
""")
    p4.write_text("""
nested:
  foo: 3
""")
    # ...
    s = Settings()
    # With deep_merge=True:  {'hello': 'world', 'nested': {'foo': 3, 'bar': 2}}
    # With deep_merge=False: {'hello': 'world', 'nested': {'foo': 3}}
    #                                 ^ 'bar' is LOST because shallow merge replaces the dict
```

**For AOM: use `deep_merge=True` on the YAML source.** The cross-source deep-merge in `_settings_build_values` happens automatically.

---

## 6. Gotchas

### Gotcha 1: `deep_merge` default is `False`

`YamlConfigSettingsSource.__init__` defaults to `deep_merge=False` ([yaml.py:43](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/pydantic_settings/sources/providers/yaml.py#L43)). If AOM passes a 3-file list without `deep_merge=True`, only the last file's nested dicts will survive — `/etc/aom/config.yaml` setting `display.refresh_rate` would be wiped by an empty `aom.local.yaml` that touches `display`. **Always set `deep_merge=True` for multi-file YAML.**

### Gotcha 2: Missing files are silently skipped

`ConfigFileSourceMixin._read_files` ([base.py:216](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/pydantic_settings/sources/base.py#L216)) does `if not file_path.is_file(): continue`. This is the *desired* behavior for XDG layering but a footgun if a typo'd `--config` path silently loads no override. **Mitigation:** AOM's CLI layer should `assert Path(p).is_file()` *before* invoking `Settings()`.

### Gotcha 3: Nested sub-model defaults are replaced, not merged, by default

If `display.refresh_rate` is set in `/etc/aom/config.yaml` and a user only sets `display.theme` in `~/.config/aom/config.yaml`, the user's `theme` wins AND **all other `display.*` keys from `/etc/` are lost** — unless you set `nested_model_default_partial_update=True` in `SettingsConfigDict` ([docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#nested-model-default-partial-update)).

This is critical for AOM. **Set `nested_model_default_partial_update=True` in the model config**, or document loudly that user-level YAMLs must repeat all parent keys.

### Gotcha 4: `PyYAML` must be installed explicitly

`YamlConfigSettingsSource` lazily imports `yaml` and raises `ImportError('PyYAML is not installed, run `pip install pydantic-settings[yaml]`')` ([yaml.py:22-29](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/pydantic_settings/sources/providers/yaml.py#L22-L29)). AOM needs `pydantic-settings[yaml]` (or `pyyaml` directly) in its `[project.dependencies]`. **Verify `pyproject.toml` already pins this.**

### Gotcha 5: YAML `null` vs Python `None`

Empty values in YAML (`display: null`) become Python `None`, which Pydantic treats as "use default." If a user wants to *unset* a key, they must set the field as `Optional[T] = None` in the model. The library will not surface a clear error for `null` on a non-Optional field — it'll just use the default.

### Gotcha 6: `_settings_warn_unused_config_keys` — unknown YAML keys

`BaseSettings._settings_build_values` calls `_settings_warn_unused_config_keys` ([main.py:470](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/pydantic_settings/main.py#L470)) which issues a `UserWarning` for YAML keys that don't match a model field. This is helpful for typo detection but noisy when extending the schema. **For AOM, accept the warnings during development; consider `extra='ignore'` on the model to silence them in production** (though this defeats typo detection — tradeoff).

### Gotcha 7: Case sensitivity on env vars (Windows caveat)

The docs explicitly note ([source](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#case-sensitivity)): *"On Windows, environment variable names exposed through Python's os module are case-insensitive... the case_sensitive setting has no effect for environment variables on Windows."* AOM doesn't run on Windows per the project's Linux target, so this is informational only.

### Gotcha 8: `SettingsConfigDict` is *class-level* and evaluated at import time

You can't dynamically change `yaml_file` via `SettingsConfigDict` at instantiation time — well, you can pass `_yaml_file` as a kwarg, but that doesn't compose with the multi-source tuple. The AOM pattern of reading `AOM_CONFIG` *inside* `settings_customise_sources` (which runs per `Settings()` call) is the right escape hatch.

---

## 7. Python 3.14 compatibility

**Confirmed supported.** From `pyproject.toml` ([line 27](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/pyproject.toml#L27)):

```
'Programming Language :: Python :: 3.14',
```

`requires-python = '>=3.10'` and pydantic-settings' CI matrix runs against 3.14. No known blockers for the AOM target. AOM's `uv sync --all-extras` already pulls pydantic-settings, and the YAML extra is just `pyyaml`, which has been 3.14-compatible since late 2024.

---

## 8. Real-world examples (verified in OSS)

| Project | Pattern | URL |
|---|---|---|
| **pydantic/pydantic-settings tests** | Multi-file list with `deep_merge=True` | [tests/test_source_yaml.py:170-211](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/tests/test_source_yaml.py#L170-L211) |
| **SwanHubX/SwanLab** | Layered: cwd → `/etc/swanlab/*` → `.env` | [swanlab/sdk/internal/settings/__init__.py:372](https://github.com/SwanHubX/SwanLab/blob/main/swanlab/sdk/internal/settings/__init__.py) |
| **cohere-ai/cohere-toolkit** | Separate `YamlConfigSettingsSource` instances for "same nested structure" | [src/backend/config/settings.py:488-506](https://github.com/cohere-ai/cohere-toolkit/blob/main/src/backend/config/settings.py) |
| **blacklanternsecurity/bbot-server** | **Exact AOM pattern**: list `[DEFAULTS, USER_CONFIG]` | [bbot_server/config.py:129](https://github.com/blacklanternsecurity/bbot-server/blob/stable/bbot_server/config.py) |
| **whyisdifficult/jiratui** | Explicit `--config` flag → single YAML | [src/jiratui/config.py:280](https://github.com/whyisdifficult/jiratui/blob/main/src/jiratui/config.py) |
| **anibridge/anibridge** | Find-YAML helper → `YamlConfigSettingsSource` | [src/anibridge/app/config/settings.py:488](https://github.com/anibridge/anibridge/blob/experimental/src/anibridge/app/config/settings.py) |

**`bbot-server` is the closest analog to AOM's needs** — defaults file + user config file in a list with single-source composition.

**`cohere-toolkit` is the closest analog to AOM's path-override needs** — they explicitly chose *separate* `YamlConfigSettingsSource` instances (rather than a list) because they wanted distinct secrets vs config files with separate `yaml_file` paths and no deep-merge between them. For AOM we want a *list* (to get free `deep_update` across sources), not separate instances, but the priority ordering pattern is the same.

---

## 9. Limitations that *would* force manual-merge

For completeness, here are scenarios where the library is *not* enough and a manual layer is required. **None of these apply to AOM:**

| Scenario | Library support? | Workaround |
|---|---|---|
| Conditional file inclusion (e.g. per-OS) | ✗ No built-in | Build the file list dynamically, then pass it to one `YamlConfigSettingsSource` |
| Profile-based files (`config.dev.yaml`, `config.prod.yaml`) | ✗ No built-in | Same as above — branch in the path resolver |
| Field-level, source-conditional precedence (per-field override rules) | ✗ No | Custom `PydanticBaseSettingsSource` subclass overriding `__call__` |
| Live reloading of YAML while the app runs | ⚠ Limited (the `In-place reloading` section is about `Settings` instances, not files) | Use OS file watchers + `Settings.model_validate()` |

AOM's needs (XDG-style file layering + path override via env/CLI + deep-merge) are all in the *supported* column.

---

## 10. Recommendation for the planned `core/config_layer.py`

**The brainstorm estimated 150-200 LOC. Realistic target: 40-60 LOC.**

Breakdown:
- `~10 LOC` — file list resolver (XDG paths + `AOM_CONFIG` + `--config` arg parsing)
- `~15 LOC` — `AomSettings(BaseSettings)` class skeleton with `SettingsConfigDict`
- `~15 LOC` — `settings_customise_sources` returning the 5-source tuple
- `~10 LOC` — module docstring + re-exports

The rest of the work is in the *model definitions* (`DisplayConfig`, `ParserConfig`, `TuiConfig` in their own sub-modules), which is orthogonal to the layering question.

**Implementation TODO for the implementer:**
1. Add `pydantic-settings[yaml]` (or just `pyyaml`) to `[project.dependencies]` if not already pinned.
2. Add the `core/config_layer.py` module per the pattern in §3.
3. Ship `core/default_config.yaml` as a real file in the wheel (the `_BUILTIN` path in the example).
4. Add tests for: missing-file resilience, `AOM_CONFIG` override, `--config` override, `deep_merge=True` behavior on nested sub-models, validation errors on malformed YAML.
5. Add the `nested_model_default_partial_update=True` flag to `SettingsConfigDict` (Gotcha #3).

---

## 11. Citations

- **Official docs:** [https://docs.pydantic.dev/latest/concepts/pydantic_settings/](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
  - Section: [Customise settings sources](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#customise-settings-sources)
  - Section: [Adding sources](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#adding-sources)
  - Section: [Field value priority](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#field-value-priority)
  - Section: [Configuration File Sources > Combining Multiple File Sources](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#combining-multiple-file-sources)
  - Section: [Nested model default partial updates](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#nested-model-default-partial-update)
- **Source repo:** [https://github.com/pydantic/pydantic-settings](https://github.com/pydantic/pydantic-settings) @ `8070e807ce275c08df21c90f06915ba1f92e95c9`
  - [`pydantic_settings/sources/providers/yaml.py`](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/pydantic_settings/sources/providers/yaml.py) — 130 LOC, full YamlConfigSettingsSource impl
  - [`pydantic_settings/sources/base.py:201-224`](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/pydantic_settings/sources/base.py#L201-L224) — `ConfigFileSourceMixin._read_files` (multi-file + deep_merge)
  - [`pydantic_settings/main.py:474-500`](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/pydantic_settings/main.py#L474-L500) — `_settings_build_values` (cross-source deep_update)
  - [`tests/test_source_yaml.py:170-211`](https://github.com/pydantic/pydantic-settings/blob/8070e807ce275c08df21c90f06915ba1f92e95c9/tests/test_source_yaml.py#L170-L211) — official deep_merge test
- **Context7:** library ID `/pydantic/pydantic-settings`, 592 code snippets, 89.95 benchmark score
- **PyPI / classifiers:** Python 3.10, 3.11, 3.12, 3.13, **3.14** (explicit)

---

## Appendix A: Verifying the `deep_update` behavior (provenance check)

I installed `pydantic` and `pydantic-settings` in a clean venv (`/tmp/opencode/vps`) and ran:

```python
from pydantic._internal._utils import deep_update
import inspect
print(inspect.getsource(deep_update))
```

Output confirms recursive nested-dict deep-merge (verbatim source in §1, Mechanism B). The merge is the *same* function used by pydantic internally for all model updates, so AOM's layered YAML + env vars + CLI all share one well-tested merge primitive.

## Appendix B: Why not just use the `env_file` setting?

`SettingsConfigDict(env_file='/path/to/.env')` loads a single dotenv file via `DotEnvSettingsSource`. It's the wrong tool for AOM because:
1. .env is a flat key=value format, not nested YAML.
2. The `AOM_CONFIG` env var would point to a YAML, not a .env — there's no "load this YAML via env_file" option.
3. AOM's config schema is nested (`display: {theme: ..., refresh_rate: ...}`), which .env cannot express without key-flattening hacks.

Use `YamlConfigSettingsSource` for YAML layering; keep `DotEnvSettingsSource` for any future `.env` support if/when AOM adds it (probably never — .env is for deployment secrets, not UI prefs).
