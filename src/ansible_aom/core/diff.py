"""Pure formatting of module-supplied Ansible result diffs."""

import json
from collections.abc import Mapping
from difflib import unified_diff


def format_result_diff(result: Mapping[str, object]) -> list[str]:
    """Return plain diff lines for a changed, uncensored module result."""
    if not result.get("changed") or result.get("_ansible_no_log") or "censored" in result:
        return []
    payload = result.get("diff")
    entries = payload if isinstance(payload, list) else [payload]
    lines: list[str] = []
    for entry in entries:
        if isinstance(entry, str):
            lines.extend(entry.splitlines())
            continue
        if not isinstance(entry, Mapping) or entry.get("_ansible_no_log") or "censored" in entry:
            continue
        for side, label in (("dst", "destination"), ("src", "source")):
            if f"{side}_binary" in entry:
                lines.append(f"diff skipped: {label} file appears to be binary")
        for side, label in (("dst", "destination"), ("src", "source")):
            if f"{side}_larger" in entry:
                lines.append(
                    f"diff skipped: {label} file size is greater than {entry[f'{side}_larger']}"
                )
        if "before" in entry and "after" in entry:
            before = _diff_text(entry["before"])
            after = _diff_text(entry["after"])
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
                    lines.append(line.rstrip("\r\n"))
                    if not line.endswith("\n"):
                        lines.append(r"\ No newline at end of file")
        prepared = entry.get("prepared")
        if isinstance(prepared, str):
            lines.extend(prepared.splitlines())
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
