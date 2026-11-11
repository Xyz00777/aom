"""Module diff payloads become plain lines without changing recorded results."""

from copy import deepcopy

import pytest

from ansible_aom.core.diff import format_result_diff


def test_text_diff_preserves_headers_context_and_hunks():
    result = {
        "changed": True,
        "diff": {
            "before": "keep\nx=1\ntail\n",
            "after": "keep\nx=2\ntail\n",
            "before_header": "/etc/example (original)",
            "after_header": "/etc/example (updated)",
        },
    }
    assert format_result_diff(result) == [
        "--- before: /etc/example (original)",
        "+++ after: /etc/example (updated)",
        "@@ -1,3 +1,3 @@",
        " keep",
        "-x=1",
        "+x=2",
        " tail",
    ]


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        ("x=1\n", "x=2\n", ["--- before", "+++ after", "@@ -1 +1 @@", "-x=1", "+x=2"]),
        ("same\n", "same\n", []),
        ("", "", []),
        (None, "new\n", ["--- before", "+++ after", "@@ -0,0 +1 @@", "+new"]),
        ("old\n", None, ["--- before", "+++ after", "@@ -1 +0,0 @@", "-old"]),
        (
            "old",
            "new",
            [
                "--- before",
                "+++ after",
                "@@ -1 +1 @@",
                "-old",
                r"\ No newline at end of file",
                "+new",
                r"\ No newline at end of file",
            ],
        ),
        (
            "same",
            "same\n",
            [
                "--- before",
                "+++ after",
                "@@ -1 +1 @@",
                "-same",
                r"\ No newline at end of file",
                "+same",
            ],
        ),
    ],
)
def test_text_diff_edges(before, after, expected):
    assert (
        format_result_diff({"changed": True, "diff": {"before": before, "after": after}})
        == expected
    )


def test_list_and_prepared_and_recorded_string_diffs_keep_order():
    assert format_result_diff(
        {
            "changed": True,
            "diff": [
                {"prepared": "first\nsecond\n"},
                {"before": "a\n", "after": "b\n"},
                "--- recorded\n+++ text\n@@ -1 +1 @@\n-old\n+new\n",
            ],
        }
    ) == [
        "first",
        "second",
        "--- before",
        "+++ after",
        "@@ -1 +1 @@",
        "-a",
        "+b",
        "--- recorded",
        "+++ text",
        "@@ -1 +1 @@",
        "-old",
        "+new",
    ]


def test_mapping_content_is_sorted_and_input_is_immutable():
    result = {
        "changed": True,
        "diff": {
            "before": {"z": 0, "a": {"y": 1, "b": 2}},
            "after": {"a": {"b": 3, "y": 1}, "z": 0},
        },
    }
    original = deepcopy(result)
    assert format_result_diff(result) == [
        "--- before",
        "+++ after",
        "@@ -1,6 +1,6 @@",
        " {",
        '     "a": {',
        '-        "b": 2,',
        '+        "b": 3,',
        '         "y": 1',
        "     },",
        '     "z": 0',
    ]
    assert result == original


def test_binary_and_oversize_notices():
    assert format_result_diff(
        {
            "changed": True,
            "diff": {
                "dst_binary": 1,
                "src_binary": 1,
                "dst_larger": 1024,
                "src_larger": 2048,
            },
        }
    ) == [
        "diff skipped: destination file appears to be binary",
        "diff skipped: source file appears to be binary",
        "diff skipped: destination file size is greater than 1024",
        "diff skipped: source file size is greater than 2048",
    ]


@pytest.mark.parametrize(
    "extra", [{"changed": False}, {"_ansible_no_log": True}, {"censored": "hidden"}]
)
def test_unchanged_or_censored_results_emit_no_diff(extra):
    result = {"changed": True, "diff": {"prepared": "private"}, **extra}
    assert format_result_diff(result) == []


@pytest.mark.parametrize("diff", [None, {}, [], 12, {"before": "incomplete"}, {"prepared": None}])
def test_missing_or_unsupported_diff_is_silent(diff):
    assert format_result_diff({"changed": True, "diff": diff}) == []


def test_nested_censored_diff_is_suppressed():
    assert format_result_diff(
        {
            "changed": True,
            "diff": [
                {"_ansible_no_log": True, "prepared": "private"},
                {"censored": "hidden", "before": "secret\n", "after": "another\n"},
                {"prepared": "public"},
            ],
        }
    ) == ["public"]


def test_surrogates_are_safe_to_encode():
    assert format_result_diff({"changed": True, "diff": {"prepared": "bad\udcff text"}}) == [
        r"bad\udcff text"
    ]


def test_multiple_hunks_keep_first_and_last_changed_lines():
    result = {
        "changed": True,
        "diff": {
            "before": "old-first\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10\nold-last\n",
            "after": "new-first\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10\nnew-last\n",
        },
    }
    assert format_result_diff(result) == [
        "--- before",
        "+++ after",
        "@@ -1,4 +1,4 @@",
        "-old-first",
        "+new-first",
        " 1",
        " 2",
        " 3",
        "@@ -9,4 +9,4 @@",
        " 8",
        " 9",
        " 10",
        "-old-last",
        "+new-last",
    ]


def test_list_contents_are_pretty_printed_without_mutation():
    result = {"changed": True, "diff": {"before": [1, 2], "after": [1, 3]}}
    original = deepcopy(result)
    assert format_result_diff(result) == [
        "--- before",
        "+++ after",
        "@@ -1,4 +1,4 @@",
        " [",
        "     1,",
        "-    2",
        "+    3",
        " ]",
    ]
    assert result == original


def test_equal_mappings_in_different_key_order_have_no_changes():
    assert (
        format_result_diff(
            {
                "changed": True,
                "diff": {
                    "before": {"z": 2, "a": 1},
                    "after": {"a": 1, "z": 2},
                },
            }
        )
        == []
    )


def test_historical_top_level_string_diff():
    assert format_result_diff({"changed": True, "diff": "-old\n+new\n"}) == ["-old", "+new"]


def test_crlf_content_produces_plain_lines_without_terminal_carriage_returns():
    assert format_result_diff(
        {
            "changed": True,
            "diff": {
                "before": "context\r\nold\r\n",
                "after": "context\r\nnew\r\n",
            },
        }
    ) == ["--- before", "+++ after", "@@ -1,2 +1,2 @@", " context", "-old", "+new"]
