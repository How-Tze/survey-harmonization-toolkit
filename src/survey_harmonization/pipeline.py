from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from survey_harmonization import __version__
from survey_harmonization.audit import audit_mapping, issue, mapping_review_row
from survey_harmonization.config import load_project_config
from survey_harmonization.models import ProjectConfig
from survey_harmonization.readers import read_dataset
from survey_harmonization.reporting import build_report
from survey_harmonization.transforms import apply_transform, coerce_canonical
from survey_harmonization.utils import code_key, sha256, write_csv, write_json
from survey_harmonization.validate import validate_harmonized, validate_source_view


OUTPUT_ORDER = (
    "inventory.json",
    "schema_catalog.csv",
    "value_labels.json",
    "coverage_matrix.csv",
    "missingness_audit.csv",
    "mapping_review.csv",
    "harmonized_long.csv",
    "validation_issues.csv",
    "audit_report.md",
)


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _input_paths(config: ProjectConfig) -> list[Path]:
    paths = list(config.config_paths)
    for spec in config.datasets:
        paths.append(config.root / spec.path)
        if spec.codebook_path:
            paths.append(config.root / spec.codebook_path)
    return paths


def _empty_output(index: pd.Index, canonical_type: str) -> pd.Series:
    if canonical_type == "integer":
        return pd.Series(pd.NA, index=index, dtype="Int64")
    if canonical_type == "number":
        return pd.Series(pd.NA, index=index, dtype="Float64")
    return pd.Series(pd.NA, index=index, dtype="string")


