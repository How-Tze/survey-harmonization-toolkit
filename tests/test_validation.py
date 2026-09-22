from __future__ import annotations

from pathlib import Path

from survey_harmonization.config import load_project_config
from survey_harmonization.readers import read_dataset
from survey_harmonization.validate import validate_source_view


def test_duplicate_ids_are_errors(config_dir: Path) -> None:
    config = load_project_config(config_dir)
    spec = config.datasets[0]
    view = read_dataset(spec, config.root)
    view.frame.loc[1, spec.respondent_id] = view.frame.loc[0, spec.respondent_id]
    issues = validate_source_view(view)
    assert any(item["code"] == "respondent_id_duplicate" for item in issues)


def test_main_sources_have_unique_ids(config_dir: Path) -> None:
    config = load_project_config(config_dir)
    for spec in config.datasets:
        assert not validate_source_view(read_dataset(spec, config.root))
