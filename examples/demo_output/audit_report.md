# Synthetic survey harmonization audit

> All inputs and outputs in this demonstration are fictional and synthetic.

## Run summary

- Status: `completed_with_blocked_mappings`
- Run timestamp: `2026-09-22T00:00:00Z`
- Dataset/wave files: 7
- Harmonized rows: 168
- Approved mappings: 65
- Blocked mappings: 5
- Validation errors: 0
- Validation warnings: 5

## Applied transforms

| Transform | Mappings |
| --- | ---: |
| `categorical_recode` | 32 |
| `identity` | 28 |
| `numeric_bin` | 1 |
| `reverse_scale` | 2 |
| `scale_shift` | 2 |

## Blocked mappings

| Dataset | Canonical variable | Status | Candidate source | Reason |
| --- | --- | --- | --- | --- |
| `civiclife_2022` | `institutional_trust` | `ambiguous` | `trust_index` | The 2022 label describes satisfaction with local services rather than trust. |
| `household_paths_2019` | `community_participation` | `unavailable` | `` | No community participation field was generated for this wave. |
| `values_work_2018` | `work_autonomy` | `unreviewed` | `decision_control` | Candidate item intentionally awaits human review. |
| `values_work_2021` | `household_income` | `ambiguous` | `monthly_personal_earnings` | Personal monthly earnings cannot replace annual household income without additional evidence. |
| `values_work_2021` | `survey_weight` | `unavailable` | `` | This synthetic wave intentionally contains no survey weight. |

## Coverage notes

The matrix contains 70 dataset/wave × canonical-variable decisions. Rows marked blocked remain empty in `harmonized_long.csv` for the affected dataset/wave.

## Missingness summary

| Classification | Count | Meaning |
| --- | ---: | --- |
| `dont_know` | 5 | Declared source code for don't know |
| `not_stated` | 11 | Declared source code for not stated |
| `refused` | 2 | Declared source code for refusal |
| `structural_missing` | 48 | System-missing response outside a declared routing universe |
| `system_missing` | 0 | System-missing response not classified as structural |
| `unexpected_source_value` | 0 | Nonmissing value outside the reviewed source definition |

Only exact declared codes are normalized. Routing classifications use explicit indicators; they are not inferred from missingness alone.

## Validation

| Severity | Code | Dataset | Wave | Variable | Rule | Count | Message |
| --- | --- | --- | --- | --- | ---: | ---: | --- |
| warning | `mapping_blocked` | `civiclife_2022` | `2022` | `institutional_trust` | 1 | 1 | The 2022 label describes satisfaction with local services rather than trust. |
| warning | `mapping_blocked` | `household_paths_2019` | `2019` | `community_participation` | 1 | 1 | No community participation field was generated for this wave. |
| warning | `mapping_blocked` | `values_work_2018` | `2018` | `work_autonomy` | 1 | 1 | Candidate item intentionally awaits human review. |
| warning | `mapping_blocked` | `values_work_2021` | `2021` | `household_income` | 1 | 1 | Personal monthly earnings cannot replace annual household income without additional evidence. |
| warning | `mapping_blocked` | `values_work_2021` | `2021` | `survey_weight` | 1 | 1 | This synthetic wave intentionally contains no survey weight. |

## Interpretation boundary

Successful coding harmonization does not establish construct validity, measurement invariance, comparable sampling universes, or a justified pooled estimand. Blocked mappings document where transformation was not defensible.

## Artifacts

| File | Purpose |
| --- | --- |
| `inventory.json` | File fingerprints and declared source identities |
| `schema_catalog.csv` | Normalized variable metadata across formats |
| `value_labels.json` | Source value labels without applying them to data |
| `coverage_matrix.csv` | Coverage and mapping status by dataset/wave and canonical variable |
| `missingness_audit.csv` | Declared, system, structural, and unexpected missingness counts |
| `mapping_review.csv` | Executable and blocked mapping decisions |
| `harmonized_long.csv` | Approved canonical variables in long multi-source form |
| `validation_issues.csv` | Stable validation warnings and errors |
| `provenance_manifest.json` | Input/config/output hashes and run status |
| `audit_report.md` | Researcher-readable audit summary |
