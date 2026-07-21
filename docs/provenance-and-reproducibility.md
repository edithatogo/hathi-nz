# HathiTrust-NZ Provenance And Reproducibility

This document is the publication-level provenance contract for the
HathiTrust-NZ collection. It describes what is sourced, transformed, derived,
published, and deliberately excluded. It applies to the GitHub repository,
Hugging Face datasets, Zenodo records, and OSF mirror packages.

## Collection Identity

- HathiTrust collection: `71329709`
- HathiTrust catalog record: `007119315`
- Curated seed: 510 volume records
- Hugging Face collection: `edithatogo/hathitrust-nz`
- Canonical code: <https://github.com/edithatogo/hathi-nz>
- Compatibility dataset: `edithatogo/corpus-nz-hathi`

The committed [archive registry](../manifests/hathitrust-nz/archive_registry.json)
is the machine-readable source of truth for child datasets, access classes,
publication endpoints, and DOI relationships.

## Dataset Lanes

| Dataset | Contents | Public route |
| --- | --- | --- |
| `hathitrust-nz-inventory` | HTIDs, catalog metadata, rights, routing, source evidence, and completeness reports | Hugging Face and Zenodo |
| `hathitrust-nz-research-fulltext` | Research Dataset eligibility manifests and interim IA overlap evidence | Metadata-only until redistribution eligibility is explicit |
| `hathitrust-nz-htrc-extracted-features` | HTRC EF 2.5 derived-feature subset and allowlists | Hugging Face and Zenodo |
| `hathitrust-nz-htrc-analytics` | Worksets, scripts, aggregates, and reproducibility metadata | Hugging Face and Zenodo |
| `corpus-nz-hathi` | Compatibility release with public full text only where confirmed | Hugging Face and Zenodo |

## Transformation Ledger

1. Source exports are retained as HathiTrust identifiers and collection
   metadata; no source record is silently discarded.
2. HTID, title, creator, year, volume, rights, access profile, and source
   fields are normalized into manifests.
3. Rights and source-policy classifiers route each record to public full text,
   public derived data, metadata-only, or manual review.
4. Internet Archive matches require title/creator evidence and are recorded in
   the overlap manifest, provenance ledger, and review queue.
5. HTRC features and analytics are derived/non-consumptive lanes; they do not
   authorize rehosting restricted source text.
6. Every generated release artifact is checksummed and associated with the
   Git commit and workflow run that produced it.

The pipeline does not perform unrecorded OCR replacement, text rewriting, or
semantic extraction in the archive publication step. OCR and downstream NLP
outputs must be published as separate derived artifacts with their own source
and transformation metadata.

## Exclusions And Fail-Closed Rules

- Restricted, Google-constrained, page-only, uncertain, or privacy-limited
  full text is never uploaded to public Hugging Face, Zenodo, or OSF targets.
- IA overlap is evidence/interim acquisition, not proof of HathiTrust
  redistribution rights.
- HTRC Data Capsule outputs are limited to scripts, aggregates, worksets, and
  reproducibility metadata unless broader rights are documented.
- Missing source evidence, checksum, or rights classification routes a record
  to metadata-only or manual review.

## Reproduction

From a pinned Git commit:

```bash
pixi install --locked
pixi run -e dev test
pixi run -e dev quality
pixi run -e dev python scripts/validate_archive_registry.py
pixi run -e dev publication-status
```

GitHub Actions is the execution environment for acquisition and publication.
The workflow run ID, commit SHA, generated manifests, validation reports, and
checksums must be retained with each release. Publication credentials are
never stored in the repository or release artifacts.

## Publication Relationships

The child dataset cards and Zenodo records are linked to this document, the
archive registry, the source collection, and the exact code repository. OSF
packages mirror the same manifests and checksums rather than creating an
independent, silently transformed dataset.
