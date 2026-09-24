# Contributing

Thanks for helping make survey-data audits more transparent. Please keep contributions small, reviewable, and safe to publish. This repository contains only fictional, synthetic survey material; do not submit real respondent data, restricted codebooks or questions, credentials, personal identifiers, or private research mappings.

## Report a bug

Open an issue describing what happened, what you expected, the command and configuration involved, your Python version and operating system, and the smallest reproducible synthetic example. Include relevant error text, but remove local paths, secrets, and any non-public data before posting. A failing test is especially helpful.

## Request a feature

Open an issue explaining the research workflow it would support, the expected input and output, and why the current audit, mapping, or validation behavior is insufficient. Please discuss scope before building a large change. This project favors explicit, bounded rules over automatic semantic matching, expression engines, or new infrastructure.

## Propose a mapping-rule extension

Describe the source and target coding, missing-value conventions, applicable waves and respondent universe, routing, and any construct or unit ambiguity using a wholly synthetic example. Explain what a researcher must review before approving the rule. New behavior must preserve source values, keep review status separate from transformation type, execute only `approved` mappings, and leave `ambiguous`, `unavailable`, and `unreviewed` mappings blocked and visible in audit outputs. Include tests for valid, invalid, missing, and blocked cases. Coding agreement alone is not evidence of measurement equivalence.

## Propose a reader extension

First open an issue naming the file format and the metadata needed for an audit: variable names and types, value labels, declared missing codes, and any format-specific limitations. Use newly generated synthetic fixtures and test both metadata extraction and end-to-end behavior. A reader must not silently change source values or infer equivalence from shared variable names or numeric codes.

## Submit a change

1. Create a focused branch and make only the agreed change.
2. Install locally with `python -m pip install -e ".[dev]"` and run `python -m pytest`.
3. If behavior changes, update the relevant documentation and add synthetic tests.
4. Open a pull request explaining the user-visible change, evidence from tests, and any interpretation or publication-safety limitations.

Please do not include private survey material in issues, pull requests, fixtures, or generated output. Maintainers may decline changes that widen scope without improving auditability or scientific clarity.
