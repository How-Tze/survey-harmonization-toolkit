# Mapping rules

Every dataset/wave has exactly one rule for every canonical variable.

## Review status

| Status | Meaning | Executable |
| --- | --- | --- |
| `approved` | The source field and coding decision have been reviewed for this demo | Yes |
| `ambiguous` | A candidate exists, but meaning, unit, wording, or universe is not defensibly comparable | No |
| `unavailable` | No candidate variable is present for that wave | No |
| `unreviewed` | A candidate exists but has not passed human review | No |

Blocked rules must have `transform: null`. The loader also rejects missing-value, routing, or transform parameters on blocked rules, so a non-approved candidate cannot execute preprocessing indirectly.

## Fixed transforms

| Transform | Purpose | Required parameters |
| --- | --- | --- |
| `identity` | Preserve a reviewed value | none |
| `categorical_recode` | Map source codes/strings to canonical categories | `value_map` |
| `numeric_bin` | Map numeric intervals to ordered categories | `breaks`, `labels` |
| `scale_shift` | Add a constant to a numeric scale | `add` |
| `reverse_scale` | Reverse a bounded numeric scale | `source_min`, `source_max` |

There is no `derive` transform and no arbitrary expression evaluation.

## Missing preprocessing

For approved mappings, `missing_values` maps exact source codes to declared classes such as `not_stated`, `dont_know`, or `refused`. These values are counted and converted to missing before transformation. All other nonmissing values continue to source-range validation and the reviewed transform. System missing values are counted separately. When a routing rule declares an indicator and eligible values, a missing source response outside the eligible universe is counted as `structural_missing` rather than ordinary system missing.

The toolkit never infers routing solely from a missingness pattern.
