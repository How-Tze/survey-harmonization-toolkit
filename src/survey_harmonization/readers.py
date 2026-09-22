from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pyreadstat
import yaml

from survey_harmonization.models import DatasetSpec, DatasetView
from survey_harmonization.utils import code_key


def _schema_row(
    spec: DatasetSpec,
    position: int,
    variable: str,
    label: str,
    storage_type: str,
    value_label_set: str,
    labels_present: bool,
) -> dict[str, Any]:
    return {
        "dataset_id": spec.dataset_id,
        "survey_id": spec.survey_id,
        "wave_id": spec.wave_id,
        "position": position,
        "variable": variable,
        "variable_label": label,
        "storage_type": storage_type,
        "value_label_set": value_label_set,
        "value_labels_present": labels_present,
        "source_format": spec.format,
    }


def _read_spss(spec: DatasetSpec, path: Path) -> DatasetView:
    frame, metadata = pyreadstat.read_sav(
        str(path), apply_value_formats=False, user_missing=True
    )
    names = list(metadata.column_names)
    labels = metadata.column_names_to_labels or {}
    types = metadata.original_variable_types or {}
    variable_to_label = metadata.variable_to_label or {}
    label_sets = metadata.value_labels or {}
    value_labels: dict[str, dict[str, str]] = {}
    schema: list[dict[str, Any]] = []
    for position, variable in enumerate(names, start=1):
        set_name = str(variable_to_label.get(variable, "") or "")
        mapping = label_sets.get(set_name, {}) if set_name else {}
        if mapping:
            value_labels[variable] = {
                code_key(code): str(label) for code, label in mapping.items()
            }
        schema.append(
            _schema_row(
                spec,
                position,
                variable,
                str(labels.get(variable, "") or ""),
                str(types.get(variable, "") or frame[variable].dtype),
                set_name,
                bool(mapping),
            )
        )
    return DatasetView(spec, frame, schema, value_labels)


def _read_stata(spec: DatasetSpec, path: Path) -> DatasetView:
    reader = pd.io.stata.StataReader(
        path, convert_categoricals=False, convert_missing=True
    )
    reader._ensure_open()
    names = list(reader._varlist)
    labels = list(reader._variable_labels)
    types = list(reader._typlist)
    formats = list(reader._fmtlist)
    label_names = list(reader._lbllist)
    label_sets = reader.value_labels()
    frame = reader.read()
    value_labels: dict[str, dict[str, str]] = {}
    schema: list[dict[str, Any]] = []
    for index, variable in enumerate(names):
        set_name = str(label_names[index] or "")
        mapping = label_sets.get(set_name, {}) if set_name else {}
        if mapping:
            value_labels[variable] = {
                code_key(code): str(label) for code, label in mapping.items()
            }
        schema.append(
            _schema_row(
                spec,
                index + 1,
                variable,
                str(labels[index] or ""),
                f"{types[index]} {formats[index]}",
                set_name,
                bool(mapping),
            )
        )
    return DatasetView(spec, frame, schema, value_labels)


def _read_csv(spec: DatasetSpec, path: Path, root: Path) -> DatasetView:
    frame = pd.read_csv(path, keep_default_na=True)
    codebook: dict[str, Any] = {}
    if spec.codebook_path:
        codebook = yaml.safe_load(
            (root / spec.codebook_path).read_text(encoding="utf-8")
        ) or {}
    variables = codebook.get("variables", {})
    raw_labels = codebook.get("value_labels", {})
    value_labels = {
        str(variable): {str(code): str(label) for code, label in mapping.items()}
        for variable, mapping in raw_labels.items()
    }
    schema = []
    for position, variable in enumerate(frame.columns, start=1):
        metadata = variables.get(variable, {})
        schema.append(
            _schema_row(
                spec,
                position,
                variable,
                str(metadata.get("label", "")),
                str(metadata.get("type", frame[variable].dtype)),
                variable if variable in value_labels else "",
                variable in value_labels,
            )
        )
    return DatasetView(spec, frame, schema, value_labels)


def read_dataset(spec: DatasetSpec, root: Path) -> DatasetView:
    path = (root / spec.path).resolve()
    if spec.format == "spss":
        return _read_spss(spec, path)
    if spec.format == "stata":
        return _read_stata(spec, path)
    if spec.format == "csv":
        return _read_csv(spec, path, root)
    raise ValueError(f"Unsupported format: {spec.format}")
