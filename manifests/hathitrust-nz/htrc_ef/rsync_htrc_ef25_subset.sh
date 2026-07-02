#!/usr/bin/env bash
set -euo pipefail
DEST_DIR="${1:-htrc_ef25_subset}"
mkdir -p "$DEST_DIR"
rsync -av --files-from="htrc_ef25_files.txt" "data.analytics.hathitrust.org::features-2025.04/" "$DEST_DIR/"
