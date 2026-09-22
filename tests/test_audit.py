from __future__ import annotations

from pathlib import Path

import pandas as pd

from survey_harmonization.audit import audit_mapping
from survey_harmonization.config import load_project_config
from survey_harmonization.readers import read_dataset
from survey_harmonization.transforms import apply_transform


def test_declared_and_structural_missing_are_separate(config_dir: Path) -> None:
    config = load_project_config(config_dir)
    spec = next(item for item in config.datasets if item.dataset_id == "civiclife_2018")
    view = read_dataset(spec, config.root)
    rule = next(
        item
        for item in config.mappings_for(spec.dataset_id)
        if item.canonical_variable == "work_autonomy"
    )
    coverage, rows, cleaned, issues = audit_mapping(view, rule)
    counts = {row["missing_class"]: row["count"] for row in rows}
    assert coverage["valid_source_n"] == 15
    assert counts["dont_know"] == 1
    assert counts["structural_missing"] == 8
    assert not issues

    raw = view.frame[rule.source_variable].copy()
    declared_index = raw.index[raw.eq(-8)][0]
    transformed = apply_transform(cleaned, rule)
    assert pd.isna(cleaned.loc[declared_index])
    assert pd.isna(transformed.loc[declared_index])
    pd.testing.assert_series_equal(view.frame[rule.source_variable], raw)


def test_blocked_statuses_are_all_present(config_dir: Path) -> None:
    config = load_project_config(config_dir)
    statuses = {rule.review_status for rule in config.mappings if not rule.executable}
    assert statuses == {"ambiguous", "unavailable", "unreviewed"}


def test_unexpected_source_value_is_an_error(config_dir: Path) -> None:
    config = load_project_config(config_dir)
    spec = next(item for item in config.datasets if item.dataset_id == "civiclife_2018")
    view = read_dataset(spec, config.root)
    rule = next(
        item
        for item in config.mappings_for(spec.dataset_id)
        if item.canonical_variable == "age"
    )
    view.frame.loc[0, rule.source_variable] = 999
    coverage, _, _, issues = audit_mapping(view, rule)
    assert coverage["unexpected_n"] == 1
    assert any(item["code"] == "unexpected_source_value" for item in issues)
