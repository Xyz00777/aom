# Implementation Learnings

## Redaction Module (src/ansible_aom/core/redaction.py)

### API to implement:
```python
# Constants
PASSWORD_MATCH = re.compile(r'^(?:.+[-_\s])?pass(?:[-_\s]?(?:word|phrase|wrd|wd))?(?:[-_\s].+)?$', re.IGNORECASE)
ANSIBLE_PASSWORD_FIELDS = frozenset({...})
GENERIC_SECRET_FIELDS = frozenset({...})
PASSWORD_WHITELIST = frozenset({"passenger_version", "passenger_pool", "bypass", "overpass", "compass", "underpass", "passport_number"})
URL_CRED_PATTERN = re.compile(r'([a-zA-Z]+://[^:]+:)([^@]+)(@)')
CLI_CRED_PATTERN = re.compile(r'(--(?:password|pass|pwd|token|secret|key|api-key)\s*[=: ]+)\S+', re.IGNORECASE)
REDACTED = '********'
MAX_DEPTH = 10

# Functions
def redact_event(event: dict, config: RedactionConfig) -> dict
def redact_dict(data: dict, config: RedactionConfig, depth: int = 0) -> dict
def sanitize_string(s: str, config: RedactionConfig) -> str
def should_redact(key: str, config: RedactionConfig) -> bool
```

### Layer Rules:
1. **Layer 1**: If `_ansible_no_log=True` is in a result dict (even nested in lists), replace that ENTIRE result with `{'censored': '(no_log)'}`.
2. **Layer 2**: For all result dict keys (except whitelisted), match `PASSWORD_MATCH` regex, `ANSIBLE_PASSWORD_FIELDS`, `GENERIC_SECRET_FIELDS`, or `config.custom_fields` → value replaced with `REDACTED`.
3. **Layer 3**: For specific string fields (`cmd`, `stdout`, `stderr`, `msg`), apply `URL_CRED_PATTERN` and `CLI_CRED_PATTERN` substitutions, plus `config.custom_patterns`.
4. **Layer 4**: If event has `res.invocation.module_args`, recursively redact with same logic (max depth 10).

## CLI Exit Code Tests (test_cli.py TC-027/TC-028)

Current tests are trivial constants. Need to mock actual behavior:
- TC-027: Mock subprocess execution to raise FileNotFoundError, verify `main()` returns 127
- TC-028: Mock signal handling or KeyboardInterrupt during main, verify `main()` returns 130

The `main()` currently handles inspect and playbook. For playbook, it calls `create_renderer()` → `print(...)`. Need to ensure `main()` properly handles `FileNotFoundError` for ansible-playbook → 127.
Since main() currently doesn't spawn ansible-playbook yet (returns 0 after print), the tests should test the DESIRED behavior defined in spec. The current code may need minor modifications to handle `FileNotFoundError` gracefully.

## Missing POSIX Callback Tests (TC-067 to TC-071)

These check:
- ansible.posix availability (via ansible-galaxy collection list or importlib)
- Install prompt
- ansible-core version >= 2.14
- ansible.posix version >= 1.5.0
- ANSIBLE_STDOUT_CALLBACK env var set

## Missing Host Resolution Tests (TC-149 to TC-152)

- resolved_hosts population
- Host cross-check warning
- Fallback after --list-hosts failure
- v2_playbook_on_stats cross-check

## TC-027 & TC-028: CLI Exit Codes for FileNotFoundError and KeyboardInterrupt (2026-04-23)

**Pattern**: Exception handling order matters in Python - specific exceptions must come before generic `Exception` handler.

**Implementation**:
- Added `FileNotFoundError` handler → return 127
- Added `KeyboardInterrupt` handler → return 130  
- Placed **before** the existing `NotImplementedError` and `Exception` handlers

**Test Pattern** for mocking exceptions in CLI:
```python
with patch("ansible_aom.renderer.factory.create_renderer") as mock_renderer:
    mock_renderer.side_effect = FileNotFoundError("ansible-playbook")
    with patch("sys.argv", ["aom", "playbook.yml"]):
        result = main()
        assert result == 127
```

**Key insight**: The `patch` path must match where the function is imported/used, not where it's defined. Since `cli.py` does `from ansible_aom.renderer.factory import create_renderer`, we patch `ansible_aom.renderer.factory.create_renderer`.
