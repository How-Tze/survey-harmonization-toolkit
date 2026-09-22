from __future__ import annotations

from pathlib import Path

from survey_harmonization.config import load_project_config
from survey_harmonization.readers import read_dataset


def test_all_three_formats_and_labels(config_dir: Path) -> None:
    config = load_project_config(config_dir)
    selected = {}
    for spec in config.datasets:
        selected.setdefault(spec.format, spec)
    assert set(selected) == {"csv", "spss", "stata"}
    views = {name: read_dataset(spec, config.root) for name, spec in selected.items()}
    assert all(len(view.frame) == 24 for view in views.values())
    assert views["spss"].value_labels["sex"]["1"] == "Man"
    assert views["stata"].value_labels["sex_code"]["1"] == "Woman"
    assert views["csv"].value_labels["edu_code"]["3"] == "Tertiary"


def test_reader_preserves_numeric_codes(config_dir: Path) -> None:
    config = load_project_config(config_dir)
    spec = next(item for item in config.datasets if item.dataset_id == "civiclife_2018")
    view = read_dataset(spec, config.root)
    assert set(view.frame["sex"].dropna().unique()) == {1.0, 2.0}
