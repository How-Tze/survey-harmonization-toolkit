from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd

from survey_harmonization.models import DatasetView, MappingRule
from survey_harmonization.utils import code_key, is_system_missing


def _unexpected_mask(series: pd.Series, expected: dict[str, Any]) -> pd.Series:
    mask = pd.Series(False, index=series.index)
    present = series.notna()
    if "allowed_values" in expected:
        allowed = {str(value) for value in expected["allowed_values"]}
        return present & ~series.map(lambda value: code_key(value) in allowed if not pd.isna(value) else True)
    if "minimum" in expected or "maximum" in expected:
        numeric = pd.to_numeric(series, errors="coerce")
        mask |= present & numeric.isna()
        if expected.get("minimum") is not None:
            mask |= present & numeric.lt(float(expected["minimum"]))
        if expected.get("maximum") is not None:
            mask |= present & numeric.gt(float(expected["maximum"]))
    return mask


def audit_mapping(
    view: DatasetView, rule: MappingRule
) -> tuple[dict[str, Any], list[dict[str, Any]], pd.Series, list[dict[str, Any]]]:
    frame = view.frame
    source_present = bool(rule.source_variable and rule.source_variable in frame.columns)
    base = {
        "dataset_id": view.spec.dataset_id,
        "survey_id": view.spec.survey_id,
        "wave_id": view.spec.wave_id,
        "canonical_variable": rule.canonical_variable,
        "source_variable": rule.source_variable or "",
        "review_status": rule.review_status,
        "transform": rule.transform or "",
        "source_present": source_present,
        "rows": len(frame),
    }
    issues: list[dict[str, Any]] = []
    empty = pd.Series(pd.NA, index=frame.index, dtype="object")
    if not source_present:
        coverage = {
            **base,
            "raw_nonmissing_n": 0,
            "valid_source_n": 0,
            "declared_missing_n": 0,
            "system_missing_n": 0,
            "structural_missing_n": 0,
            "unexpected_n": 0,
        }
        if rule.review_status != "unavailable":
            issues.append(
                issue(
                    "error",
                    "source_variable_missing",
                    view.spec.dataset_id,
                    rule.canonical_variable,
                    1,
                    f"Configured source variable {rule.source_variable!r} is absent.",
                )
            )
        else:
            issues.append(
                issue(
                    "warning",
                    "mapping_blocked",
                    view.spec.dataset_id,
                    rule.canonical_variable,
                    1,
                    rule.review_note or "Source variable is unavailable for this wave.",
                )
            )
        return coverage, [], empty, issues

    source = frame[rule.source_variable].copy()
    raw_nonmissing = ~source.map(is_system_missing)
    if not rule.executable:
        coverage = {
            **base,
            "raw_nonmissing_n": int(raw_nonmissing.sum()),
            "valid_source_n": 0,
            "declared_missing_n": 0,
            "system_missing_n": int((~raw_nonmissing).sum()),
            "structural_missing_n": 0,
            "unexpected_n": 0,
        }
        issues.append(
            issue(
                "warning",
                "mapping_blocked",
                view.spec.dataset_id,
                rule.canonical_variable,
                1,
                rule.review_note or f"Mapping status is {rule.review_status}.",
            )
        )
        return coverage, [], empty, issues

    system_mask = source.map(is_system_missing)
    structural_mask = pd.Series(False, index=source.index)
    if rule.routing:
        indicator = str(rule.routing.get("indicator", ""))
        if indicator not in frame.columns:
            issues.append(
                issue(
                    "error",
                    "routing_indicator_missing",
                    view.spec.dataset_id,
                    rule.canonical_variable,
                    1,
                    f"Routing indicator {indicator!r} is absent.",
                )
            )
        else:
            eligible = {str(value) for value in rule.routing.get("eligible_values", [])}
            eligible_mask = frame[indicator].map(
                lambda value: code_key(value) in eligible if not is_system_missing(value) else False
            )
            structural_mask = system_mask & ~eligible_mask

    declared_class = pd.Series("", index=source.index, dtype="string")
    for raw_code, classification in rule.missing_values.items():
        matches = source.map(
            lambda value: False if is_system_missing(value) else code_key(value) == str(raw_code)
        )
        declared_class.loc[matches] = classification
    declared_mask = declared_class.ne("")
    ordinary_system = system_mask & ~structural_mask
    cleaned = source.mask(system_mask | declared_mask, pd.NA)
    unexpected_mask = _unexpected_mask(cleaned, rule.expected_source)
    valid_mask = cleaned.notna() & ~unexpected_mask

    missing_counts = Counter(str(value) for value in declared_class[declared_mask])
    missing_rows = [
        {
            "dataset_id": view.spec.dataset_id,
            "survey_id": view.spec.survey_id,
            "wave_id": view.spec.wave_id,
            "canonical_variable": rule.canonical_variable,
            "source_variable": rule.source_variable,
            "missing_class": classification,
            "count": int(count),
        }
        for classification, count in sorted(missing_counts.items())
    ]
    missing_rows.extend(
        [
            {
                "dataset_id": view.spec.dataset_id,
                "survey_id": view.spec.survey_id,
                "wave_id": view.spec.wave_id,
                "canonical_variable": rule.canonical_variable,
                "source_variable": rule.source_variable,
                "missing_class": "system_missing",
                "count": int(ordinary_system.sum()),
            },
            {
                "dataset_id": view.spec.dataset_id,
                "survey_id": view.spec.survey_id,
                "wave_id": view.spec.wave_id,
                "canonical_variable": rule.canonical_variable,
                "source_variable": rule.source_variable,
                "missing_class": "structural_missing",
                "count": int(structural_mask.sum()),
            },
            {
                "dataset_id": view.spec.dataset_id,
                "survey_id": view.spec.survey_id,
                "wave_id": view.spec.wave_id,
                "canonical_variable": rule.canonical_variable,
                "source_variable": rule.source_variable,
                "missing_class": "unexpected_source_value",
                "count": int(unexpected_mask.sum()),
            },
        ]
    )
    if unexpected_mask.any():
        issues.append(
            issue(
                "error",
                "unexpected_source_value",
                view.spec.dataset_id,
                rule.canonical_variable,
                int(unexpected_mask.sum()),
                "Observed source values fall outside the reviewed range or categories.",
            )
        )
    coverage = {
        **base,
        "raw_nonmissing_n": int(raw_nonmissing.sum()),
        "valid_source_n": int(valid_mask.sum()),
        "declared_missing_n": int(declared_mask.sum()),
        "system_missing_n": int(ordinary_system.sum()),
        "structural_missing_n": int(structural_mask.sum()),
        "unexpected_n": int(unexpected_mask.sum()),
    }
    return coverage, missing_rows, cleaned, issues


def issue(
    severity: str,
    code: str,
    dataset_id: str,
    canonical_variable: str,
    count: int,
    message: str,
) -> dict[str, Any]:
    return {
        "severity": severity,
        "code": code,
        "dataset_id": dataset_id,
        "canonical_variable": canonical_variable,
        "count": count,
        "message": message,
    }


def mapping_review_row(view: DatasetView, rule: MappingRule) -> dict[str, Any]:
    block_reason = "" if rule.executable else (rule.review_note or rule.review_status)
    return {
        "dataset_id": view.spec.dataset_id,
        "survey_id": view.spec.survey_id,
        "wave_id": view.spec.wave_id,
        "canonical_variable": rule.canonical_variable,
        "source_variable": rule.source_variable or "",
        "review_status": rule.review_status,
        "executable": rule.executable,
        "transform": rule.transform or "",
        "routing_indicator": str(rule.routing.get("indicator", "")),
        "missing_rule_count": len(rule.missing_values),
        "review_note": rule.review_note,
        "comparability_warning": rule.comparability_warning,
        "block_reason": block_reason,
        "rule_version": rule.rule_version,
    }
