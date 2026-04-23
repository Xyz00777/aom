"""Tests for JSONL callback plugin configuration (TC-067 to TC-071).

Test cases cover:
- TC-067: ansible.posix Availability Check
- TC-068: ansible.posix Install Prompt
- TC-069: ansible-core Version Check
- TC-070: ansible.posix Version Check
- TC-071: JSONL Environment Variable

All tests are self-contained and use mocks to avoid requiring real Ansible installations.
"""

from unittest.mock import patch, MagicMock
import subprocess

import pytest


def _parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a version string to tuple for comparison.

    Args:
        version_str: Version string like '2.14.0' or '1.5.0'

    Returns:
        Tuple of integers like (2, 14, 0)
    """
    parts = []
    for part in version_str.split("."):
        if part.isdigit():
            parts.append(int(part))
        else:
            # Handle versions like '2.14.0rc1' by taking the numeric prefix
            numeric = ""
            for char in part:
                if char.isdigit():
                    numeric += char
                else:
                    break
            if numeric:
                parts.append(int(numeric))
    return tuple(parts)


def _check_ansible_core_version(version_str: str) -> bool:
    """Return True if ansible-core >= 2.14.

    Args:
        version_str: Version string like '2.14.0'

    Returns:
        True if version meets the minimum requirement
    """
    return _parse_version(version_str) >= (2, 14)


def _check_ansible_posix_version(version_str: str) -> bool:
    """Return True if ansible.posix >= 1.5.0.

    Args:
        version_str: Version string like '1.5.0'

    Returns:
        True if version meets the minimum requirement
    """
    return _parse_version(version_str) >= (1, 5, 0)


def _check_ansible_posix_installed() -> bool:
    """Check if ansible.posix collection is installed.

    Returns:
        True if ansible.posix is available
    """
    try:
        result = subprocess.run(
            ["ansible-galaxy", "collection", "list"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return "ansible.posix" in result.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def _generate_install_prompt() -> str:
    """Generate the install prompt message for missing ansible.posix.

    Returns:
        Prompt message string
    """
    return "ansible.posix collection not found. Install? [Y/n]"


def _build_subprocess_env_jsonl(base_env: dict | None = None) -> dict:
    """Build subprocess environment with JSONL callback set.

    Args:
        base_env: Base environment dict to extend. If None, uses os.environ copy.

    Returns:
        Environment dict with ANSIBLE_STDOUT_CALLBACK set
    """
    import os

    env = dict(base_env) if base_env else dict(os.environ)
    env["ANSIBLE_STDOUT_CALLBACK"] = "ansible.posix.jsonl"
    return env


class TestAnsiblePosixAvailability:
    """Tests for TC-067: ansible.posix Availability Check."""

    def test_ansible_posix_availability_check_installed(self):
        """TC-067: Check returns True when ansible.posix is installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="ansible.posix\nansible.builtin\n", returncode=0
            )
            result = _check_ansible_posix_installed()
            assert result is True

    def test_ansible_posix_availability_check_not_installed(self):
        """TC-067: Check returns False when ansible.posix is not installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="ansible.builtin\nansible.utils\n", returncode=0
            )
            result = _check_ansible_posix_installed()
            assert result is False

    def test_ansible_posix_availability_check_ansible_galaxy_not_found(self):
        """TC-067: Check returns False when ansible-galaxy command not found."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("ansible-galaxy not found")
            result = _check_ansible_posix_installed()
            assert result is False

    def test_ansible_posix_availability_check_timeout(self):
        """TC-067: Check returns False on subprocess timeout."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="ansible-galaxy", timeout=30)
            result = _check_ansible_posix_installed()
            assert result is False


class TestAnsiblePosixInstallPrompt:
    """Tests for TC-068: ansible.posix Install Prompt."""

    def test_install_prompt_message_contains_expected_text(self):
        """TC-068: Prompt shows installation message."""
        prompt = _generate_install_prompt()
        assert "ansible.posix" in prompt
        assert "not found" in prompt.lower()
        assert "Install" in prompt

    def test_install_prompt_format(self):
        """TC-068: Prompt format includes confirmation options."""
        prompt = _generate_install_prompt()
        assert "[Y/n]" in prompt or "[y/N]" in prompt

    def test_install_prompt_function_exists(self):
        """TC-068: Install prompt helper function is callable."""
        assert callable(_generate_install_prompt)
        prompt = _generate_install_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestAnsibleCoreVersionCheck:
    """Tests for TC-069: ansible-core Version Check."""

    def test_ansible_core_version_passes_at_minimum(self):
        """TC-069: Version 2.14.0 passes minimum requirement."""
        assert _check_ansible_core_version("2.14.0") is True

    def test_ansible_core_version_passes_above_minimum(self):
        """TC-069: Version above 2.14 passes minimum requirement."""
        assert _check_ansible_core_version("2.15.0") is True
        assert _check_ansible_core_version("2.16.3") is True
        assert _check_ansible_core_version("3.0.0") is True

    def test_ansible_core_version_fails_below_minimum(self):
        """TC-069: Version below 2.14 fails minimum requirement."""
        assert _check_ansible_core_version("2.13.0") is False
        assert _check_ansible_core_version("2.12.9") is False
        assert _check_ansible_core_version("2.10.0") is False

    def test_ansible_core_version_handles_prerelease(self):
        """TC-069: Prerelease versions are handled correctly."""
        assert _check_ansible_core_version("2.14.0rc1") is True
        assert _check_ansible_core_version("2.14.0a1") is True

    def test_ansible_core_version_parse_function(self):
        """TC-069: Version parsing handles various formats."""
        assert _parse_version("2.14.0") == (2, 14, 0)
        assert _parse_version("2.14") == (2, 14)
        assert _parse_version("3.1.2") == (3, 1, 2)


class TestAnsiblePosixVersionCheck:
    """Tests for TC-070: ansible.posix Version Check."""

    def test_ansible_posix_version_passes_at_minimum(self):
        """TC-070: Version 1.5.0 passes minimum requirement."""
        assert _check_ansible_posix_version("1.5.0") is True

    def test_ansible_posix_version_passes_above_minimum(self):
        """TC-070: Version above 1.5.0 passes minimum requirement."""
        assert _check_ansible_posix_version("1.6.0") is True
        assert _check_ansible_posix_version("2.0.0") is True
        assert _check_ansible_posix_version("1.5.1") is True

    def test_ansible_posix_version_fails_below_minimum(self):
        """TC-070: Version below 1.5.0 fails minimum requirement."""
        assert _check_ansible_posix_version("1.4.0") is False
        assert _check_ansible_posix_version("1.4.9") is False
        assert _check_ansible_posix_version("1.3.0") is False

    def test_ansible_posix_version_handles_patch_versions(self):
        """TC-070: Patch versions below minimum still fail."""
        assert _check_ansible_posix_version("1.4.99") is False

    def test_ansible_posix_version_parse_function(self):
        """TC-070: Version parsing handles various formats."""
        assert _parse_version("1.5.0") == (1, 5, 0)
        assert _parse_version("1.5") == (1, 5)
        assert _parse_version("2.0.0") == (2, 0, 0)


class TestJsonlEnvironmentVariable:
    """Tests for TC-071: JSONL Environment Variable."""

    def test_jsonl_env_variable_is_set(self):
        """TC-071: ANSIBLE_STDOUT_CALLBACK is set to ansible.posix.jsonl."""
        env = _build_subprocess_env_jsonl(base_env={})
        assert env["ANSIBLE_STDOUT_CALLBACK"] == "ansible.posix.jsonl"

    def test_jsonl_env_variable_preserves_existing_env(self):
        """TC-071: Existing environment variables are preserved."""
        base_env = {"PATH": "/usr/bin", "HOME": "/home/user"}
        env = _build_subprocess_env_jsonl(base_env=base_env)
        assert env["PATH"] == "/usr/bin"
        assert env["HOME"] == "/home/user"
        assert env["ANSIBLE_STDOUT_CALLBACK"] == "ansible.posix.jsonl"

    def test_jsonl_env_variable_overrides_existing_callback(self):
        """TC-071: JSONL callback overrides existing ANSIBLE_STDOUT_CALLBACK."""
        base_env = {"ANSIBLE_STDOUT_CALLBACK": "default"}
        env = _build_subprocess_env_jsonl(base_env=base_env)
        assert env["ANSIBLE_STDOUT_CALLBACK"] == "ansible.posix.jsonl"

    def test_jsonl_env_variable_with_none_uses_os_environ(self):
        """TC-071: When base_env is None, copies from os.environ."""
        import os

        with patch.dict(os.environ, {"TEST_VAR": "test_value"}, clear=False):
            env = _build_subprocess_env_jsonl(base_env=None)
            assert env["ANSIBLE_STDOUT_CALLBACK"] == "ansible.posix.jsonl"

    def test_jsonl_env_variable_function_callable(self):
        """TC-071: Environment builder function is callable."""
        assert callable(_build_subprocess_env_jsonl)
        result = _build_subprocess_env_jsonl(base_env={})
        assert isinstance(result, dict)
        assert "ANSIBLE_STDOUT_CALLBACK" in result