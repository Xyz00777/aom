"""Contract test for the committed ``RunSummary`` v1 JSON schema (Item #7).

Downstream CI consumers (``jq``-driven pipelines, dashboards) pin to
the shape of the JSON object emitted by ``aom --format json``. A silent
field rename today would break them with no warning. This file freezes
the v1 schema at ``schemas/run_summary.v1.json`` and guards it with
three layers:

1. **Byte-for-byte schema parity.** Re-generate ``RunSummary``'s schema
   at test time and compare it to the committed file (pretty-printed
   identically). Any model change fails the test. The author then has
   to decide: revert, or bump ``schema_version`` and add a v2 schema.

2. **Golden payload validation.** Five hand-written ``RunSummary``
   JSON payloads exercise the realistic shape distribution: all-pass,
   mixed-failure, all-unreachable, syntax-error/empty, and a single
   localhost run. Each must validate against the committed schema via
   ``jsonschema.validate`` — proves the schema actually accepts what
   ``JsonRenderer`` emits in practice, not just what Pydantic happens
   to dump.

3. **Schema-version pin.** Both the schema itself (``const: 1``) and
   a live ``RunSummary`` instance must agree on ``schema_version == 1``.

**Update workflow on intentional changes:**

    UPDATE_SCHEMA=1 uv run pytest tests/unit/test_run_summary_schema.py

regenerates ``schemas/run_summary.v1.json`` from the current model.
Use deliberately — bumping the schema is a breaking change for
downstream consumers; prefer a v2 file alongside v1 when possible.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import jsonschema
import pytest

from ansible_aom.formats.json import RunSummary

# Repository root, derived from this file's location. Used to locate
# ``schemas/run_summary.v1.json`` without depending on the test CWD.
REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "run_summary.v1.json"


def _canonical_schema_text() -> str:
    """Pretty-print the current ``RunSummary`` schema for comparison.

    Format pinned to ``indent=2, sort_keys=True`` with a trailing
    newline so the committed file and the regenerated string compare
    byte-for-byte regardless of dict-iteration order.
    """
    schema = RunSummary.model_json_schema()
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


# ---------------------------------------------------------------------------
# Layer 1: schema parity
# ---------------------------------------------------------------------------


class TestSchemaParity:
    """The committed schema must match the model verbatim."""

    def test_committed_schema_matches_current_model(self) -> None:
        """Re-generate and compare. Failure means the model drifted.

        The escape hatch ``UPDATE_SCHEMA=1`` overwrites the committed
        file with the regenerated text. Use only for deliberate schema
        bumps; otherwise this test should fail and prompt either a
        revert or a v2 file.
        """
        if not SCHEMA_PATH.exists():
            pytest.fail(
                f"missing schema file at {SCHEMA_PATH}. "
                "Generate with: UPDATE_SCHEMA=1 pytest tests/unit/test_run_summary_schema.py"
            )

        regenerated = _canonical_schema_text()

        if os.environ.get("UPDATE_SCHEMA"):
            SCHEMA_PATH.write_text(regenerated)
            return

        committed = SCHEMA_PATH.read_text()
        assert regenerated == committed, (
            f"RunSummary model has drifted from {SCHEMA_PATH.relative_to(REPO_ROOT)}.\n"
            "Either revert the model change, or (if intentional) bump "
            "schema_version and add a v2 schema file. To overwrite v1 "
            "deliberately:\n"
            "    UPDATE_SCHEMA=1 uv run pytest tests/unit/test_run_summary_schema.py"
        )


# ---------------------------------------------------------------------------
# Layer 2: golden payloads validate
# ---------------------------------------------------------------------------


def _load_committed_schema() -> dict:
    """Load the on-disk schema. Skipped if missing (handled in Layer 1)."""
    return json.loads(SCHEMA_PATH.read_text())


# Five hand-written golden payloads. These are *the shape downstream
# consumers will see*, not Pydantic-roundtripped output. If any of these
# stops validating, the schema dropped a field or tightened a constraint
# in a way that breaks the wire format.

_GOLDEN_ALL_PASS = {
    "schema_version": 1,
    "playbook": "site.yml",
    "exit_code": 0,
    "started_at": "2026-05-13T10:00:00+00:00",
    "ended_at": "2026-05-13T10:00:05+00:00",
    "duration_s": 5.0,
    "hosts": {
        "web1": {"ok": 3, "changed": 0, "failed": 0, "unreachable": 0},
        "web2": {"ok": 3, "changed": 0, "failed": 0, "unreachable": 0},
    },
    "tasks_failed": [],
}

_GOLDEN_MIXED_FAILURE = {
    "schema_version": 1,
    "playbook": "deploy.yml",
    "exit_code": 1,
    "started_at": "2026-05-13T10:00:00+00:00",
    "ended_at": "2026-05-13T10:00:12+00:00",
    "duration_s": 12.3,
    "hosts": {
        "web1": {"ok": 2, "changed": 1, "failed": 0, "unreachable": 0},
        "web2": {"ok": 1, "changed": 0, "failed": 1, "unreachable": 0},
    },
    "tasks_failed": [
        {"host": "web2", "task": "Install nginx", "msg": "Package not found"},
    ],
}

_GOLDEN_ALL_UNREACHABLE = {
    "schema_version": 1,
    "playbook": "site.yml",
    "exit_code": 4,
    "started_at": "2026-05-13T10:00:00+00:00",
    "ended_at": "2026-05-13T10:00:30+00:00",
    "duration_s": 30.0,
    "hosts": {
        "web1": {"ok": 0, "changed": 0, "failed": 0, "unreachable": 1},
        "web2": {"ok": 0, "changed": 0, "failed": 0, "unreachable": 1},
    },
    "tasks_failed": [
        {"host": "web1", "task": "Gathering Facts", "msg": "ssh: timeout"},
        {"host": "web2", "task": "Gathering Facts", "msg": "ssh: timeout"},
    ],
}

# Syntax error / empty: no events ever fired. hosts {} and
# tasks_failed [] are still valid shapes.
_GOLDEN_SYNTAX_ERROR_EMPTY = {
    "schema_version": 1,
    "playbook": "broken.yml",
    "exit_code": 4,
    "started_at": "2026-05-13T10:00:00+00:00",
    "ended_at": "2026-05-13T10:00:00+00:00",
    "duration_s": 0.0,
    "hosts": {},
    "tasks_failed": [],
}

_GOLDEN_LOCALHOST_ONLY = {
    "schema_version": 1,
    "playbook": "local.yml",
    "exit_code": 0,
    "started_at": "2026-05-13T10:00:00+00:00",
    "ended_at": "2026-05-13T10:00:01+00:00",
    "duration_s": 1.4,
    "hosts": {
        "localhost": {"ok": 1, "changed": 1, "failed": 0, "unreachable": 0},
    },
    "tasks_failed": [],
}


@pytest.mark.parametrize(
    ("name", "payload"),
    [
        ("all-pass", _GOLDEN_ALL_PASS),
        ("mixed-failure", _GOLDEN_MIXED_FAILURE),
        ("all-unreachable", _GOLDEN_ALL_UNREACHABLE),
        ("syntax-error-empty", _GOLDEN_SYNTAX_ERROR_EMPTY),
        ("localhost-only", _GOLDEN_LOCALHOST_ONLY),
    ],
)
def test_golden_payload_validates_against_committed_schema(name: str, payload: dict) -> None:
    """Each canonical shape must validate. Catches accidental tightening."""
    schema = _load_committed_schema()
    # ``validate`` raises ``ValidationError`` on failure — let it bubble.
    jsonschema.validate(payload, schema)


def test_pydantic_roundtrip_also_validates() -> None:
    """Bonus: a payload produced through the Pydantic model must validate.

    Prevents the case where ``model_dump_json()`` and the JSON schema
    disagree about a field's serialised type (e.g. ``Literal[1]``
    serialising as a string).
    """
    summary = RunSummary(
        schema_version=1,
        playbook="site.yml",
        exit_code=0,
        started_at="2026-05-13T10:00:00+00:00",
        ended_at="2026-05-13T10:00:01+00:00",
        duration_s=1.0,
        hosts={},
        tasks_failed=[],
    )
    payload = json.loads(summary.model_dump_json())
    jsonschema.validate(payload, _load_committed_schema())


# ---------------------------------------------------------------------------
# Layer 3: schema_version pin
# ---------------------------------------------------------------------------


class TestSchemaVersionPin:
    """``schema_version`` is the only stable contract callers can pin to."""

    def test_committed_schema_pins_schema_version_to_one(self) -> None:
        """JSON Schema's ``const`` keyword fixes the value to literally 1."""
        schema = _load_committed_schema()
        props = schema["properties"]
        assert props["schema_version"].get("const") == 1, (
            "schema_version must be locked to const:1 in the committed schema; "
            f"got {props['schema_version']}."
        )
        assert "schema_version" in schema["required"]

    def test_live_model_instance_has_schema_version_one(self) -> None:
        """The model itself emits 1, matching what the schema requires."""
        summary = RunSummary(
            schema_version=1,
            playbook="x",
            exit_code=0,
            started_at="2026-05-13T10:00:00+00:00",
            ended_at="2026-05-13T10:00:00+00:00",
            duration_s=0.0,
            hosts={},
            tasks_failed=[],
        )
        assert summary.schema_version == 1

    def test_construction_with_wrong_version_rejected(self) -> None:
        """``Literal[1]`` rejects any other integer at construction time."""
        import pydantic

        with pytest.raises(pydantic.ValidationError):
            RunSummary(
                schema_version=2,  # not allowed by Literal[1]
                playbook="x",
                exit_code=0,
                started_at="2026-05-13T10:00:00+00:00",
                ended_at="2026-05-13T10:00:00+00:00",
                duration_s=0.0,
                hosts={},
                tasks_failed=[],
            )
