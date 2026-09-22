# Survey Harmonization Toolkit

Survey files rarely agree on names, codes, missing values, routing, or scale direction. This toolkit helps behavioral and social-science researchers audit those differences, record explicit review decisions, and produce a traceable harmonized dataset without treating resemblance as evidence of equivalence.

> **Synthetic demonstration only.** Every survey, respondent, variable label, codebook, mapping, and output in this repository was created from scratch for this project.

## Why a rename is not enough

Suppose two files both encode gender with numbers:

| File | Variable | Code `1` | Code `2` |
| --- | --- | --- | --- |
| CivicLife 2018 | `sex` | man | woman |
| Household Paths 2019 | `sex_code` | woman | man |

Renaming both columns to `gender` preserves the numbers and reverses their meaning in one source. The same danger appears with special missing codes, routed questions, changed scale direction, and variables whose wording changes while their name stays stable.

This toolkit audits those differences before it transforms data. Explicit, reviewed rules correctly recode the defensible cases. Mappings marked `ambiguous`, `unavailable`, or `unreviewed` are reported and never executed. In the included demo, a changed institutional-trust item and a personal-monthly-versus-household-annual income candidate remain deliberately blocked.

```text
heterogeneous survey files
        ↓
metadata / schema / missingness audit
        ↓
explicit researcher-reviewed mappings
        ↓
approved fixed transformations
        ↓
harmonized output + validation + provenance
```

Principled refusal is part of the output:

| Canonical variable | Source/wave | Review status | Action |
| --- | --- | --- | --- |
| Institutional trust | CivicLife 2022 | `ambiguous` | blocked |
| Community participation | Household Paths 2019 | `unavailable` | blocked |
| Work autonomy | Values and Work 2018 | `unreviewed` | blocked |
| Household income | Values and Work 2021 | `ambiguous` | blocked |

## What v0.1 does

The command-line pipeline:

1. validates a YAML dataset registry, canonical-variable definitions, and mapping rules;
2. fingerprints declared synthetic source files;
3. reads CSV, SPSS `.sav`, and Stata `.dta` schemas and value labels;
4. audits coverage, declared special missing values, system missingness, and configured routing;
5. compiles an explicit mapping-review matrix;
6. applies only approved fixed transformations;
7. writes `harmonized_long.csv` with blocked mappings left empty for their affected dataset/waves;
8. validates IDs, categories, ranges, row accounting, and source immutability;
9. produces deterministic audit and provenance artifacts for a fixed run timestamp.

Supported mapping statuses:

- `approved`
- `ambiguous`
- `unavailable`
- `unreviewed`

Supported transforms:

- `identity`
- `categorical_recode`
- `numeric_bin`
- `scale_shift`
- `reverse_scale`

Missing-value normalization is a separate declared preprocessing rule. There is no arbitrary expression or generic derive mechanism.

## Synthetic demo

The repository contains seven small generated waves from three fictional programs:

- CivicLife Survey: 2018, 2020, 2022 (`.sav`)
- Household Paths Study: 2019, 2021 (`.dta`)
- Values and Work Monitor: 2018, 2021 (`.csv` plus YAML codebooks)

The files include deliberately different names, categorical encodings, missing codes, scale endpoints, scale direction, routing patterns, wave availability, and review status. See [the synthetic design](docs/synthetic_demo_design.md).

## Quick start

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python scripts/generate_synthetic_data.py
python -m survey_harmonization run --config-dir config --output-dir output/demo --run-timestamp 2026-09-22T00:00:00Z
pytest
```

The generated source fixtures are already included, so the generation step is optional for an ordinary demo run. It is provided to make their synthetic provenance reproducible.

Use `--strict` when deliberately blocked mappings should result in exit code 2 after diagnostic outputs are written. Validation errors return exit code 1. A normal demo run with reviewed blocks returns exit code 0 and status `completed_with_blocked_mappings`.

## Generated outputs

The example run writes:

- `inventory.json`
- `schema_catalog.csv`
- `value_labels.json`
- `coverage_matrix.csv`
- `missingness_audit.csv`
- `mapping_review.csv`
- `harmonized_long.csv`
- `validation_issues.csv`
- `provenance_manifest.json`
- `audit_report.md`

The deterministic, reviewed example outputs are retained in `examples/demo_output/`. Ordinary runtime outputs belong under ignored `output/` paths, so running the quick start does not overwrite the reviewed examples.

## Configuration

- `config/datasets.yaml` declares files, waves, IDs, weights, and routing context.
- `config/canonical_variables.yaml` defines canonical types, ranges, and categories.
- `config/mappings.yaml` records one reviewed decision for every dataset/wave × canonical-variable pair.

Rules are declarative and bounded. Unknown transforms, absolute data paths, incomplete mapping grids, and executable blocked rules are rejected.

## Research interpretation boundary

**Coding harmonization does not establish construct equivalence, measurement invariance, or the validity of pooled analysis.** The toolkit reports coding and structural compatibility; scientific equivalence remains a researcher judgment. See [interpretation boundaries](docs/interpretation_boundaries.md).

## Tests

Run the complete suite with:

```powershell
pytest
```

The test suite covers configuration gates, all five transforms, metadata readers, missingness/routing classification, blocked mappings, structural validation, deterministic end-to-end outputs, source immutability, and publication-safety checks.

The package separates configuration, readers, audit/classification, fixed transforms, validation, reporting, and orchestration. See [architecture](docs/architecture.md) and [mapping rules](docs/mapping_rules.md).

## Publication boundary

This project works without access to any private research workspace. It contains no real survey data, questions, labels, institutions, URLs, mappings, hypotheses, participant records, credentials, or local-machine paths. Do not replace the synthetic fixtures in a public fork with restricted data.

## License

MIT. The license applies to the newly created code, synthetic fixtures, documentation, and generated demonstration outputs in this project.
