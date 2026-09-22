from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any


OUTPUT_DESCRIPTIONS = {
    "inventory.json": "File fingerprints and declared source identities",
    "schema_catalog.csv": "Normalized variable metadata across formats",
    "value_labels.json": "Source value labels without applying them to data",
    "coverage_matrix.csv": "Coverage and mapping status by dataset/wave and canonical variable",
    "missingness_audit.csv": "Declared, system, structural, and unexpected missingness counts",
    "mapping_review.csv": "Executable and blocked mapping decisions",
    "harmonized_long.csv": "Approved canonical variables in long multi-source form",
    "validation_issues.csv": "Stable validation warnings and errors",
    "provenance_manifest.json": "Input/config/output hashes and run status",
    "audit_report.md": "Researcher-readable audit summary",
}


def build_report(
    *,
    run_timestamp: str,
    status: str,
    dataset_count: int,
    row_count: int,
    mapping_rows: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    missing_rows: list[dict[str, Any]],
) -> str:
    blocked = [row for row in mapping_rows if not row["executable"]]
    transforms = Counter(
        row["transform"] for row in mapping_rows if row["executable"]
    )
    issue_counts = Counter(row["severity"] for row in issues)
    missing_counts = Counter()
    for row in missing_rows:
        missing_counts[row["missing_class"]] += int(row["count"])
    lines = [
        "# Synthetic survey harmonization audit",
        "",
        "> All inputs and outputs in this demonstration are fictional and synthetic.",
        "",
        "## Run summary",
        "",
        f"- Status: `{status}`",
        f"- Run timestamp: `{run_timestamp}`",
        f"- Dataset/wave files: {dataset_count}",
        f"- Harmonized rows: {row_count}",
        f"- Approved mappings: {sum(1 for row in mapping_rows if row['executable'])}",
        f"- Blocked mappings: {len(blocked)}",
        f"- Validation errors: {issue_counts.get('error', 0)}",
        f"- Validation warnings: {issue_counts.get('warning', 0)}",
        "",
        "## Applied transforms",
        "",
        "| Transform | Mappings |",
        "| --- | ---: |",
    ]
    for transform, count in sorted(transforms.items()):
        lines.append(f"| `{transform}` | {count} |")
    lines.extend(
        [
            "",
            "## Blocked mappings",
            "",
            "| Dataset | Canonical variable | Status | Candidate source | Reason |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in blocked:
        reason = str(row["block_reason"]).replace("|", "\\|")
        lines.append(
            f"| `{row['dataset_id']}` | `{row['canonical_variable']}` | "
            f"`{row['review_status']}` | `{row['source_variable']}` | {reason} |"
        )
    lines.extend(
        [
            "",
            "## Coverage notes",
            "",
            f"The matrix contains {len(coverage_rows)} dataset/wave × canonical-variable decisions. "
            "Rows marked blocked remain empty in `harmonized_long.csv` for the affected dataset/wave.",
            "",
            "## Missingness summary",
            "",
            "| Classification | Count | Meaning |",
            "| --- | ---: | --- |",
        ]
    )
    missing_descriptions = {
        "dont_know": "Declared source code for don't know",
        "not_stated": "Declared source code for not stated",
        "refused": "Declared source code for refusal",
        "structural_missing": "System-missing response outside a declared routing universe",
        "system_missing": "System-missing response not classified as structural",
        "unexpected_source_value": "Nonmissing value outside the reviewed source definition",
    }
    for classification in sorted(missing_counts):
        lines.append(
            f"| `{classification}` | {missing_counts[classification]} | "
            f"{missing_descriptions.get(classification, 'Declared missing class')} |"
        )
    lines.extend(
        [
            "",
            "Only exact declared codes are normalized. Routing classifications use explicit indicators; they are not inferred from missingness alone.",
            "",
            "## Validation",
            "",
        ]
    )
    if issues:
        lines.extend(
            [
                "| Severity | Code | Dataset | Wave | Variable | Rule | Count | Message |",
                "| --- | --- | --- | --- | --- | ---: | ---: | --- |",
            ]
        )
        for row in issues:
            message = str(row["message"]).replace("|", "\\|")
            lines.append(
                f"| {row['severity']} | `{row['code']}` | `{row['dataset_id']}` | "
                f"`{row['wave_id']}` | `{row['canonical_variable']}` | "
                f"{row['rule_version']} | {row['count']} | {message} |"
            )
    else:
        lines.append("No validation issues were emitted.")
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "Successful coding harmonization does not establish construct validity, measurement invariance, comparable sampling universes, or a justified pooled estimand. Blocked mappings document where transformation was not defensible.",
            "",
            "## Artifacts",
            "",
            "| File | Purpose |",
            "| --- | --- |",
        ]
    )
    for name, description in OUTPUT_DESCRIPTIONS.items():
        lines.append(f"| `{name}` | {description} |")
    return "\n".join(lines) + "\n"
