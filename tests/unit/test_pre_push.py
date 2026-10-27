import os
import subprocess
from pathlib import Path
from typing import Final

import pytest

HOOK: Final = Path(__file__).resolve().parents[2] / ".githooks" / "pre-push"


@pytest.mark.parametrize("run_rc", [0, 7])
def test_pre_push_requests_test_extras_for_both_phases(tmp_path: Path, run_rc: int) -> None:
    # Given a clean tree and a uv environment that needs the dev extra.
    git = tmp_path / "git"
    git.write_text(
        '#!/usr/bin/env bash\nif [[ "$1" == rev-parse ]]; then pwd; fi\n',
        encoding="utf-8",
    )
    git.chmod(0o755)
    uv = tmp_path / "uv"
    uv.write_text(
        "#!/usr/bin/env bash\n"
        '[[ " $* " == *" --extra dev "* ]] || exit 127\n'
        '[[ " $* " == *" --extra integration "* ]] || exit 127\n'
        'if [[ " $* " == *" --collect-only "* ]]; then\n'
        "    printf 'tests/unit/test_example.py::test_example\\n'\n"
        "else\n"
        '    exit "$TEST_RUN_RC"\n'
        "fi\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)

    # When Git invokes the actual pre-push hook.
    result = subprocess.run(
        ["bash", str(HOOK)],
        cwd=tmp_path,
        env=os.environ | {"PATH": f"{tmp_path}:{os.environ['PATH']}", "TEST_RUN_RC": str(run_rc)},
        capture_output=True,
        text=True,
        check=False,
    )

    # Then collection and execution work, preserving the test runner's status.
    assert "running 1 affected test(s)" in result.stdout
    assert result.returncode == run_rc, result.stderr
