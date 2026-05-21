"""Display helpers for AOM inspect output.

After the inspect rebuild this module only houses the overhead-stats
helper. The legacy session/diff/tree formatters were removed; their
replacements live in ``inspect/text.py`` (text mode) and
``tui/screens/inspect.py`` (TUI).
"""

from ansible_aom.core.overhead import OverheadStats


def _fmt_seconds(value: float) -> str:
    """Render durations: sub-second as ms, anything else as s with one decimal."""
    if value < 1.0:
        return f"{int(round(value * 1000))} ms"
    return f"{value:.1f} s"


def format_overhead_section(stats: OverheadStats) -> str | None:
    """Render the per-task overhead summary.

    Returns ``None`` when there's literally nothing useful to display
    (no measurable samples at all). When samples exist but the P25
    threshold isn't met, returns a one-line acknowledgement so the
    caller knows the analysis ran but had nothing to chew on.
    """
    if stats.samples == 0:
        return None

    lines = ["", "Per-task overhead (approximate):"]

    if stats.overhead_floor_s is None:
        lines.append(f"  insufficient data ({stats.samples} sample(s); need ≥ 4)")
        return "\n".join(lines)

    assert stats.median_duration_s is not None
    lines.append(
        f"  measured floor:    {_fmt_seconds(stats.overhead_floor_s)}"
        f"  (P25 of {stats.samples} host × task samples)"
    )
    lines.append(f"  median duration:   {_fmt_seconds(stats.median_duration_s)}")

    if stats.estimated_overhead_wall_s is not None:
        est = stats.estimated_overhead_wall_s
        if stats.overhead_share is not None:
            pct = stats.overhead_share * 100
            lines.append(
                f"  estimated setup time: ~{_fmt_seconds(est)} "
                f"({pct:.1f}% of {_fmt_seconds(stats.wall_clock_s or 0)} wall-clock)"
            )
        else:
            lines.append(f"  estimated setup time: ~{_fmt_seconds(est)}")

    return "\n".join(lines)
