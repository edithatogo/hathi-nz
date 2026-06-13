# Specification: Zenodo Release Archival Automation (release_archival_20260613)

## 1. Overview
For academic credibility and open science compliance, the staged datasets must be archived on Zenodo, minting a persistent Digital Object Identifier (DOI) for each release. This track automates the packaging, metadata validation, and publication of the Hathi NZ corpus releases to Zenodo.

## 2. Zenodo Metadata
- **File:** `.zenodo.json`
- **Fields:** Title, descriptions, creators, license, version, keywords, communities.
- **Rules:** Must validate against Zenodo's metadata schema before submission.

## 3. Automation Pipeline
1. **Package Creation:** Compress raw data, processed text, and metadata catalogs into versioned ZIP files.
2. **Zenodo Upload:** Interact with Zenodo's REST API using deposition endpoints.
3. **Release & Publish:** Publish the deposition, fetching the resulting DOI and writing it back to the dataset card.
