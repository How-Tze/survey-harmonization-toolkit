from __future__ import annotations

from typing import Any

import pandas as pd

from survey_harmonization.audit import issue
from survey_harmonization.models import DatasetView, ProjectConfig
from survey_harmonization.utils import is_system_missing


def validate_source_view(view: DatasetView) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    identifier = view.spec.respondent_id
    if identifier not in view.frame.columns:
        return [
            issue(
                "error",
                "respondent_id_missing",
                view.spec.dataset_id,
                "respondent_id",
                1,
                f"Respondent ID field {identifier!r} is absent.",
            )
        ]
    values = view.frame[identifier]
    missing = values.map(is_system_missing)
    duplicates = values[~missing].duplicated(keep=False)
    if missing.any():
        issues.append(
            issue(
                "error",
                "respondent_id_null",
                view.spec.dataset_id,
                "respondent_id",
                int(missing.sum()),
                "Respondent IDs must be nonmissing within each source file.",
            )
        )
    if duplicates.any():
        issues.append(
            issue(
                "error",
                "respondent_id_duplicate",
                view.spec.dataset_id,
                "respondent_id",
                int(duplicates.sum()),
                "Respondent IDs must be unique within each source file.",
            )
        )
    return issues


def validate_harmonized(
    frame: pd.DataFrame,
    config: ProjectConfig,
    expected_rows: int,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if len(frame) != expected_rows:
        issues.append(
            issue(
                "error",
                "row_accounting_mismatch",
                "all",
                "all",
                abs(len(frame) - expected_rows),
                f"Expected {expected_rows} rows but produced {len(frame)}.",
            )
        )
    compound_duplicates = frame.duplicated(
        subset=["dataset_id", "respondent_id"], keep=False
    )
    if compound_duplicates.any():
        issues.append(
            issue(
                "error",
                "harmonized_id_duplicate",
                "all",
                "respondent_id",
                int(compound_duplicates.sum()),
                "dataset_id + respondent_id must be unique in harmonized output.",
            )
        )

    canonical = config.canonical_by_name()
    for variable, definition in canonical.items():
        values = frame[variable]
        present = values.notna()
        if definition.allowed_values:
            invalid = present & ~values.astype("string").isin(definition.allowed_values)
        else:
            numeric = pd.to_numeric(values, errors="coerce")
            invalid = present & numeric.isna()
            if definition.minimum is not None:
                invalid |= present & numeric.lt(definition.minimum)
            if definition.maximum is not None:
                invalid |= present & numeric.gt(definition.maximum)
        if invalid.any():
            issues.append(
                issue(
                    "error",
                    "canonical_value_invalid",
                    "all",
                    variable,
                    int(invalid.sum()),
                    "Harmonized values violate the canonical definition.",
                )
            )

    for rule in config.mappings:
        if rule.executable:
            continue
        mask = frame["dataset_id"].eq(rule.dataset_id)
        leaked = frame.loc[mask, rule.canonical_variable].notna()
        if leaked.any():
            issues.append(
                issue(
                    "error",
                    "blocked_mapping_executed",
                    rule.dataset_id,
                    rule.canonical_variable,
                    int(leaked.sum()),
                    "A blocked mapping produced harmonized values.",
                )
            )
    return issues
