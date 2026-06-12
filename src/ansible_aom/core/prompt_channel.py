"""Pure schema for the per-host interactive-prompt control channel.

The AOM runner and the bundled ``aom.interactive.confirm`` action plugin exchange
JSON request files in a control directory and a one-line answer over a per-request
FIFO. This module is the *AOM side* of that contract (plus the answer-interpretation
helper) and is import-clean for ``core/``. The plugin keeps a stdlib-only mirror of
the same 4-key JSON shape because it can't import this package.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

ENV_VAR = "AOM_PROMPT_CONTROL_DIR"
REQUEST_SUFFIX = ".req"
FIFO_SUFFIX = ".fifo"

# Answers (case-insensitive, stripped) that mean "abort this host".
_ABORT_WORDS: frozenset[str] = frozenset({"n", "no", "abort", "cancel"})


@dataclass(frozen=True)
class PromptRequest:
    """One per-host prompt awaiting an answer."""

    id: str
    host: str
    prompt: str
    created: float = 0.0


def encode_request(req: PromptRequest) -> str:
    """Serialize a request to a single JSON line."""
    return json.dumps(
        {"id": req.id, "host": req.host, "prompt": req.prompt, "created": req.created}
    )


def decode_request(text: str) -> PromptRequest:
    """Parse a request JSON line; ``created`` defaults to 0.0 when absent."""
    data = json.loads(text)
    return PromptRequest(
        id=str(data["id"]),
        host=str(data["host"]),
        prompt=str(data["prompt"]),
        created=float(data.get("created", 0.0)),
    )


def is_abort(answer: str) -> bool:
    """True when the operator's answer means "abort this host"."""
    return answer.strip().lower() in _ABORT_WORDS