def run_pipeline(
    config_dir: Path,
    output_dir: Path,
    *,
    run_timestamp: str,
) -> dict[str, Any]:
    config = load_project_config(config_dir)
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    input_paths = _input_paths(config)
    hashes_before = {_relative(config.root, path): sha256(path) for path in input_paths}

    views = [read_dataset(spec, config.root) for spec in config.datasets]
    canonical = config.canonical_by_name()
    inventory: list[dict[str, Any]] = []
    schema_rows: list[dict[str, Any]] = []
    value_labels: dict[str, Any] = {}
    coverage_rows: list[dict[str, Any]] = []
    missing_rows: list[dict[str, Any]] = []
    mapping_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    harmonized_parts: list[pd.DataFrame] = []

    for view in views:
        source_path = config.root / view.spec.path
        inventory.append(
            {
                "dataset_id": view.spec.dataset_id,
                "survey_id": view.spec.survey_id,
                "survey_name": view.spec.survey_name,
                "wave_id": view.spec.wave_id,
                "path": view.spec.path,
                "format": view.spec.format,
                "bytes": source_path.stat().st_size,
                "sha256": hashes_before[view.spec.path],
                "rows": len(view.frame),
                "variables": len(view.frame.columns),
                "license_status": view.spec.license_status,
                "universe_note": view.spec.universe_note,
            }
        )
        schema_rows.extend(view.schema_rows)
        value_labels[view.spec.dataset_id] = view.value_labels
        issues.extend(validate_source_view(view))

        part = pd.DataFrame(
            {
                "dataset_id": view.spec.dataset_id,
                "survey_id": view.spec.survey_id,
                "wave_id": view.spec.wave_id,
                "respondent_id": view.frame[view.spec.respondent_id].map(code_key),
            },
            index=view.frame.index,
        )
        for rule in config.mappings_for(view.spec.dataset_id):
            mapping_rows.append(mapping_review_row(view, rule))
            coverage, rule_missing, cleaned, rule_issues = audit_mapping(view, rule)
            coverage_rows.append(coverage)
            missing_rows.extend(rule_missing)
            issues.extend(rule_issues)
            definition = canonical[rule.canonical_variable]
            if not rule.executable or not coverage["source_present"]:
                part[rule.canonical_variable] = _empty_output(
                    view.frame.index, definition.type
                )
                continue
            transformed = apply_transform(cleaned, rule)
            lost = cleaned.notna() & transformed.isna()
            if lost.any():
                issues.append(
                    issue(
                        "error",
                        "transform_unmapped_value",
                        view.spec.dataset_id,
                        rule.canonical_variable,
                        int(lost.sum()),
                        "Reviewed source values were not handled by the configured transform.",
                    )
                )
            part[rule.canonical_variable] = coerce_canonical(
                transformed, definition.type
            )
        harmonized_parts.append(part)

    canonical_columns = [item.name for item in config.canonical_variables]
    harmonized = pd.concat(harmonized_parts, ignore_index=True)
    harmonized = harmonized[
        ["dataset_id", "survey_id", "wave_id", "respondent_id", *canonical_columns]
    ]
    issues.extend(
        validate_harmonized(
            harmonized,
            config,
            expected_rows=sum(len(view.frame) for view in views),
        )
    )

    source_paths = [config.root / spec.path for spec in config.datasets]
    source_hashes_after = {
        spec.path: sha256(path) for spec, path in zip(config.datasets, source_paths)
    }
    source_unchanged = all(
        source_hashes_after[spec.path] == hashes_before[spec.path]
        for spec in config.datasets
    )
    if not source_unchanged:
        issues.append(
            issue(
                "error",
                "source_file_changed",
                "all",
                "all",
                1,
                "At least one synthetic source file changed during execution.",
            )
        )

    issues = sorted(
        issues,
        key=lambda row: (
            row["severity"],
            row["code"],
            row["dataset_id"],
            row["canonical_variable"],
        ),
    )
    dataset_lineage = {
        spec.dataset_id: (spec.survey_id, spec.wave_id) for spec in config.datasets
    }
    rule_versions = {
        (rule.dataset_id, rule.canonical_variable): rule.rule_version
        for rule in config.mappings
    }
    for row in issues:
        survey_id, wave_id = dataset_lineage.get(row["dataset_id"], ("", ""))
        row["survey_id"] = survey_id
        row["wave_id"] = wave_id
        row["rule_version"] = rule_versions.get(
            (row["dataset_id"], row["canonical_variable"]), ""
        )
    blocked = [row for row in mapping_rows if not row["executable"]]
    error_count = sum(row["severity"] == "error" for row in issues)
    status = (
        "failed_validation"
        if error_count
        else "completed_with_blocked_mappings"
        if blocked
        else "complete"
    )

    schema_frame = pd.DataFrame(schema_rows).sort_values(
        ["dataset_id", "position"], kind="stable"
    )
    coverage_frame = pd.DataFrame(coverage_rows).sort_values(
        ["dataset_id", "canonical_variable"], kind="stable"
    )
    missing_frame = pd.DataFrame(missing_rows).sort_values(
        ["dataset_id", "canonical_variable", "missing_class"], kind="stable"
    )
    mapping_frame = pd.DataFrame(mapping_rows).sort_values(
        ["dataset_id", "canonical_variable"], kind="stable"
    )
    issue_columns = [
        "severity",
        "code",
        "dataset_id",
        "survey_id",
        "wave_id",
        "canonical_variable",
        "rule_version",
        "count",
        "message",
    ]
    issue_frame = pd.DataFrame(issues, columns=issue_columns)

    write_json(
        output_dir / "inventory.json",
        {"schema_version": 1, "synthetic_only": True, "datasets": inventory},
    )
    write_csv(schema_frame, output_dir / "schema_catalog.csv")
    write_json(output_dir / "value_labels.json", value_labels)
    write_csv(coverage_frame, output_dir / "coverage_matrix.csv")
    write_csv(missing_frame, output_dir / "missingness_audit.csv")
    write_csv(mapping_frame, output_dir / "mapping_review.csv")
    write_csv(harmonized, output_dir / "harmonized_long.csv")
    write_csv(issue_frame, output_dir / "validation_issues.csv")
    report = build_report(
        run_timestamp=run_timestamp,
        status=status,
        dataset_count=len(views),
        row_count=len(harmonized),
        mapping_rows=mapping_rows,
        issues=issues,
        coverage_rows=coverage_rows,
        missing_rows=missing_rows,
    )
    (output_dir / "audit_report.md").write_text(
        report, encoding="utf-8", newline="\n"
    )

    output_hashes = {
        name: sha256(output_dir / name) for name in OUTPUT_ORDER
    }
    provenance = {
        "schema_version": 1,
        "toolkit_version": __version__,
        "run_timestamp": run_timestamp,
        "status": status,
        "synthetic_only": True,
        "input_hashes": dict(sorted(hashes_before.items())),
        "output_hashes": output_hashes,
        "source_files_unchanged": source_unchanged,
        "dataset_count": len(views),
        "harmonized_rows": len(harmonized),
        "approved_mappings": sum(row["executable"] for row in mapping_rows),
        "blocked_mappings": [
            {
                "dataset_id": row["dataset_id"],
                "survey_id": row["survey_id"],
                "wave_id": row["wave_id"],
                "canonical_variable": row["canonical_variable"],
                "source_variable": row["source_variable"],
                "review_status": row["review_status"],
                "block_reason": row["block_reason"],
                "rule_version": row["rule_version"],
            }
            for row in blocked
        ],
        "validation_issue_counts": dict(
            sorted(Counter(row["severity"] for row in issues).items())
        ),
        "provenance_note": "The manifest omits its own hash to avoid recursive self-reference.",
    }
    write_json(output_dir / "provenance_manifest.json", provenance)
    return {
        "status": status,
        "output_dir": str(output_dir),
        "dataset_count": len(views),
        "harmonized_rows": len(harmonized),
        "approved_mappings": provenance["approved_mappings"],
        "blocked_mappings": len(blocked),
        "validation_errors": error_count,
        "validation_warnings": sum(row["severity"] == "warning" for row in issues),
        "source_files_unchanged": source_unchanged,
    }
