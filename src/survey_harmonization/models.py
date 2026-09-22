from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class DatasetSpec:
    dataset_id: str
    survey_id: str
    survey_name: str
    wave_id: str
    path: str
    format: str
    respondent_id: str
    weight_variable: str | None
    codebook_path: str | None
    universe_note: str
    source_note: str
    license_status: str


@dataclass(frozen=True)
class CanonicalVariable:
    name: str
    label: str
    type: str
    required: bool
    allowed_values: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    interpretation_note: str = ""


@dataclass(frozen=True)
class MappingRule:
    dataset_id: str
    canonical_variable: str
    source_variable: str | None
    review_status: str
    transform: str | None
    missing_values: dict[str, str] = field(default_factory=dict)
    routing: dict[str, Any] = field(default_factory=dict)
    expected_source: dict[str, Any] = field(default_factory=dict)
    transform_params: dict[str, Any] = field(default_factory=dict)
    review_note: str = ""
    comparability_warning: str = ""
    rule_version: int = 1

    @property
    def executable(self) -> bool:
        return self.review_status == "approved"


@dataclass(frozen=True)
class ProjectConfig:
    root: Path
    datasets: tuple[DatasetSpec, ...]
    canonical_variables: tuple[CanonicalVariable, ...]
    mappings: tuple[MappingRule, ...]
    config_paths: tuple[Path, ...]

    def canonical_by_name(self) -> dict[str, CanonicalVariable]:
        return {item.name: item for item in self.canonical_variables}

    def mappings_for(self, dataset_id: str) -> tuple[MappingRule, ...]:
        return tuple(rule for rule in self.mappings if rule.dataset_id == dataset_id)


@dataclass
class DatasetView:
    spec: DatasetSpec
    frame: pd.DataFrame
    schema_rows: list[dict[str, Any]]
    value_labels: dict[str, dict[str, str]]
