"""The runner prints a `Session …  aom inspect` footer on termination."""

from ansible_aom.runner import _print_session_footer


def test_footer_prints_short_id_and_inspect_hint(capsys):
    _print_session_footer(
        session_id="019e4520-fa64-7000-a627-5b8efe0da85f",
        stderr_isatty=True,
    )
    captured = capsys.readouterr()
    # Footer goes to stderr so it survives `aom site.yml | tee log`.
    assert "019e4520" in captured.err
    assert "aom inspect" in captured.err


def test_footer_suppressed_when_no_session_id(capsys):
    _print_session_footer(session_id=None, stderr_isatty=True)
    captured = capsys.readouterr()
    assert captured.err == ""


def test_footer_suppressed_when_stderr_not_tty(capsys):
    _print_session_footer(
        session_id="019e4520-fa64-7000-a627-5b8efe0da85f",
        stderr_isatty=False,
    )
    captured = capsys.readouterr()
    assert captured.err == ""
