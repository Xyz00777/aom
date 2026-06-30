"""Tests for duplicate-playbook argument detection.

When the user types `aom site.yml -i inv.ini site.yml` (a typo where
the playbook path was repeated), argparse parses playbook=site.yml and
puts the trailing site.yml in ansible_args. ansible-playbook then
fails with an unhelpful argparse error wall. Detect the exact-match
case in AOM and surface a clear error before spawning anything.
"""

from __future__ import annotations

from ansible_aom.cli import detect_duplicate_playbook


def test_detect_duplicate_playbook_finds_exact_repeat():
    assert detect_duplicate_playbook("site.yml", ["-i", "inv.ini", "site.yml"]) is True


def test_detect_duplicate_playbook_returns_false_when_no_repeat():
    assert detect_duplicate_playbook("site.yml", ["-i", "inv.ini"]) is False


def test_detect_duplicate_playbook_distinguishes_different_files():
    """Multiple distinct .yml files are a legitimate ansible-playbook invocation."""
    assert detect_duplicate_playbook("site.yml", ["other.yml"]) is False


def test_detect_duplicate_playbook_handles_empty_args():
    assert detect_duplicate_playbook("site.yml", []) is False


def test_detect_duplicate_playbook_handles_path_normalisation():
    """./site.yml and site.yml refer to the same file — flag the duplicate."""
    assert detect_duplicate_playbook("site.yml", ["./site.yml"]) is True
    assert detect_duplicate_playbook("./site.yml", ["site.yml"]) is True
