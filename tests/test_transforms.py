from __future__ import annotations

import pandas as pd
import pytest

from survey_harmonization.models import MappingRule
from survey_harmonization.transforms import apply_transform


def rule(transform: str | None, params=None, status="approved") -> MappingRule:
    return MappingRule(
        dataset_id="demo",
        canonical_variable="x",
        source_variable="x",
        review_status=status,
        transform=transform,
        transform_params=params or {},
    )


def test_all_fixed_transforms() -> None:
    values = pd.Series([1, 2, pd.NA], dtype="object")
    assert apply_transform(values, rule("identity")).tolist()[:2] == [1, 2]
    recoded = apply_transform(
        values, rule("categorical_recode", {"value_map": {"1": "a", "2": "b"}})
    )
    assert recoded.tolist()[:2] == ["a", "b"]
    binned = apply_transform(
        pd.Series([8, 12, 16]),
        rule("numeric_bin", {"breaks": [0, 12, 16, 30], "labels": ["low", "mid", "high"]}),
    )
    assert binned.tolist() == ["low", "mid", "high"]
    assert apply_transform(pd.Series([0, 4]), rule("scale_shift", {"add": 1})).tolist() == [1.0, 5.0]
    assert apply_transform(
        pd.Series([1, 5]), rule("reverse_scale", {"source_min": 1, "source_max": 5})
    ).tolist() == [5.0, 1.0]


def test_blocked_mapping_never_executes() -> None:
    with pytest.raises(ValueError, match="not executable"):
        apply_transform(pd.Series([1]), rule(None, status="ambiguous"))
