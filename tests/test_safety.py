from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from survey_harmonization.config import load_project_config
from survey_harmonization.pipeline import run_pipeline
from survey_harmonization.utils import sha256


TEXT_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".toml", ".gitignore"}


def test_project_contains_no_absolute_paths_or_network_urls(project_root: Path) -> None:
    findings = []
    for path in project_root.rglob("*"):
        if not path.is_file() or any(
            part in {".venv", ".testenv", ".pytest_cache"} for part in path.parts
        ):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        drive_path = re.search(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/](?![nrt])", text)
        user_root = "/" + "Users" + "/"
        if drive_path or user_root in text:
            findings.append(f"absolute path in {path.relative_to(project_root)}")
        if re.search(r"https?://", text):
            findings.append(f"network URL in {path.relative_to(project_root)}")
        markers = (
            "api" + "_" + "key",
            "access" + "_" + "token",
            "private" + "_" + "key",
        )
        if any(marker in text.lower() for marker in markers):
            findings.append(f"secret marker in {path.relative_to(project_root)}")
    assert findings == []


def test_pipeline_does_not_modify_sources(config_dir: Path, tmp_path: Path) -> None:
    config = load_project_config(config_dir)
    before = {spec.path: sha256(config.root / spec.path) for spec in config.datasets}
    result = run_pipeline(
        config_dir, tmp_path / "immutability", run_timestamp="2026-09-22T00:00:00Z"
    )
    after = {spec.path: sha256(config.root / spec.path) for spec in config.datasets}
    assert before == after
    assert result["source_files_unchanged"] is True


def test_generator_is_byte_deterministic(project_root: Path, config_dir: Path) -> None:
    config = load_project_config(config_dir)
    before = {spec.path: sha256(config.root / spec.path) for spec in config.datasets}
    subprocess.run(
        [sys.executable, str(project_root / "scripts" / "generate_synthetic_data.py")],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )
    after = {spec.path: sha256(config.root / spec.path) for spec in config.datasets}
    assert before == after


def test_generated_outputs_contain_no_machine_paths_or_urls(
    config_dir: Path, tmp_path: Path
) -> None:
    output = tmp_path / "safe-output"
    run_pipeline(
        config_dir, output, run_timestamp="2026-09-22T00:00:00Z"
    )
    drive_pattern = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/](?![nrt])")
    user_root = "/" + "Users" + "/"
    for path in output.iterdir():
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert not drive_pattern.search(text), path.name
        assert user_root not in text, path.name
        assert not re.search(r"https?://", text), path.name


def test_runtime_and_environment_paths_are_ignored(project_root: Path) -> None:
    entries = {
        line.strip()
        for line in (project_root / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert {"output/", ".venv/", ".testenv/", ".pytest_cache/", "__pycache__/"} <= entries
