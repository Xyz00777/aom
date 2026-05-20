"""Guard: tests must not write into the real ~/.local/state/aom path.

The autouse ``isolated_state_dir`` fixture in ``tests/conftest.py``
monkeypatches the module-level helpers; this test verifies the patch is
taking effect by re-reading the attribute lazily (a top-level
``from ansible_aom.runner import _default_session_dir`` would bind the
original function before the fixture runs).
"""

import ansible_aom.inspect.cli
import ansible_aom.runner


def test_runner_state_dir_is_isolated():
    p = str(ansible_aom.runner._default_session_dir())
    assert "aom-state-iso" in p
    assert "/.local/state/aom/sessions" not in p


def test_inspect_state_dir_is_isolated():
    p = str(ansible_aom.inspect.cli._default_state_dir())
    assert "aom-state-iso" in p
    assert "/.local/state/aom/sessions" not in p
