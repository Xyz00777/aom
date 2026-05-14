"""Tests for the overhead-section formatter in inspect display."""

from __future__ import annotations

from ansible_aom.core.overhead import OverheadStats
from ansible_aom.inspect.display import format_overhead_section


def _stats(
    samples: int = 12,
    distinct_tasks: int = 4,
    distinct_hosts: int = 3,
    overhead_floor_s: float | None = 0.142,
    median_duration_s: float | None = 0.340,
    wall_clock_s: float | None = 51.8,
    estimated_overhead_wall_s: float | None = 4 * 0.142,
    overhead_share: float | None = (4 * 0.142) / 51.8,
) -> OverheadStats:
    return OverheadStats(
        samples=samples,
        distinct_tasks=distinct_tasks,
        distinct_hosts=distinct_hosts,
        overhead_floor_s=overhead_floor_s,
        median_duration_s=median_duration_s,
        wall_clock_s=wall_clock_s,
        estimated_overhead_wall_s=estimated_overhead_wall_s,
        overhead_share=overhead_share,
    )


class TestZeroSamples:
    def test_returns_none_when_no_samples(self) -> None:
        stats = OverheadStats(
            samples=0,
            distinct_tasks=0,
            distinct_hosts=0,
            overhead_floor_s=None,
            median_duration_s=None,
            wall_clock_s=None,
            estimated_overhead_wall_s=None,
            overhead_share=None,
        )
        assert format_overhead_section(stats) is None


class TestInsufficientSamples:
    def test_shows_one_line_about_insufficient_data(self) -> None:
        stats = OverheadStats(
            samples=2,
            distinct_tasks=2,
            distinct_hosts=1,
            overhead_floor_s=None,
            median_duration_s=None,
            wall_clock_s=10.0,
            estimated_overhead_wall_s=None,
            overhead_share=None,
        )
        out = format_overhead_section(stats)
        assert out is not None
        assert "insufficient" in out.lower()
        assert "2" in out  # sample count surfaced


class TestFullStats:
    def test_section_contains_floor_and_median(self) -> None:
        out = format_overhead_section(_stats())
        assert out is not None
        # Floor 142 ms and median 340 ms expressed in ms.
        assert "142" in out
        assert "340" in out

    def test_section_mentions_estimated_overhead_seconds(self) -> None:
        out = format_overhead_section(_stats())
        assert out is not None
        # 4 * 0.142 = 0.568 s, formatter renders sub-second as ms → "568 ms".
        assert "568 ms" in out

    def test_section_includes_percent_share_when_available(self) -> None:
        out = format_overhead_section(_stats())
        assert out is not None
        # 0.568 / 51.8 ≈ 1.1%.
        assert "%" in out
        assert "1" in out  # the digit

    def test_omits_share_line_when_wall_clock_missing(self) -> None:
        stats = _stats(wall_clock_s=None, overhead_share=None, estimated_overhead_wall_s=4 * 0.142)
        out = format_overhead_section(stats)
        assert out is not None
        assert "%" not in out

    def test_includes_sample_count(self) -> None:
        out = format_overhead_section(_stats())
        assert out is not None
        assert "12" in out  # samples


class TestFormatting:
    def test_floor_below_one_second_uses_ms(self) -> None:
        stats = _stats(overhead_floor_s=0.085, median_duration_s=0.250)
        out = format_overhead_section(stats)
        assert out is not None
        assert "85" in out
        assert "ms" in out.lower()

    def test_floor_at_or_above_one_second_uses_s(self) -> None:
        stats = _stats(overhead_floor_s=1.4, median_duration_s=2.1)
        out = format_overhead_section(stats)
        assert out is not None
        assert "1.4" in out
        assert " s" in out

    def test_section_has_header(self) -> None:
        out = format_overhead_section(_stats())
        assert out is not None
        assert "overhead" in out.lower()
