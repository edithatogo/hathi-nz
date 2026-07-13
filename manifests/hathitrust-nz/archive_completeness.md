# HathiTrust-NZ Archive Completeness Report

- Source collection: HathiTrust Collection `71329709`.
- HF collection: `edithatogo/hathitrust-nz`.
- Publication map: [`archive_registry.json`](./archive_registry.json).
- Seed record count: `510`.
- Parsed numeric volume labels: `369`.
- Parsed enumeration labels: `510`.
- Fully parsed seed labels: `510`.
- Needs enumeration enrichment: `0`.
- Public full-text uploads fail closed when rights, source, or access profile is ambiguous.
- Internet Archive public-domain overlap is the interim full-text path while HathiTrust rsync remains unavailable.
- Hathi Research Dataset full text must be staged via the approved static rsync host once access is restored.
- HTRC Extracted Features 2.5 subset acquisition uses rsync file allowlists.

## Child Datasets

- `corpus-nz-hathi` -> `edithatogo/corpus-nz-hathi`
- `hathitrust-nz-inventory` -> `edithatogo/hathitrust-nz-inventory`
- `hathitrust-nz-research-fulltext` -> `edithatogo/hathitrust-nz-research-fulltext`
- `hathitrust-nz-htrc-extracted-features` -> `edithatogo/hathitrust-nz-htrc-extracted-features`
- `hathitrust-nz-htrc-analytics` -> `edithatogo/hathitrust-nz-htrc-analytics`

The registry records the verified Hugging Face and Zenodo endpoints, access
class, DOI, release version, and content status for every child. Publication
health is scored separately from content completeness: the public endpoints
are healthy, while Research Dataset full text remains metadata-only until the
official HathiTrust static-host route is approved.
