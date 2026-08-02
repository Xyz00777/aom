from __future__ import annotations

import tomllib
from pathlib import Path

from ansible_aom.cli import create_parser

PROJECT_ROOT = Path(__file__).parents[2]
REPOSITORY_URL = "https://github.com/Xyz00777/aom"


def test_publication_policy_files_and_project_urls_when_reading_metadata() -> None:
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())

    assert all(
        (PROJECT_ROOT / filename).is_file()
        for filename in ("CONTRIBUTING.md", "SECURITY.md", "CODE_OF_CONDUCT.md", "SUPPORT.md")
    )
    assert project["project"]["urls"] == {
        "Homepage": REPOSITORY_URL,
        "Repository": REPOSITORY_URL,
        "Issues": f"{REPOSITORY_URL}/issues",
        "Documentation": f"{REPOSITORY_URL}/wiki",
        "Releases": f"{REPOSITORY_URL}/releases",
    }


def test_readme_disclosures_links_and_current_artifacts_when_reading_public_entrypoint() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text()
    file_locations = readme.split("## File locations", maxsplit=1)[1].split("## ", maxsplit=1)[0]

    assert "active development" in readme
    assert "AI-assisted development" in readme
    assert "as-is" in readme
    assert "no warranty" in readme
    assert "[Contributing](CONTRIBUTING.md)" in readme
    assert "[Security](SECURITY.md)" in readme
    assert "[Code of Conduct](CODE_OF_CONDUCT.md)" in readme
    assert "[Support](SUPPORT.md)" in readme
    assert "(ARCHITECTURE.md#101-gpl-subclass-concern-ansiblecallbackaom_jsonlpy)" in readme
    assert "events.jsonl" in readme
    assert "meta.json" in readme
    assert "diagnostics.json" in readme
    assert "index.db" in readme
    assert "aom_stderr_line" in readme
    assert "stderr.log" not in readme
    assert "| User config | `~/.config/aom/aom_config.yaml` (optional) |" in file_locations
    assert "| User config | `~/.config/aom/config.yaml` (optional) |" not in file_locations


def test_current_specification_and_help_when_reading_runtime_guidance() -> None:
    specification = (PROJECT_ROOT / "SPECIFICATION.md").read_text()
    session_recording = specification.split("### 6.3 Session Recording", maxsplit=1)[1].split(
        "### 6.4", maxsplit=1
    )[0]
    configuration = specification.split("## 8. Configuration", maxsplit=1)[1].split(
        "## 9. Session Inspection", maxsplit=1
    )[0]
    help_text = create_parser().format_help()

    assert "~/.config/aom/aom_config.yaml" in configuration
    assert "legacy" in configuration
    assert "events.jsonl" in session_recording
    assert "meta.json" in session_recording
    assert "diagnostics.json" in session_recording
    assert "index.db" in session_recording
    assert "aom_stderr_line" in session_recording
    assert "stderr.log" not in session_recording
    assert "~/.config/aom/aom_config.yaml" in help_text
    assert "diagnostics.json" in help_text
    assert "index.db" in help_text
    assert "aom_stderr_line" in help_text
    assert "stderr.log" not in help_text


def test_source_help_and_comments_when_describing_stderr_storage() -> None:
    replay = (PROJECT_ROOT / "src/ansible_aom/drivers/replay.py").read_text()
    inspect_model = (PROJECT_ROOT / "src/ansible_aom/core/inspect_model.py").read_text()
    inspect_screen = (PROJECT_ROOT / "src/ansible_aom/tui/screens/inspect.py").read_text()

    assert "stderr lines from stderr.log" not in replay
    assert "``stderr.log``, overall stats" not in inspect_model
    assert "session ``stderr.log``" not in inspect_screen
