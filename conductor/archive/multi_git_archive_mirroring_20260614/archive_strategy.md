# Multi-Archive Mirroring Strategy

## Scope

This note records the local, non-gated strategy for redundant publication of the
`hathi-nz` code and dataset artifacts. It does not configure external accounts,
secrets, remotes, Zenodo depositions, OSF projects, or browser profiles.

## Publication Targets

| Target | Role | Cadence | Local source | Gate |
|--------|------|---------|--------------|------|
| GitHub | Canonical code repository | On push | Repository working tree | None for local workflow file |
| GitLab or Codeberg | Secondary Git mirror | On push | `.github/workflows/mirror_sync.yml` | GitHub secrets and trigger verification |
| Hugging Face Hub | Live dataset publication | Daily/manual | `data/processed`, `manifests`, `DATASET_CARD.md` | HF token and upload |
| Zenodo | DOI-backed archival snapshot | Annual/manual release | Release package, `.zenodo.json` | Zenodo token and publication approval |
| OSF | Optional review or backup package | Annual or release-driven | Same release package as Zenodo | OSF project/API approval |

## Zenodo Snapshot Requirements

Zenodo snapshots should be built from the same validated local artifacts used for
Hugging Face publication:

- `manifests/latest_manifest.json`
- `manifests/schema.json`
- `DATASET_CARD.md`
- `.zenodo.json`
- staged metadata from `data/processed`
- raw or processed volume payloads included according to rights status
- a generated release manifest listing file paths, sizes, and SHA-256 checksums

Before any upload, the local package should pass these checks:

- `.zenodo.json` contains title, creators, access right, upload type, license,
  related identifiers, version, and source references.
- every packaged payload has a SHA-256 checksum in the release manifest.
- the manifest record count matches `manifests/latest_manifest.json`.
- restricted or undetermined-rights volumes are either excluded or explicitly
  documented in the release manifest.
- the package can be recreated from local scripts without manual file selection.

Publication to Zenodo is gated because it creates or mutates an external
deposition and may reserve or publish a DOI.

## OSF Optional Mirror Policy

OSF is optional and should not be treated as the live dataset source of truth.
Use it only when one of these conditions applies:

- a review process needs a stable bundle outside Hugging Face and Zenodo;
- a funder, collaborator, or institutional workflow requests OSF storage;
- the corpus family adopts OSF as a standard backup target across sibling repos.

The OSF package should reuse the Zenodo release package rather than introducing
a divergent structure. OSF metadata should point back to GitHub, Hugging Face,
and the Zenodo DOI when available. OSF upload, project creation, token use, or
browser-profile work remains gated.

## Current Local Evidence

- `.github/workflows/mirror_sync.yml` exists and skips safely when
  `GIT_MIRROR_URL` is unset.
- `.zenodo.json` exists with dataset metadata, related identifiers, version, and
  HathiTrust references.
- `DATASET_CARD.md` identifies Hugging Face as the live dataset and Zenodo as
  the annual archival snapshot target.

