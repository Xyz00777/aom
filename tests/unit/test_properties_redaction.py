"""Property-based tests for the redaction layers (Batch C, family #5b).

These properties protect the four redaction layers in :mod:`core.redaction`
against regression by asserting whole-shape invariants rather than
specific examples.

Invariants:

* **P1 / positive coverage.** For any "password-shaped" key, the verbatim
  secret value never appears in the JSON-serialised redacted event.
* **P2 / whitelist immunity.** Keys in :data:`PASSWORD_WHITELIST` retain
  their original values.
* **P3 / string sanitisation.** URL ``scheme://user:secret@host`` and
  ``--password=secret`` CLI shapes are stripped from sanitised strings.
* **P4 / no_log nuke.** ``_ansible_no_log=True`` on a result (top-level
  or nested in a ``results`` list) collapses that dict to
  ``{"censored": "(no_log)"}``, taking any sibling secrets with it.
"""

from __future__ import annotations

import json
import string

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from ansible_aom.core.config import RedactionConfig
from ansible_aom.core.redaction import (
    PASSWORD_MATCH,
    PASSWORD_WHITELIST,
    REDACTED,
    redact_event,
    sanitize_string,
)

# --------------------------------------------------------------------------- #
# Strategies                                                                  #
# --------------------------------------------------------------------------- #

_DEFAULT_CONFIG = RedactionConfig()


def _password_shaped_key() -> st.SearchStrategy[str]:
    """Generate keys that satisfy the PASSWORD_MATCH regex and are not whitelisted."""
    base = st.sampled_from(
        [
            "password",
            "passphrase",
            "db_password",
            "admin-password",
            "mypass",
            "passwd",
            "pass",
        ]
    )
    return base.filter(
        lambda k: (
            PASSWORD_MATCH.match(k.lower()) is not None
            and k.lower() not in {w.lower() for w in PASSWORD_WHITELIST}
        )
    )


def _distinctive_secret() -> st.SearchStrategy[str]:
    """Distinctive non-empty secret values unlikely to collide with other fields."""
    return st.text(
        alphabet=string.ascii_letters + string.digits,
        min_size=16,
        max_size=48,
    ).filter(lambda s: s != REDACTED)


def _innocuous_key() -> st.SearchStrategy[str]:
    """Keys that should never be redacted."""
    return st.sampled_from(["msg", "stdout", "stderr", "value", "name", "host", "item"])


def _whitelisted_key() -> st.SearchStrategy[str]:
    return st.sampled_from(sorted(PASSWORD_WHITELIST))


# --------------------------------------------------------------------------- #
# P1: password-shaped keys always redact, secret never leaks                  #
# --------------------------------------------------------------------------- #


@settings(max_examples=100, deadline=2000, suppress_health_check=[HealthCheck.too_slow])
@given(
    key=_password_shaped_key(),
    secret=_distinctive_secret(),
    extra_key=_innocuous_key(),
    extra_value=st.text(min_size=0, max_size=20),
)
def test_password_shaped_keys_are_redacted(
    key: str, secret: str, extra_key: str, extra_value: str
) -> None:
    """The verbatim secret never appears in the redacted serialisation."""
    # Avoid accidental substring collision between the secret and innocuous fields.
    assume(secret not in extra_value)
    assume(secret not in extra_key)

    event = {"_event": "v2_runner_on_ok", "res": {key: secret, extra_key: extra_value}}
    out = redact_event(event, _DEFAULT_CONFIG)
    blob = json.dumps(out)
    assert secret not in blob, f"Secret leaked through key {key!r}: {blob}"
    # The redaction marker should also appear under the key.
    assert out["res"][key] == REDACTED


# --------------------------------------------------------------------------- #
# P1b: nested dicts also redact                                               #
# --------------------------------------------------------------------------- #


@settings(max_examples=60, deadline=2000, suppress_health_check=[HealthCheck.too_slow])
@given(
    key=_password_shaped_key(),
    secret=_distinctive_secret(),
    depth=st.integers(min_value=1, max_value=5),
)
def test_password_redaction_works_through_nested_dicts(key: str, secret: str, depth: int) -> None:
    """Nested dicts under MAX_DEPTH still redact password-shaped keys."""
    inner: dict = {key: secret}
    for _ in range(depth):
        inner = {"nested": inner}

    event = {"_event": "v2_runner_on_ok", "res": inner}
    out = redact_event(event, _DEFAULT_CONFIG)
    blob = json.dumps(out)
    assert secret not in blob


