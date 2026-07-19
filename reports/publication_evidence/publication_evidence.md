# HathiTrust-NZ Publication Evidence

- This bundle records route evidence for the collection child datasets.
- It distinguishes official HathiTrust, IA interim, HTRC EF, analytics-only, metadata-only, and blocked routes.

## hathitrust-nz-inventory

- HF repo: `edithatogo/hathitrust-nz-inventory`
- Zenodo stream: `hathitrust-nz-inventory`
- Publication state: `metadata_only`
- Route evidence: Official HathiTrust collection export and rights metadata, HathiTrust source-policy registry snapshot, Internet Archive interim overlap evidence and checksums, Metadata-only publication route
- Blocked routes: restricted full text, Google/page-only full text

## hathitrust-nz-research-fulltext

- HF repo: `edithatogo/hathitrust-nz-research-fulltext`
- Zenodo stream: `hathitrust-nz-research-fulltext`
- Publication state: `metadata_only_until_static_host_bundle_is_eligible`
- Route evidence: HathiTrust Research Dataset static-host acquisition plan, Official HathiTrust rsync staging contract, Internet Archive overlap evidence as an interim source only, Metadata-only publication until the approved bundle is available
- Blocked routes: restricted research full text without explicit approval, Google-restricted or page-only full text

## hathitrust-nz-htrc-extracted-features

- HF repo: `edithatogo/hathitrust-nz-htrc-extracted-features`
- Zenodo stream: `hathitrust-nz-htrc-extracted-features`
- Publication state: `public_derived_features`
- Route evidence: HTRC Solr EF20 discovery candidates, HTRC Extracted Features 2.5 rsync allowlist, GitHub Actions routing for small subsets, Static-host staging for larger subsets
- Blocked routes: restricted full text, non-derivative page images

## hathitrust-nz-htrc-analytics

- HF repo: `edithatogo/hathitrust-nz-htrc-analytics`
- Zenodo stream: `hathitrust-nz-htrc-analytics`
- Publication state: `public_scripts_aggregates_and_reproducibility_metadata`
- Route evidence: HTRC Analytics workset definitions, Aggregate outputs and reproducibility metadata only, Non-consumptive analysis lane, Metadata-only and blocked full-text routes stay excluded
- Blocked routes: restricted full text, Data Capsule-only source material

## corpus-nz-hathi

- HF repo: `edithatogo/corpus-nz-hathi`
- Zenodo stream: `corpus-nz-hathi`
- Publication state: `public_full_text_where_confirmed`
- Route evidence: Compatibility dataset retained for the existing public full-text corpus, Existing Zenodo DOI-backed release stream, HF collection compatibility mirror
- Blocked routes: restricted HathiTrust research full text

