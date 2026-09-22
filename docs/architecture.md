# Architecture

```text
datasets.yaml + canonical_variables.yaml + mappings.yaml
                         │
                         ▼
              configuration validation
                         │
                         ▼
       source fingerprints + format-aware readers
                         │
                         ▼
 schema/value labels + coverage/missingness classification
                         │
                         ▼
             explicit mapping review gate
                         │
       approved ─────────┴──────── blocked and reported
           │
           ▼
 missing preprocessing + one fixed transformation
           │
           ▼
 harmonized long rows + structural/canonical validation
           │
           ▼
 CSV/JSON/Markdown evidence + provenance manifest
```

Source files are opened read-only. Their SHA-256 hashes are recorded before processing and checked again before the run completes. Readers return source values without applying display labels. Missing-value normalization occurs only after audit classification and only for approved mappings.

The mapping review gate is deliberately asymmetric: `approved` rules may execute; `ambiguous`, `unavailable`, and `unreviewed` rules may only appear in evidence outputs. A completed demo may therefore contain blocked mappings while still producing an approved harmonized file for the defensible subset.

The package does not infer semantic matches, download data, execute user expressions, estimate statistical models, or claim measurement equivalence.
