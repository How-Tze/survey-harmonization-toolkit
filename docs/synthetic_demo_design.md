# Synthetic demo design

All names and records are fictional.

| Program | Waves | Format | Main differences |
| --- | --- | --- | --- |
| CivicLife Survey | 2018, 2020, 2022 | SPSS | renamed fields, label-set changes, 0–4 versus 1–5 scales, reversed scale, changed trust wording |
| Household Paths Study | 2019, 2021 | Stata | reversed gender codes, education years versus credentials, renamed IDs, changed scale direction |
| Values and Work Monitor | 2018, 2021 | CSV + YAML codebooks | text/numeric category changes, routed work item, unreviewed candidate, incomparable income unit |

Each wave contains 24 deterministic synthetic rows. Employment determines eligibility for the work-autonomy item. Source-specific special missing codes occur only in declared positions. No row represents a real person.

Deliberately blocked examples include:

- CivicLife 2022 `trust_index`: the label describes satisfaction with local services rather than institutional trust (`ambiguous`).
- Values and Work Monitor 2018 `decision_control`: candidate work-autonomy field awaiting review (`unreviewed`).
- Values and Work Monitor 2021 `monthly_personal_earnings`: a personal monthly amount cannot silently replace annual household income (`ambiguous`).
- Household Paths 2019 community participation: source variable unavailable (`unavailable`).

The main demo has no duplicate IDs or undeclared invalid codes, allowing the approved subset to be emitted. Separate tests introduce duplicate IDs and unexpected source values to verify failure behavior without making the reviewed example output intentionally invalid.
