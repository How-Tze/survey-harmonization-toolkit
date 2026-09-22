from __future__ import annotations

from typing import Any

import pandas as pd

from survey_harmonization.models import MappingRule
from survey_harmonization.utils import code_key


def apply_transform(series: pd.Series, rule: MappingRule) -> pd.Series:
    if not rule.executable or rule.transform is None:
        raise ValueError("Blocked mappings are not executable")
    if rule.transform == "identity":
        return series.copy()
    if rule.transform == "categorical_recode":
        value_map = {
            str(key): value
            for key, value in rule.transform_params["value_map"].items()
        }
        return series.map(
            lambda value: pd.NA if pd.isna(value) else value_map.get(code_key(value), pd.NA)
        )
    numeric = pd.to_numeric(series, errors="coerce")
    if rule.transform == "numeric_bin":
        params = rule.transform_params
        return pd.cut(
            numeric,
            bins=params["breaks"],
            labels=params["labels"],
            right=False,
            include_lowest=True,
        ).astype("string")
    if rule.transform == "scale_shift":
        return numeric + float(rule.transform_params["add"])
    if rule.transform == "reverse_scale":
        minimum = float(rule.transform_params["source_min"])
        maximum = float(rule.transform_params["source_max"])
        return minimum + maximum - numeric
    raise ValueError(f"Unsupported transform: {rule.transform}")


def coerce_canonical(series: pd.Series, canonical_type: str) -> pd.Series:
    if canonical_type == "integer":
        return pd.to_numeric(series, errors="coerce").astype("Int64")
    if canonical_type == "number":
        return pd.to_numeric(series, errors="coerce").astype("Float64")
    return series.astype("string")
