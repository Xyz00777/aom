"""Text normalisation shared by the display and storage boundaries."""


def replace_surrogates(s: str) -> str:
    """Replace lone-surrogate codepoints in ``s`` with ``?``.

    The runner decodes PTY output with ``surrogateescape``, so invalid
    UTF-8 bytes become lone surrogates that round-trip losslessly through
    ``str`` and ``events.jsonl``. Neither a terminal nor sqlite TEXT can
    take them, so text leaving for either goes through here. Strings
    without surrogates are returned unchanged.
    """
    if s.isascii():
        return s
    return s.encode("utf-8", "replace").decode("utf-8")
