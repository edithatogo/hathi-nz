# HathiTrust-NZ HTRC Extracted Features

HTRC Extracted Features 2.5 subset plans and fetched derived feature files for
HathiTrust-NZ volumes, with source-policy routing that keeps this as a
non-consumptive derived-data lane.

For academic citation, use the Zenodo DOI [10.5281/zenodo.21322329](https://doi.org/10.5281/zenodo.21322329).

## Access

HTRC Extracted Features 2.5 is a non-consumptive derived dataset distributed as
open JSON-LD under CC-BY-4.0. This dataset does not publish HathiTrust page
images or restricted full text.

Provenance records tie these outputs back to the HathiTrust collection export
and the interim source policy registry.

## Source

- HTRC Analytics
- HTRC Extracted Features 2.5 rsync module
  `data.analytics.hathitrust.org::features-2025.04/`

## Route Evidence

- Official HTRC source: extracted-features discovery and rsync allowlists.
- GitHub Actions route: small subsets can be fetched directly by workflow.
- Static-host route: larger subsets stage through the approved host when runner limits are exceeded.
- Blocked routes: restricted full text and non-derivative page-image publication.

## Publication Status

- Hugging Face repo: `edithatogo/hathitrust-nz-htrc-extracted-features`
- Zenodo stream: `hathitrust-nz-htrc-extracted-features`
