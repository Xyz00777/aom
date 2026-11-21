"""Pure formatting of module-supplied Ansible result diffs."""

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from difflib import unified_diff

MAX_DIFF_LINES = 200
MAX_DIFF_BYTES = 16_384
_TRUNCATION = f"... diff truncated ({MAX_DIFF_LINES} lines, {MAX_DIFF_BYTES} bytes)"


@dataclass(slots=True)
class DiffBudget:
    """Plain diff-line content budget, shared by aggregate loop previews.

    UTF-8 bytes count line contents and the truncation marker, but exclude
    inter-line separators and compact-renderer indentation or ANSI styling.
    """

    lines: int = MAX_DIFF_LINES
    bytes: int = MAX_DIFF_BYTES
    truncated: bool = False


def _append_line(lines: list[str], line: str, budget: DiffBudget) -> bool:
    marker_bytes = len(_TRUNCATION.encode("utf-8"))
    line_bytes = len(line.encode("utf-8", errors="backslashreplace"))
    if budget.lines <= 1 or line_bytes > budget.bytes - marker_bytes:
        budget.truncated = True
        return False
    lines.append(line)
    budget.lines -= 1
    budget.bytes -= line_bytes
    return True


def _fits_source_budget(value: object) -> bool:
    """Check source size before materializing normalized structured text."""
    if isinstance(value, str):
        if len(value) > MAX_DIFF_BYTES:
            return False
        return len(value.encode("utf-8", errors="backslashreplace")) <= MAX_DIFF_BYTES
    if not isinstance(value, (Mapping, list)):
        return True
    pending: list[Iterator[object]] = [iter((value,))]
    visited = 0
    while pending:
        try:
            current = next(pending[-1])
        except StopIteration:
            pending.pop()
            continue
        visited += 1
        if visited > MAX_DIFF_BYTES:
            return False
        if isinstance(current, str):
            if len(current) > MAX_DIFF_BYTES:
                return False
            continue
        if isinstance(current, Mapping):
            pending.append(iter(current.keys()))
            pending.append(iter(current.values()))
        elif isinstance(current, list):
            pending.append(iter(current))
    encoded_bytes = 0
    for chunk in json.JSONEncoder(sort_keys=True, indent=4, ensure_ascii=False).iterencode(value):
        encoded_bytes += len(chunk.encode("utf-8", errors="backslashreplace"))
        if encoded_bytes > MAX_DIFF_BYTES:
            return False
    return True


def format_result_diff(result: Mapping[str, object], budget: DiffBudget | None = None) -> list[str]:
    """Return bounded plain diff lines, before renderer indentation or ANSI styling."""
    if not result.get("changed") or result.get("_ansible_no_log") or "censored" in result:
        return []
    output_budget = budget if budget is not None else DiffBudget()
    payload = result.get("diff")
    entries = payload if isinstance(payload, list) else [payload]
    lines: list[str] = []
    for entry in entries:
        if output_budget.lines <= 1 or output_budget.bytes <= len(_TRUNCATION.encode("utf-8")):
            output_budget.truncated = True
            break
        if isinstance(entry, str):
            bounded_text = entry[: output_budget.bytes]
            if len(bounded_text) < len(entry):
                output_budget.truncated = True
            for line in bounded_text.splitlines():
                if not _append_line(lines, line, output_budget):
                    break
            if output_budget.truncated:
                break
            continue
        if not isinstance(entry, Mapping) or entry.get("_ansible_no_log") or "censored" in entry:
            continue
        for side, label in (("dst", "destination"), ("src", "source")):
            if f"{side}_binary" in entry:
                if not _append_line(
                    lines, f"diff skipped: {label} file appears to be binary", output_budget
                ):
                    break
        for side, label in (("dst", "destination"), ("src", "source")):
            if f"{side}_larger" in entry:
                if not _append_line(
                    lines,
                    f"diff skipped: {label} file size is greater than {entry[f'{side}_larger']}",
                    output_budget,
                ):
                    break
        if output_budget.truncated:
            break
        if "before" in entry and "after" in entry:
            before_value = entry["before"]
            after_value = entry["after"]
            if not all(_fits_source_budget(value) for value in (before_value, after_value)):
                output_budget.truncated = True
                break
            before = _diff_text(before_value)
            after = _diff_text(after_value)
            if before is not None and after is not None:
                before_header = "before"
                after_header = "after"
                if "before_header" in entry:
                    before_header += f": {entry['before_header']}"
                if "after_header" in entry:
                    after_header += f": {entry['after_header']}"
                for line in unified_diff(
                    before.splitlines(keepends=True),
                    after.splitlines(keepends=True),
                    fromfile=before_header,
                    tofile=after_header,
                    n=3,
                ):
                    if not _append_line(lines, line.rstrip("\r\n"), output_budget):
                        break
                    if not line.endswith("\n"):
                        if not _append_line(lines, r"\ No newline at end of file", output_budget):
                            break
                if output_budget.truncated:
                    break
        prepared = entry.get("prepared")
        if isinstance(prepared, str):
            bounded_text = prepared[: output_budget.bytes]
            if len(bounded_text) < len(prepared):
                output_budget.truncated = True
            for line in bounded_text.splitlines():
                if not _append_line(lines, line, output_budget):
                    break
        if output_budget.truncated:
            break
    if output_budget.truncated:
        marker_bytes = len(_TRUNCATION.encode("utf-8"))
        if output_budget.lines > 0 and output_budget.bytes >= marker_bytes:
            output_budget.lines -= 1
            output_budget.bytes -= marker_bytes
        lines.append(_TRUNCATION)
    return [line.encode("utf-8", errors="backslashreplace").decode("utf-8") for line in lines]


def _diff_text(value: object) -> str | None:
    """Normalize JSON content without mutating the source payload."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (Mapping, list)):
        return json.dumps(value, sort_keys=True, indent=4, ensure_ascii=False) + "\n"
    return None
