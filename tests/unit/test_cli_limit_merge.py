"""Tests for merging repeated ``-l`` / ``--limit`` flags.

ansible-playbook stores ``--limit`` as a single string in its own
argparse setup, so passing ``-l host1 -l host2`` silently drops the
first one — only ``host2`` runs. This is a recurring footgun. AOM
detects multiple limit flags in the forwarded args and merges them
into a single comma-joined value (the syntax ansible actually honours
as a union).

The merge is positional-stable: the merged flag lives where the FIRST
limit flag appeared, so the user's overall arg ordering is preserved.
The flag form (``-l`` vs ``--limit``) is taken from the first
occurrence too.
"""

from __future__ import annotations

from ansible_aom.cli import merge_limit_args


class TestMergeLimitArgs:
    def test_no_limit_args_unchanged(self):
        assert merge_limit_args(["--tags", "base"]) == ["--tags", "base"]

    def test_single_short_limit_unchanged(self):
        assert merge_limit_args(["-l", "host1", "--tags", "base"]) == [
            "-l",
            "host1",
            "--tags",
            "base",
        ]

    def test_single_long_limit_unchanged(self):
        assert merge_limit_args(["--limit", "host1"]) == ["--limit", "host1"]

    def test_single_long_equals_form_unchanged(self):
        assert merge_limit_args(["--limit=host1"]) == ["--limit=host1"]

    def test_two_short_flags_merged(self):
        assert merge_limit_args(["-l", "host1", "-l", "host2"]) == ["-l", "host1,host2"]

    def test_two_long_flags_merged(self):
        assert merge_limit_args(["--limit", "host1", "--limit", "host2"]) == [
            "--limit",
            "host1,host2",
        ]

    def test_equals_form_merged(self):
        assert merge_limit_args(["--limit=host1", "--limit=host2"]) == [
            "--limit",
            "host1,host2",
        ]

    def test_mixed_short_and_long_uses_first_form(self):
        assert merge_limit_args(["-l", "host1", "--limit", "host2"]) == ["-l", "host1,host2"]

    def test_three_flags_merged(self):
        assert merge_limit_args(["-l", "a", "-l", "b", "-l", "c"]) == ["-l", "a,b,c"]

    def test_preserves_surrounding_args(self):
        result = merge_limit_args(
            ["site.yml-not-really", "-l", "host1", "--tags", "base", "-l", "host2", "-vvv"]
        )
        assert result == [
            "site.yml-not-really",
            "-l",
            "host1,host2",
            "--tags",
            "base",
            "-vvv",
        ]

    def test_merged_flag_lives_at_first_limit_position(self):
        result = merge_limit_args(["-i", "inv.ini", "-l", "host1", "--tags", "base", "-l", "host2"])
        assert result == ["-i", "inv.ini", "-l", "host1,host2", "--tags", "base"]

    def test_comma_value_combined_with_single_value(self):
        assert merge_limit_args(["-l", "host1,host2", "-l", "host3"]) == [
            "-l",
            "host1,host2,host3",
        ]

    def test_does_not_dedupe_intentionally(self):
        # Dedup would silently change semantics if the user passed the same
        # host twice on purpose (rare, but their call). Pass-through is safer.
        assert merge_limit_args(["-l", "host1", "-l", "host1"]) == ["-l", "host1,host1"]

    def test_trailing_lone_short_flag_is_left_alone(self):
        # A bare `-l` at the end of args has no value — ansible-playbook will
        # error on it. AOM has no business inventing one, so leave it for
        # ansible to complain about.
        assert merge_limit_args(["-l"]) == ["-l"]

    def test_trailing_lone_short_flag_with_one_preceding_pair(self):
        # First `-l host1` is a complete pair, trailing `-l` is dangling. Only
        # one real limit value exists, so no merging is needed — pass through.
        assert merge_limit_args(["-l", "host1", "-l"]) == ["-l", "host1", "-l"]
