from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from survey_harmonization.models import (
    CanonicalVariable,
    DatasetSpec,
    MappingRule,
    ProjectConfig,
)


REVIEW_STATUSES = {"approved", "ambiguous", "unavailable", "unreviewed"}
TRANSFORMS = {
    "identity",
    "categorical_recode",
    "numeric_bin",
    "scale_shift",
    "reverse_scale",
}
FORMATS = {"csv", "spss", "stata"}
CANONICAL_TYPES = {"integer", "number", "categorical", "ordinal"}


class ConfigError(ValueError):
    pass


def _read_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ConfigError(f"{path.name} must contain a YAML mapping")
    return value


def _safe_relative(root: Path, raw_path: str, label: str, require_exists: bool) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        raise ConfigError(f"{label} must be relative: {raw_path}")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ConfigError(f"{label} escapes project root: {raw_path}")
    if require_exists and not resolved.is_file():
        raise ConfigError(f"{label} not found: {raw_path}")
    return resolved


def _validate_transform(rule: MappingRule, errors: list[str]) -> None:
    prefix = f"{rule.dataset_id}/{rule.canonical_variable}"
    if rule.review_status not in REVIEW_STATUSES:
        errors.append(f"{prefix}: invalid review_status {rule.review_status!r}")
        return
    if rule.review_status != "approved":
        if rule.transform is not None:
            errors.append(f"{prefix}: blocked mappings must use transform: null")
        if rule.missing_values or rule.routing or rule.transform_params:
            errors.append(f"{prefix}: blocked mappings cannot declare executable preprocessing")
        if rule.review_status == "unavailable" and rule.source_variable is not None:
            errors.append(f"{prefix}: unavailable mappings must use source_variable: null")
        if rule.review_status in {"ambiguous", "unreviewed"} and not rule.source_variable:
            errors.append(f"{prefix}: {rule.review_status} mapping needs a candidate source_variable")
        return
    if not rule.source_variable:
        errors.append(f"{prefix}: approved mapping requires source_variable")
    if rule.transform not in TRANSFORMS:
        errors.append(f"{prefix}: unsupported transform {rule.transform!r}")
        return
    params = rule.transform_params
    if rule.transform == "categorical_recode" and not isinstance(params.get("value_map"), dict):
        errors.append(f"{prefix}: categorical_recode requires value_map")
    if rule.transform == "categorical_recode" and isinstance(params.get("value_map"), dict):
        expected = {str(value) for value in rule.expected_source.get("allowed_values", [])}
        mapped = {str(value) for value in params["value_map"]}
        if expected and not expected.issubset(mapped):
            errors.append(f"{prefix}: value_map does not cover reviewed allowed_values")
    if rule.transform == "numeric_bin":
        breaks, labels = params.get("breaks"), params.get("labels")
        if not isinstance(breaks, list) or not isinstance(labels, list) or len(breaks) != len(labels) + 1:
            errors.append(f"{prefix}: numeric_bin requires len(breaks) = len(labels) + 1")
    if rule.transform == "scale_shift" and not isinstance(params.get("add"), (int, float)):
        errors.append(f"{prefix}: scale_shift requires numeric add")
    if rule.transform == "reverse_scale":
        if not isinstance(params.get("source_min"), (int, float)) or not isinstance(params.get("source_max"), (int, float)):
            errors.append(f"{prefix}: reverse_scale requires source_min and source_max")


