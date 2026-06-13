# Specification: Dataset Mapping & Hugging Face Config Planning (config_mapping_20260613)

## 1. Overview
As the legal-nz corpus expands on Hugging Face, dataset sprawl must be mitigated. This track designs the naming conventions and structure for all HathiTrust datasets under the `edithatogo` namespace, prioritizing a unified multi-configuration (subset) approach.

## 2. Naming Standards
- **Repository Name:** `edithatogo/corpus-nz-hathi`
- **Configurations (Subsets):** Instead of publishing dozens of distinct datasets, use Hugging Face's multi-configuration feature. Loading configurations:
  - `load_dataset("edithatogo/corpus-nz-hathi", "debates")`
  - `load_dataset("edithatogo/corpus-nz-hathi", "legislation")`
- **Volume Naming Structure:** Files grouped by category and year inside the repository layout:
  ```
  data/raw/debates/year=YYYY/volume_num/
  ```

## 3. Metadata Schema
Every volume is mapped to a standardized sidecar json mapping:
```json
{
  "htid": "uc1.b2889853",
  "category": "debates",
  "year": 1854,
  "volume": "1",
  "title": "Parliamentary Debates",
  "oclc_num": "1234567",
  "rights": "pd"
}
```
This enables DuckDB and Polars to easily execute partitioned queries over the database index.
