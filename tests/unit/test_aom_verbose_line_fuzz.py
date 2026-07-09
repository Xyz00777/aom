"""Deterministic fuzz test for the v1 stderr classifier.

Exercises ``classify()`` with 10k stderr-like lines — a mix of known
non-verbose patterns (``ERROR!``, ``Traceback``, ``FATAL``, etc.) and
randomly generated noise — and asserts that none of them produce a
false positive (i.e. every line returns ``UNKNOWN`` with ``host=None``).

This complements the hand-picked weird-input tests in
``TestNoExceptions`` by adding volume and coverage of realistic
non-verbose stderr prefixes that ansible-playbook might emit but that
the classifier should *not* match.
"""

from __future__ import annotations

import random

from ansible_aom.core.stderr_classifier import StderrSource, classify

_RNG = random.Random(42)

_NON_VERBOSE_TEMPLATES: list[str] = [
    "ERROR! {}",
    "ERROR!",
    "Traceback (most recent call last):",
    '  File "{}", line {}, in {}',
    "{}Error: {}",
    "{}Exception: {}",
    "{}KeyError: {}",
    "{}ValueError: {}",
    "{}TypeError: {}",
    "{}AttributeError: {}",
    "{}ImportError: {}",
    "{}ModuleNotFoundError: {}",
    "{}OSError: {}",
    "{}PermissionError: {}",
    "{}FileNotFoundError: {}",
    "FATAL: {}",
    "fatal: {}",
    "FATAL {}",
    "debug1: {}",
    "debug2: {}",
    "debug3: {}",
    "Warning: Permanently added '{}' (ED25519) to the list of known hosts.",
    "Warning: {}",
    "Connection closed by {} port {}",
    "Connection reset by {}",
    "kex_exchange_identification: {}",
    "ssh_exchange_identification: {}",
    "+ {}",
    "make: *** [{}] Error {}",
    "npm ERR! {}",
    "pip: {}",
    "warning: {}",
    "{}: command not found",
    "{}: No such file or directory",
    "{}: Permission denied",
    "{}: not found",
    "cannot {}: {}",
    "usage: {} [-{}] {}",
    "Try '{} --help' for more information.",
    "localhost | SUCCESS => {}",
    "{} | UNREACHABLE! => {}",
    "{}",
    "  {}",
    "\t{}",
    "{} {} {}",
    "{}={}",
    "{}: {}: {}",
]

_WORDS = [
    "localhost",
    "web1",
    "db01",
    "ansible",
    "python3",
    "ssh",
    "config",
    "inventory",
    "playbook",
    "site.yml",
    "hosts",
    "port",
    "22",
    "file",
    "path",
    "error",
    "warning",
    "info",
    "debug",
    "trace",
    "fail",
    "connection",
    "timeout",
    "refused",
    "reset",
    "broken",
    "pipe",
    "permission",
    "denied",
    "not",
    "found",
    "no",
    "such",
    "unknown",
    "invalid",
    "argument",
    "option",
    "flag",
    "value",
    "key",
    "var",
    "module",
    "task",
    "role",
    "play",
    "run",
    "session",
    "record",
    "status",
    "code",
    "exit",
    "signal",
    "term",
    "kill",
    "stop",
    "start",
    "init",
    "load",
    "unload",
    "reload",
    "restart",
]


def _random_word() -> str:
    return _RNG.choice(_WORDS)


def _random_text(min_words: int = 1, max_words: int = 8) -> str:
    count = _RNG.randint(min_words, max_words)
    return " ".join(_RNG.choice(_WORDS) for _ in range(count))


def _generate_line(template: str) -> str:
    result = template
    while "{}" in result:
        result = result.replace("{}", _random_text(1, 3), 1)
    return result


def _build_corpus(size: int = 10_000) -> list[str]:
    _RNG.seed(42)
    lines: list[str] = []
    templates = _NON_VERBOSE_TEMPLATES
    for tpl in templates:
        lines.append(_generate_line(tpl))
    while len(lines) < size:
        tpl = _RNG.choice(templates)
        lines.append(_generate_line(tpl))
    _RNG.shuffle(lines)
    return lines


class TestFuzzNoFalsePositives:
    """10k stderr-like lines must not produce false positives."""

    CORPUS = _build_corpus(10_000)

    def test_all_lines_are_unknown(self) -> None:
        failures: list[tuple[str, str]] = []
        for line in self.CORPUS:
            event = classify(line)
            if event.source is not StderrSource.UNKNOWN:
                failures.append((line, event.source.value))
        assert not failures, (
            f"{len(failures)} / {len(self.CORPUS)} lines produced a false positive:\n"
            + "\n".join(f"  {src!r}: {line!r}" for line, src in failures[:20])
        )

    def test_all_lines_have_no_host(self) -> None:
        failures: list[tuple[str, str | None]] = []
        for line in self.CORPUS:
            event = classify(line)
            if event.host is not None:
                failures.append((line, event.host))
        assert not failures, (
            f"{len(failures)} / {len(self.CORPUS)} lines unexpectedly had a host:\n"
            + "\n".join(f"  host={host!r}: {line!r}" for line, host in failures[:20])
        )

    def test_corpus_size_is_exactly_10k(self) -> None:
        assert len(self.CORPUS) == 10_000

    def test_corpus_is_deterministic(self) -> None:
        corpus_b = _build_corpus(10_000)
        assert self.CORPUS == corpus_b, "Corpus is not deterministic — check RNG seed"

    def test_never_raises(self) -> None:
        for line in self.CORPUS:
            try:
                classify(line)
            except Exception as exc:  # pragma: no cover
                raise AssertionError(f"classify({line!r}) raised {exc!r}") from exc
