#!/usr/bin/env bash
set -euo pipefail
: "${HATHI_RSYNC_MODULE:?Set approved Hathi rsync module on static host}"
: "${HATHI_STATIC_HOST_STAGING_DIR:?Set local staging dir on static host}"
mkdir -p "$HATHI_STATIC_HOST_STAGING_DIR/research_datasets"
# Use research_dataset_eligible_htids.txt as the allowlist for approved acquisition.
# Dataset-specific path mapping is supplied by the approved Hathi Research Dataset endpoint.
