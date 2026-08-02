from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "ansible"


def test_ansible_fixture_tree_is_repository_local() -> None:
    required_paths = (
        "simple.yml",
        "with_include.yml",
        "included_tasks.yml",
        "with_role_rel_include.yml",
        "roles/test_role/tasks/main.yml",
        "roles/podman_role_rel/tasks/_includes/setup.yml",
    )

    assert all((FIXTURES_DIR / path).is_file() for path in required_paths)