# --------------------------------------------------------------------------- #
# P2: whitelist keys pass through verbatim                                    #
# --------------------------------------------------------------------------- #


@settings(max_examples=60, deadline=2000, suppress_health_check=[HealthCheck.too_slow])
@given(
    key=_whitelisted_key(),
    value=st.text(min_size=1, max_size=40),
)
def test_whitelisted_keys_pass_through(key: str, value: str) -> None:
    """Keys in PASSWORD_WHITELIST keep their value unchanged."""
    event = {"_event": "v2_runner_on_ok", "res": {key: value}}
    out = redact_event(event, _DEFAULT_CONFIG)
    assert out["res"][key] == value


# --------------------------------------------------------------------------- #
# P3: URL / CLI credential patterns                                           #
# --------------------------------------------------------------------------- #


@settings(max_examples=80, deadline=2000, suppress_health_check=[HealthCheck.too_slow])
@given(
    scheme=st.sampled_from(["http", "https", "postgres", "redis", "mongodb"]),
    user=st.text(alphabet=string.ascii_lowercase + string.digits, min_size=1, max_size=12),
    secret=_distinctive_secret(),
    host=st.text(
        alphabet=string.ascii_lowercase + string.digits + ".",
        min_size=3,
        max_size=20,
    ).filter(lambda s: "." in s and not s.startswith(".") and not s.endswith(".")),
)
def test_url_credentials_are_stripped(scheme: str, user: str, secret: str, host: str) -> None:
    """URL of form scheme://user:SECRET@host/ has SECRET removed by sanitize_string."""
    url = f"{scheme}://{user}:{secret}@{host}/path"
    sanitised = sanitize_string(url, _DEFAULT_CONFIG)
    assert secret not in sanitised
    assert REDACTED in sanitised


@settings(max_examples=80, deadline=2000, suppress_health_check=[HealthCheck.too_slow])
@given(
    flag=st.sampled_from(["--password", "--pass", "--pwd", "--token", "--secret", "--api-key"]),
    sep=st.sampled_from([" ", "=", ": "]),
    secret=_distinctive_secret(),
)
def test_cli_credentials_are_stripped(flag: str, sep: str, secret: str) -> None:
    """CLI flag of form --password=SECRET has SECRET removed by sanitize_string."""
    cmd = f"some-tool {flag}{sep}{secret} --foo bar"
    sanitised = sanitize_string(cmd, _DEFAULT_CONFIG)
    assert secret not in sanitised


# --------------------------------------------------------------------------- #
# P4: _ansible_no_log nukes the result dict                                   #
# --------------------------------------------------------------------------- #


@settings(max_examples=60, deadline=2000, suppress_health_check=[HealthCheck.too_slow])
@given(
    key=_password_shaped_key(),
    secret=_distinctive_secret(),
    extra_text=st.text(min_size=0, max_size=40),
)
def test_no_log_at_top_level_censors_everything(key: str, secret: str, extra_text: str) -> None:
    """_ansible_no_log=True at result top-level: entire res becomes censored marker."""
    assume(secret not in extra_text)
    event = {
        "_event": "v2_runner_on_ok",
        "res": {"_ansible_no_log": True, key: secret, "msg": extra_text},
    }
    out = redact_event(event, _DEFAULT_CONFIG)
    assert out["res"] == {"censored": "(no_log)"}
    assert secret not in json.dumps(out)


@settings(max_examples=60, deadline=2000, suppress_health_check=[HealthCheck.too_slow])
@given(
    key=_password_shaped_key(),
    secret=_distinctive_secret(),
)
def test_no_log_in_loop_items_censors_that_item(key: str, secret: str) -> None:
    """A list ``results`` entry with _ansible_no_log=True collapses to the marker."""
    event = {
        "_event": "v2_runner_on_ok",
        "res": {
            "results": [
                {"item": "ok", "_ansible_no_log": False},
                {"item": "secret", "_ansible_no_log": True, key: secret},
            ]
        },
    }
    out = redact_event(event, _DEFAULT_CONFIG)
    assert out["res"]["results"][1] == {"censored": "(no_log)"}
    assert secret not in json.dumps(out)
