# HathiTrust-NZ Discovery Manifest

- This manifest documents the broader NZ source families that should be discovered beyond the Hansard seed.
- Public metadata and derived manifests are publication-safe; restricted full text remains static-host only.

## Families

### Parliamentary and legal serials

- Family ID: `parliamentary_and_legal`
- Status: `active_discovery`
- Public archive status: `mixed`
- Discovery inputs: HathiTrust collection exports, Hathifiles, HathiTrust Bibliographic API, HathiTrust OAI feed, HathiTrust catalog records, HathiTrust Research Center extracted features 2.0/2.5
- Acquisition modes: github_actions_inventory, github_actions_public_metadata_publish, github_actions_derived_features, static_host_rsync_for_restricted_research_datasets
- Public sources: Parliamentary Debates / Hansard, Gazettes, Statutes, Acts, and Ordinances
- Restricted sources: Records with page-only, suppressed, or Google-restricted access profiles

### Government and policy serials

- Family ID: `government_and_policy`
- Status: `active_discovery`
- Public archive status: `mixed`
- Discovery inputs: Hathifiles, HathiTrust public collections, HathiTrust Bibliographic API, HathiTrust OAI feed, Catalog record crosswalks, Internet Archive public-domain overlap where provenance is explicit
- Acquisition modes: github_actions_inventory, github_actions_public_metadata_publish, github_actions_incremental_metadata_sync, static_host_rsync_for_restricted_research_datasets
- Public sources: Departmental reports, Official statistics, Commission reports, Public works and education reports
- Restricted sources: Records with privacy-limited, suppressed, or Google-restricted profiles

### NZ scholarly and cultural serials

- Family ID: `scholarly_and_cultural`
- Status: `active_discovery`
- Public archive status: `mixed`
- Discovery inputs: Hathifiles, HathiTrust catalog records, Public collections, HathiTrust Bibliographic API, HathiTrust OAI feed, HathiTrust Research Center extracted features 2.0/2.5
- Acquisition modes: github_actions_inventory, github_actions_public_metadata_publish, github_actions_derived_features, static_host_rsync_for_restricted_research_datasets
- Public sources: Journal and proceedings material with public rights, Public-domain scholarly serials
- Restricted sources: Google-restricted or page-only serials

### Māori / Aotearoa materials

- Family ID: `maori_and_aotearoa`
- Status: `active_discovery`
- Public archive status: `mixed`
- Discovery inputs: Hathifiles, HathiTrust catalog records, HathiTrust Bibliographic API, HathiTrust OAI feed, HTRC Workset Builder and extracted features search, HathiTrust Research Center Extracted Features v.2.0
- Acquisition modes: github_actions_inventory, github_actions_public_metadata_publish, github_actions_derived_features, static_host_rsync_for_restricted_research_datasets
- Public sources: Public-domain dictionaries, histories, grammars, and missionary-era publications, Public-domain newspapers and pamphlets
- Restricted sources: Privacy-limited, suppressed, or otherwise non-rehostable records

