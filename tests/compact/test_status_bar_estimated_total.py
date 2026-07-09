"""The status-bar task denominator can be an estimate (prior-run seeded).

When the total comes from a *loose* prior-run match rather than a
preflight-certain / strict count, the bar marks it with a leading ``~``
(``40/~110 tasks``) so the number reads as projected, not known.
"""

from __future__ import annotations

from ansible_aom.compact.format import format_status_bar


def _bar(**kw) -> str:
    base = dict(
        playbook="site.yml",
        hosts_completed=1,
        hosts_total=1,
        warnings=0,
        deprecations=0,
        elapsed_seconds=10,
        tasks_completed=40,
        tasks_total=110,
    )
    base.update(kw)
    return format_status_bar(**base)


def test_estimated_total_prefixes_tilde() -> None:
    assert "40/~110 tasks" in _bar(estimated_total=True)


def test_non_estimated_total_is_plain() -> None:
    assert "40/110 tasks" in _bar(estimated_total=False)
    assert "~" not in _bar(estimated_total=False)


def test_estimated_default_is_plain() -> None:
    assert "40/110 tasks" in _bar()
