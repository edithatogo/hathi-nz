# Historical Coverage Bridge

This repository publishes an evidence-only bridge for the curated HathiTrust
collection `71329709`. It is intended for consumption by `corpus-nz-hansard`
as historical discovery and gap-detection evidence.

The bridge does not claim complete historical New Zealand Hansard coverage.
The 510 records are a collection seed, and full-text archive state remains
metadata-only until source and redistribution evidence permit publication.
NZ legislation and Gazette materials remain outside this bridge.

The machine-readable output is generated and validated by
`scripts/build_historical_coverage_bridge.py` against
`schemas/historical_coverage_bridge.schema.json`.