def load_project_config(config_dir: Path, *, require_files: bool = True) -> ProjectConfig:
    config_dir = config_dir.resolve()
    root = config_dir.parent
    dataset_path = config_dir / "datasets.yaml"
    canonical_path = config_dir / "canonical_variables.yaml"
    mapping_path = config_dir / "mappings.yaml"
    docs = [_read_yaml(path) for path in (dataset_path, canonical_path, mapping_path)]
    dataset_doc, canonical_doc, mapping_doc = docs
    errors: list[str] = []

    datasets: list[DatasetSpec] = []
    seen_datasets: set[str] = set()
    for raw in dataset_doc.get("datasets", []):
        try:
            spec = DatasetSpec(
                dataset_id=str(raw["dataset_id"]),
                survey_id=str(raw["survey_id"]),
                survey_name=str(raw["survey_name"]),
                wave_id=str(raw["wave_id"]),
                path=str(raw["path"]),
                format=str(raw["format"]),
                respondent_id=str(raw["respondent_id"]),
                weight_variable=(str(raw["weight_variable"]) if raw.get("weight_variable") else None),
                codebook_path=(str(raw["codebook_path"]) if raw.get("codebook_path") else None),
                universe_note=str(raw.get("universe_note", "")),
                source_note=str(raw.get("source_note", "")),
                license_status=str(raw.get("license_status", "")),
            )
        except (KeyError, TypeError) as error:
            errors.append(f"invalid dataset entry: {error}")
            continue
        if spec.dataset_id in seen_datasets:
            errors.append(f"duplicate dataset_id: {spec.dataset_id}")
        seen_datasets.add(spec.dataset_id)
        if spec.format not in FORMATS:
            errors.append(f"{spec.dataset_id}: unsupported format {spec.format!r}")
        if spec.license_status != "synthetic":
            errors.append(f"{spec.dataset_id}: v0.1 accepts synthetic inputs only")
        try:
            _safe_relative(root, spec.path, f"{spec.dataset_id} path", require_files)
            if spec.codebook_path:
                _safe_relative(root, spec.codebook_path, f"{spec.dataset_id} codebook_path", require_files)
        except ConfigError as error:
            errors.append(str(error))
        datasets.append(spec)

    canonical: list[CanonicalVariable] = []
    seen_canonical: set[str] = set()
    for raw in canonical_doc.get("canonical_variables", []):
        try:
            item = CanonicalVariable(
                name=str(raw["name"]),
                label=str(raw["label"]),
                type=str(raw["type"]),
                required=bool(raw.get("required", False)),
                allowed_values=tuple(str(value) for value in raw.get("allowed_values", [])),
                minimum=(float(raw["minimum"]) if raw.get("minimum") is not None else None),
                maximum=(float(raw["maximum"]) if raw.get("maximum") is not None else None),
                interpretation_note=str(raw.get("interpretation_note", "")),
            )
        except (KeyError, TypeError, ValueError) as error:
            errors.append(f"invalid canonical variable: {error}")
            continue
        if item.name in seen_canonical:
            errors.append(f"duplicate canonical variable: {item.name}")
        seen_canonical.add(item.name)
        if item.type not in CANONICAL_TYPES:
            errors.append(f"{item.name}: unsupported canonical type {item.type!r}")
        if item.minimum is not None and item.maximum is not None and item.minimum > item.maximum:
            errors.append(f"{item.name}: minimum exceeds maximum")
        if item.type in {"categorical", "ordinal"} and not item.allowed_values and item.minimum is None:
            errors.append(f"{item.name}: categorical/ordinal definition needs values or a numeric range")
        canonical.append(item)

    raw_groups = mapping_doc.get("mappings", {})
    rule_version = int(mapping_doc.get("rule_version", 1))
    mappings: list[MappingRule] = []
    expected_dataset_ids = {item.dataset_id for item in datasets}
    if set(raw_groups) != expected_dataset_ids:
        errors.append(
            f"mapping dataset grid mismatch: expected={sorted(expected_dataset_ids)} actual={sorted(raw_groups)}"
        )
    for dataset_id, raw_rules in raw_groups.items():
        if not isinstance(raw_rules, dict):
            errors.append(f"{dataset_id}: mapping group must be a mapping")
            continue
        if set(raw_rules) != seen_canonical:
            errors.append(
                f"{dataset_id}: canonical mapping grid mismatch: missing={sorted(seen_canonical - set(raw_rules))} extra={sorted(set(raw_rules) - seen_canonical)}"
            )
        for canonical_name, raw in raw_rules.items():
            raw = raw or {}
            rule = MappingRule(
                dataset_id=str(dataset_id),
                canonical_variable=str(canonical_name),
                source_variable=(str(raw["source_variable"]) if raw.get("source_variable") is not None else None),
                review_status=str(raw.get("review_status", "")),
                transform=(str(raw["transform"]) if raw.get("transform") is not None else None),
                missing_values={str(key): str(value) for key, value in (raw.get("missing_values") or {}).items()},
                routing=dict(raw.get("routing") or {}),
                expected_source=dict(raw.get("expected_source") or {}),
                transform_params=dict(raw.get("transform_params") or {}),
                review_note=str(raw.get("review_note", "")),
                comparability_warning=str(raw.get("comparability_warning", "")),
                rule_version=rule_version,
            )
            _validate_transform(rule, errors)
            mappings.append(rule)

    if errors:
        raise ConfigError("Configuration errors:\n- " + "\n- ".join(errors))
    return ProjectConfig(
        root=root,
        datasets=tuple(datasets),
        canonical_variables=tuple(canonical),
        mappings=tuple(mappings),
        config_paths=(dataset_path, canonical_path, mapping_path),
    )
