---
license: other
language:
- en
- nz
tags:
- new-zealand
- parliamentary-debates
- hansard
- hathitrust
- historical-texts
- legal-corpus
- parquet
pretty_name: NZ Parliamentary Debates (HathiTrust)
task_categories:
- text-generation
- text-classification
- token-classification
- question-answering
configs:
- config_name: debates
  data_dir: data/raw/debates
  data_files:
  - "**/*.txt"
  default: true
  features:
  - name: htid
    dtype: string
  - name: category
    dtype: string
  - name: year
    dtype: int64
  - name: volume
    dtype: string
  - name: title
    dtype: string
  - name: rights
    dtype: string
  - name: collection_id
    dtype: string
  - name: source
    dtype: string
- config_name: legislation
  data_dir: data/raw/legislation
  data_files:
  - "**/*.txt"
  default: false
  features:
  - name: htid
    dtype: string
  - name: category
    dtype: string
  - name: year
    dtype: int64
  - name: volume
    dtype: string
  - name: title
    dtype: string
  - name: rights
    dtype: string
  - name: collection_id
    dtype: string
  - name: source
    dtype: string
---

# corpus-nz-hathi: NZ Parliamentary Debates (1854–1990)

## Dataset Summary

This dataset contains **510 volumes** of **New Zealand Parliamentary Debates (Hansard)** spanning **1854 to 1990**, sourced from the [HathiTrust Digital Library](https://www.hathitrust.org/) Collection ID `71329709` (source institution `uc1` — University of California).

It is part of the NZ corpus-family under the `edithatogo` organization, designed for NLP research, legal analysis, historical text mining, and reproducible open science.

## Source Provenance

| Property | Value |
|----------|-------|
| **Collection** | NZ Parliamentary Debates (Hansard) |
| **HathiTrust Collection ID** | `71329709` |
| **Source institution** | `uc1` (University of California) |
| **Expected volumes** | 510 |
| **Date range** | 1854 – 1990 |
| **Primary content category** | `debates` |
| **Rights status** | Public domain (`pd`) for most volumes |

## Dataset Structure

### Configurations

| Config | Description |
|--------|-------------|
| `debates` | **Default.** Full corpus of 510 NZ Parliamentary Debates volumes (1854–1990). |
| `legislation` | Planned legislation subset for future HathiTrust-backed uploads under the same corpus namespace. |

### Data Fields

Each volume record in the manifest conforms to the [`manifests/schema.json`](https://github.com/edithatogo/hathi-nz/blob/main/manifests/schema.json) schema (JSON Schema Draft 2020-12):

| Field | Type | Description |
|-------|------|-------------|
| `htid` | `string` | HathiTrust volume ID (e.g. `uc1.b2889853`) — primary identifier |
| `category` | `string` | Content category (`debates`, `hansard`, `parliamentary-papers`, etc.) |
| `year` | `int\|null` | Publication year (1800–2100); null when indeterminate |
| `volume` | `string` | Volume number or identifier string (from enumcron) |
| `title` | `string` | Full bibliographic title |
| `rights` | `string` | Rights status code: `pd`, `ic-world`, `undetermined`, `suppressed` |
| `collection_id` | `string` | HathiTrust collection ID (`71329709`) |
| `source` | `string` | Source institution code (e.g. `uc1`) |
| `enumcron` | `string` | Raw enumeration/chronology string |
| `oclc_num` | `string` | OCLC control number |
| `isbn` | `string` | ISBN (if available) |
| `issn` | `string` | ISSN (if available) |
| `lccn` | `string` | Library of Congress Control Number |
| `sha256` | `string` | SHA-256 checksum of volume content |
| `size_bytes` | `int` | File size in bytes |
| `pipeline_version` | `string` | Pipeline version that produced the record |
| `record_schema_version` | `string` | `"1.0"` — schema version constant |
| `corpus_id` | `string` | `"corpus-nz-hathi"` — cross-corpus identifier |

## Collection Methodology

1. **Discovery**: Volumes are discovered by filtering HathiFile dumps (tab-delimited) for Collection ID `71329709`.
2. **Enumeration**: Each matching line is parsed into a structured volume record with year extraction from imprint/title.
3. **Metadata enrichment**: Optionally enriched via the HathiTrust Data API (`/volume/{htid}/json`).
4. **Download**: Volume content is downloaded from HathiTrust as raw text/zip files.
5. **Verification**: SHA-256 checksums verify file integrity.
6. **Staging**: Files are organized into `data/raw/` and `data/processed/` with Parquet metadata tables.
7. **Validation**: Automated validation against JSON Schema Draft 2020-12, consistency checks, and file integrity verification.
8. **Upload**: Validated files are pushed to Hugging Face Hub via `huggingface-hub`.

## Usage Examples

### Python (Hugging Face Datasets)

```python
from datasets import load_dataset

ds = load_dataset("edithatogo/corpus-nz-hathi", "debates", split="train", streaming=True)

# Preview first 5 volumes
for i, row in enumerate(ds.take(5)):
    print(f"[{row['year']}] {row['title']}")
```

### Polars (local Parquet files)

```python
import polars as pl

df = pl.read_parquet("data/processed/metadata/*.parquet")
print(df.head())
```

### DuckDB (direct HF query)

## Intended Use

- **Legal NLP research**: Training language models on historical parliamentary language
- **Historical text mining**: Analyzing political discourse across 136 years of New Zealand history
- **Digital humanities**: Studying legislative evolution, policy debates, and political trends
- **Open science**: Reproducible, versioned corpus with persistent identifiers

## Limitations

- **OCR quality**: Early volumes (1854–1900) may have lower OCR quality due to typeface and page condition.
- **Coverage**: The corpus covers 1854–1990. Post-1990 debates and supplementary parliamentary papers are not included.
- **Rights**: Some volumes may have undetermined or restricted rights status (`ic-world`, `undetermined`, `suppressed`).
- **Not legal advice**: This dataset is provided for research and informational purposes, not as legal advice.

## Update Cadence

- **Live HF dataset**: Updated daily or as new volumes are discovered/verified.
- **Zenodo snapshots**: Annual DOI-backed archival releases for academic citation.
- **OSF mirrors**: Release bundles mirrored to an OSF project for secondary redundancy.

## Release Mirrors

The OSF mirror reuses the same prepared release archives and manifest files as Zenodo. Publish steps read `.osf.json` for mirror-specific metadata and use `OSF_TOKEN` plus `OSF_PROJECT_ID` to upload into the configured OSF project.

### Zenodo Release Workflow

GitHub Actions publishes Zenodo releases from the same packaged archive that is
used for the OSF mirror. The `zenodo_release.yml` workflow runs on published
GitHub releases or manual `workflow_dispatch` events with a version input,
packages the archive, validates version consistency, uploads to Zenodo, and
updates the citation line in this dataset card with the DOI.

Use the `production` input only when you want the workflow to switch away from
the sandbox Zenodo API. The workflow expects `ZENODO_TOKEN` to be available as a
repository secret.

## Citation

```bibtex
@misc{togo2026corpusnzhathi,
  author = {Edith A. Togo},
  title = {corpus-nz-hathi: NZ Parliamentary Debates (1854--1990) from HathiTrust},
  year = {2026},
  publisher = {Hugging Face},
  howpublished = {\url{https://huggingface.co/edithatogo/corpus-nz-hathi}}
}
```

For live use, cite the Hugging Face repository with access date. For academic citation, use the Zenodo DOI _(once available)_.

## Licensing

- **Pipeline code**: Licensed separately in the source GitHub repository.
- **Source material**: NZ Parliamentary Debates text is Crown copyright. This dataset card does not relicense the source material. Users should verify HathiTrust rights status for each volume before redistribution.
- **Metadata**: Project-created metadata (schemas, manifests, dataset cards) shared under CC-BY-4.0.
- **This dataset is not legal advice.**

## Contact

- **Hugging Face**: [edithatogo/corpus-nz-hathi](https://huggingface.co/edithatogo/corpus-nz-hathi)
- **GitHub**: [edithatogo/hathi-nz](https://github.com/edithatogo/hathi-nz)
- **Organization**: [edithatogo](https://huggingface.co/edithatogo)


```sql
SELECT htid, year, title, volume
FROM read_parquet('hf://datasets/edithatogo/corpus-nz-hathi/metadata/*.parquet')
WHERE year BETWEEN 1890 AND 1900
ORDER BY year, volume
LIMIT 10;
```

### PyArrow

```python
import pyarrow.dataset as ds

dataset = ds.dataset("hf://datasets/edithatogo/corpus-nz-hathi", format="parquet")
table = dataset.to_table(columns=["htid", "year", "title", "volume"])
print(table.to_pandas().head())
```


### Data Splits

The dataset is not pre-split. Use `streaming=True` and filter by `year` or `htid` for custom splits.


All volumes are enumerated from HathiFile dumps, with metadata enriched via the HathiTrust Data API. Each volume record includes provenance fields: `source`, `collection_id`, `sha256` checksum, and `pipeline_version`.

## Languages

- **English** (`en`): Primary language of the debates.
- **New Zealand English** (`nz`): Includes New Zealand-specific terminology, place names, and Māori loanwords.
- **Māori** (selected terms): Occasional use of te reo Māori in parliamentary speeches.
