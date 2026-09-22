from __future__ import annotations

from pathlib import Path

import pandas as pd

from survey_harmonization.cli import main
from survey_harmonization.config import load_project_config
from survey_harmonization.pipeline import OUTPUT_ORDER, run_pipeline
from survey_harmonization.utils import sha256


STAMP = "2026-09-22T00:00:00Z"


def test_end_to_end_outputs_and_blocks(config_dir: Path, tmp_path: Path) -> None:
    output = tmp_path / "demo"
    result = run_pipeline(config_dir, output, run_timestamp=STAMP)
    assert result == {
        "status": "completed_with_blocked_mappings",
        "output_dir": str(output.resolve()),
        "dataset_count": 7,
        "harmonized_rows": 168,
        "approved_mappings": 65,
        "blocked_mappings": 5,
        "validation_errors": 0,
        "validation_warnings": 5,
        "source_files_unchanged": True,
    }
    expected = {*OUTPUT_ORDER, "provenance_manifest.json"}
    assert {path.name for path in output.iterdir()} == expected
    data = pd.read_csv(output / "harmonized_long.csv")
    assert len(data) == 168
    config = load_project_config(config_dir)
    for rule in config.mappings:
        if not rule.executable:
            assert data.loc[
                data.dataset_id == rule.dataset_id, rule.canonical_variable
            ].isna().all()

    provenance = pd.read_json(output / "provenance_manifest.json", typ="series")
    assert len(provenance["blocked_mappings"]) == 5
    assert all("block_reason" in row for row in provenance["blocked_mappings"])


def test_outputs_are_deterministic(config_dir: Path, tmp_path: Path) -> None:
    left, right = tmp_path / "left", tmp_path / "right"
    run_pipeline(config_dir, left, run_timestamp=STAMP)
    run_pipeline(config_dir, right, run_timestamp=STAMP)
    names = [*OUTPUT_ORDER, "provenance_manifest.json"]
    assert {name: sha256(left / name) for name in names} == {
        name: sha256(right / name) for name in names
    }


def test_retained_example_matches_generated(
    project_root: Path, config_dir: Path, tmp_path: Path
) -> None:
    generated = tmp_path / "generated"
    run_pipeline(config_dir, generated, run_timestamp=STAMP)
    retained = project_root / "examples" / "demo_output"
    names = [*OUTPUT_ORDER, "provenance_manifest.json"]
    assert {name: sha256(generated / name) for name in names} == {
        name: sha256(retained / name) for name in names
    }


def test_strict_mode_reports_blocks(config_dir: Path, tmp_path: Path) -> None:
    code = main(
        [
            "run",
            "--config-dir",
            str(config_dir),
            "--output-dir",
            str(tmp_path / "strict"),
            "--run-timestamp",
            STAMP,
            "--strict",
        ]
    )
    assert code == 2
