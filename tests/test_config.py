from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from survey_harmonization.config import ConfigError, load_project_config


def copy_config(config_dir: Path, tmp_path: Path) -> Path:
    target = tmp_path / "config"
    shutil.copytree(config_dir, target)
    return target


def test_complete_config_grid(config_dir: Path) -> None:
    config = load_project_config(config_dir)
    assert len(config.datasets) == 7
    assert len(config.canonical_variables) == 10
    assert len(config.mappings) == 70
    assert sum(rule.executable for rule in config.mappings) == 65


def test_derive_transform_is_rejected(config_dir: Path, tmp_path: Path) -> None:
    target = copy_config(config_dir, tmp_path)
    path = target / "mappings.yaml"
    text = path.read_text(encoding="utf-8").replace(
        "transform: identity", "transform: derive", 1
    )
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ConfigError, match="unsupported transform"):
        load_project_config(target, require_files=False)


def test_blocked_mapping_cannot_execute(config_dir: Path, tmp_path: Path) -> None:
    target = copy_config(config_dir, tmp_path)
    path = target / "mappings.yaml"
    text = path.read_text(encoding="utf-8").replace(
        "review_status: ambiguous\n      transform: null",
        "review_status: ambiguous\n      transform: identity",
        1,
    )
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ConfigError, match="blocked mappings must use transform"):
        load_project_config(target, require_files=False)


def test_absolute_dataset_path_is_rejected(config_dir: Path, tmp_path: Path) -> None:
    target = copy_config(config_dir, tmp_path)
    path = target / "datasets.yaml"
    absolute = (tmp_path.anchor or "/") + "synthetic-forbidden.sav"
    text = path.read_text(encoding="utf-8").replace(
        "data/synthetic/sources/civiclife_2018.sav", absolute, 1
    )
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ConfigError, match="must be relative"):
        load_project_config(target, require_files=False)
