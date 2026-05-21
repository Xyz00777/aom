"""Integration tests for run_preflight against a fake ansible-playbook."""

from __future__ import annotations

import shlex
import sys
import textwrap
from pathlib import Path


def _make_fake_ansible(
    tmp_path: Path,
    *,
    list_tasks_stdout: str = "",
    list_hosts_stdout: str = "",
    list_tasks_exit: int = 0,
    list_hosts_exit: int = 0,
) -> Path:
    """Create a Python script that mimics ansible-playbook --list-tasks/--list-hosts."""
    script = tmp_path / "ansible-playbook"
    body = textwrap.dedent(
        f"""
        #!{sys.executable}
        import sys

        args = sys.argv[1:]
        if "--list-tasks" in args:
            sys.stdout.write({list_tasks_stdout!r})
            sys.exit({list_tasks_exit})
        elif "--list-hosts" in args:
            sys.stdout.write({list_hosts_stdout!r})
            sys.exit({list_hosts_exit})
        else:
            sys.exit(2)
        """
    ).lstrip()
    script.write_text(body)
    script.chmod(0o755)
    return script


def test_run_preflight_runs_both_commands_and_assembles_definitions(
    tmp_path: Path, list_tasks_output: str, list_hosts_output: str
) -> None:
    from ansible_aom.ansible.preflight import run_preflight

    fake = _make_fake_ansible(
        tmp_path,
        list_tasks_stdout=list_tasks_output,
        list_hosts_stdout=list_hosts_output,
    )

    result = run_preflight(
        playbook="site.yml",
        ansible_args=[],
        executable=str(fake),
    )

    assert result.errors == []
    assert len(result.plays) == 2
    assert len(result.play_hosts) == 2
    assert len(result.definitions) == 2
    assert result.definitions[0].resolved_hosts == ["web1.example.com", "web2.example.com"]


def test_run_preflight_executable_not_found_records_error(tmp_path: Path) -> None:
    from ansible_aom.ansible.preflight import run_preflight

    result = run_preflight(
        playbook="site.yml",
        ansible_args=[],
        executable=str(tmp_path / "does-not-exist"),
    )

    assert result.definitions == []
    assert result.plays == []
    assert any("not found" in err.lower() or "no such" in err.lower() for err in result.errors)


def test_run_preflight_list_hosts_failure_yields_definitions_without_resolved_hosts(
    tmp_path: Path, list_tasks_output: str
) -> None:
    from ansible_aom.ansible.preflight import run_preflight

    fake = _make_fake_ansible(
        tmp_path,
        list_tasks_stdout=list_tasks_output,
        list_hosts_stdout="",
        list_hosts_exit=1,
    )

    result = run_preflight(
        playbook="site.yml",
        ansible_args=[],
        executable=str(fake),
    )

    assert len(result.plays) == 2
    assert len(result.definitions) == 2
    assert result.definitions[0].resolved_hosts == []
    assert any("--list-hosts" in err for err in result.errors)


def test_run_preflight_sets_ansible_nocolor_env(tmp_path: Path) -> None:
    """ANSIBLE_NOCOLOR=1 must be set so ansible-playbook emits stderr without colours.

    Without this, ansible suppresses error output entirely when stderr
    is not a TTY (which is always the case for our captured subprocess).
    """
    log = tmp_path / "env.log"
    script = tmp_path / "ansible-playbook"
    body = (
        f"#!{sys.executable}\n"
        "import os\n"
        f"open({str(log)!r}, 'a').write(os.environ.get('ANSIBLE_NOCOLOR', '<unset>') + chr(10))\n"
        "import sys; sys.exit(0)\n"
    )
    script.write_text(body)
    script.chmod(0o755)

    from ansible_aom.ansible.preflight import run_preflight

    run_preflight(playbook="site.yml", ansible_args=[], executable=str(script))

    lines = log.read_text().splitlines()
    assert lines == ["1", "1"]


def test_run_preflight_trims_argparse_help_wall_from_error(tmp_path: Path) -> None:
    """When ansible-playbook fails with an argparse error, only the error line surfaces."""
    from ansible_aom.ansible.preflight import run_preflight

    fake_stderr = (
        "usage: ansible-playbook [-h] [--version]\n"
        "                        playbook [playbook ...]\n"
        "ansible-playbook: error: unrecognized arguments: extra.yml\n"
        "\n"
        "usage: ansible-playbook [-h] [--version]\n"
        "Runs Ansible playbooks, executing the defined tasks on the targeted hosts.\n"
        "  -h, --help            show this help message and exit\n"
    )
    script = tmp_path / "ansible-playbook"
    body = f"#!{sys.executable}\nimport sys\nsys.stderr.write({fake_stderr!r})\nsys.exit(2)\n"
    script.write_text(body)
    script.chmod(0o755)

    result = run_preflight(playbook="site.yml", ansible_args=[], executable=str(script))

    joined = "\n".join(result.errors)
    assert "unrecognized arguments: extra.yml" in joined
    assert "show this help message" not in joined
    assert "positional arguments" not in joined
    assert "Runs Ansible playbooks" not in joined


def test_run_preflight_passes_ansible_args(tmp_path: Path) -> None:
    """Args like -i inventory.ini must reach both subprocess invocations."""
    from ansible_aom.ansible.preflight import run_preflight

    log = tmp_path / "args.log"
    script = tmp_path / "ansible-playbook"
    body = (
        f"#!{sys.executable}\n"
        "import sys\n"
        f"open({str(log)!r}, 'a').write(' '.join(sys.argv[1:]) + chr(10))\n"
        "sys.exit(0)\n"
    )
    script.write_text(body)
    script.chmod(0o755)

    run_preflight(
        playbook="site.yml",
        ansible_args=["-i", "inv.ini", "-c", "local"],
        executable=str(script),
    )

    lines = log.read_text().splitlines()
    assert len(lines) == 2
    for line in lines:
        parts = shlex.split(line)
        assert "site.yml" in parts
        assert "-i" in parts and "inv.ini" in parts
        assert "-c" in parts and "local" in parts
