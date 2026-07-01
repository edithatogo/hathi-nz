"""Validate the volume catalog manifest and staged dataset integrity.

Responsibility:
  - Validate the manifest JSON against manifests/schema.json (JSON Schema)
  - Check manifest internal consistency (no duplicate htid, numeric year range)
  - Validate staged volume file integrity (SHA-256, size_bytes)
  - Produce a validation report at data/_state/validation_report.json
  - Return non-zero exit code on blocking failures

This script is the quality gate before any upload to HF Hub.

Usage:
  python scripts/validate_catalog.py --manifest manifests/latest_manifest.json
  python scripts/validate_catalog.py --stage-dir data/processed
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import jsonschema
from loguru import logger

from scripts.logging_utils import configure_logging

# ---------------------------------------------------------------
# Constants
# ---------------------------------------------------------------

SCHEMA_PATH = Path("manifests/schema.json")

REQUIRED_FIELDS = frozenset(
    {
        "htid",
        "category",
        "year",
        "volume",
        "title",
        "rights",
        "collection_id",
        "source",
    }
)

ALLOWED_RIGHTS = frozenset({"pd", "ic-world", "undetermined", "suppressed"})


# ---------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------


def validate_manifest_schema(
    manifest: dict[str, Any],
    schema_path: Path = SCHEMA_PATH,
) -> list[str]:
    """Validate the manifest structure against the JSON Schema.

    Args:
        manifest: The manifest dict (with 'meta' and 'volumes' keys).
        schema_path: Path to the JSON Schema file.

    Returns:
        List of validation error strings. Empty list = valid.

    """
    errors: list[str] = []

    try:
        with schema_path.open(encoding="utf-8") as f:
            schema = json.load(f)
    except FileNotFoundError:
        errors.append(f"Schema file not found: {schema_path}")
        return errors
    except json.JSONDecodeError as exc:
        errors.append(f"Schema file is not valid JSON: {exc}")
        return errors

    volumes = manifest.get("volumes", [])
    if not isinstance(volumes, list):
        errors.append("Manifest 'volumes' must be a list")
        return errors

    # Validate meta structure
    meta = manifest.get("meta")
    if not isinstance(meta, dict):
        errors.append("Manifest 'meta' must be a dict")
    else:
        for key in ("generated_at", "source", "version", "record_count", "schema"):
            if key not in meta:
                errors.append(f"Manifest 'meta' is missing required key: '{key}'")

    validator = jsonschema.Draft202012Validator(schema)

    for i, volume in enumerate(volumes):
        if not isinstance(volume, dict):
            errors.append(f"volumes[{i}] is not a dict")
            continue
        vs_errors = list(validator.iter_errors(volume))
        for ve in vs_errors:
            path = ".".join(str(p) for p in ve.absolute_path) if ve.absolute_path else "(root)"
            errors.append(f"volumes[{i}].{path}: {ve.message}")

    return errors


def check_manifest_consistency(volumes: list[dict[str, Any]]) -> list[str]:
    """Check manifest internal consistency.

    Checks:
      - No duplicate htid values
      - All required fields present (per schema)
      - Year within 1800-2100 range (if not None)
      - rights is one of the allowed values
      - source is a non-empty string

    Args:
        volumes: List of volume record dicts.

    Returns:
        List of error strings. Empty list = consistent.

    """
    errors: list[str] = []
    seen_htids: set[str] = set()

    for i, vol in enumerate(volumes):
        prefix = f"volumes[{i}]"

        if not isinstance(vol, dict):
            errors.append(f"{prefix} is not a dict")
            continue

        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in vol:
                errors.append(f"{prefix} missing required field '{field}'")

        # Check duplicate htid
        htid = vol.get("htid")
        if htid is not None:
            if not isinstance(htid, str):
                errors.append(f"{prefix}.htid must be a string, got {type(htid).__name__}")
            elif htid in seen_htids:
                errors.append(f"{prefix}.htid duplicate: '{htid}'")
            else:
                seen_htids.add(htid)

        # Check year range
        year = vol.get("year")
        if year is not None:
            if not isinstance(year, int):
                errors.append(
                    f"{prefix}.year must be an integer or null, got {type(year).__name__}"
                )
            elif year < 1800 or year > 2100:
                errors.append(f"{prefix}.year out of range: {year} (expected 1800-2100)")

        # Check rights
        rights = vol.get("rights")
        if rights is not None and rights not in ALLOWED_RIGHTS:
            errors.append(
                f"{prefix}.rights invalid: '{rights}' "
                f"(allowed: {', '.join(sorted(ALLOWED_RIGHTS))})"
            )

        # Check source is non-empty string
        source = vol.get("source")
        if source is not None and not isinstance(source, str):
            errors.append(f"{prefix}.source must be a string, got {type(source).__name__}")
        elif source is not None and not source.strip():
            errors.append(f"{prefix}.source is empty")

    return errors


def verify_staged_files(
    stage_dir: Path,
    volumes: list[dict[str, Any]],
) -> tuple[int, list[str], list[str]]:
    """Verify staged volume file integrity against manifest.

    Args:
        stage_dir: Directory with staged volume content.
        volumes: List of volume record dicts (must have htid, sha256, size_bytes).

    Returns:
        Tuple of (files_checked, errors, warnings).

    """
    errors: list[str] = []
    warnings: list[str] = []
    files_checked = 0

    for i, vol in enumerate(volumes):
        htid = vol.get("htid")
        if not htid:
            warnings.append(f"volumes[{i}] has no htid, skipping file check")
            continue

        source = vol.get("source", "unknown")
        expected_path = stage_dir / source / f"{htid}.zip"
        alt_path = stage_dir / f"{htid}.zip"

        file_path: Path | None = None
        if expected_path.exists():
            file_path = expected_path
        elif alt_path.exists():
            file_path = alt_path

        if file_path is None:
            errors.append(f"File not found for htid='{htid}' (tried: {expected_path}, {alt_path})")
            continue

        # Verify SHA256
        expected_sha256 = vol.get("sha256")
        if expected_sha256 is not None:
            try:
                actual_sha256 = _compute_sha256(file_path)
                if actual_sha256 is None:
                    errors.append(f"Cannot compute SHA256 for '{htid}' at {file_path}")
                elif actual_sha256 != expected_sha256:
                    errors.append(
                        f"SHA256 mismatch for '{htid}': "
                        f"expected {expected_sha256}, got {actual_sha256}"
                    )
            except OSError as exc:
                errors.append(f"Error reading {file_path} for '{htid}': {exc}")
        else:
            warnings.append(f"No sha256 in manifest for '{htid}', skipping checksum verification")

        # Verify file size
        expected_size = vol.get("size_bytes")
        if expected_size is not None:
            try:
                actual_size = file_path.stat().st_size
                if actual_size != expected_size:
                    errors.append(
                        f"size_bytes mismatch for '{htid}': "
                        f"expected {expected_size}, got {actual_size}"
                    )
            except OSError as exc:
                errors.append(f"Error stat'ing {file_path} for '{htid}': {exc}")
        else:
            warnings.append(f"No size_bytes in manifest for '{htid}', skipping size verification")

        files_checked += 1

    return files_checked, errors, warnings


def generate_validation_report(
    schema_errors: list[str],
    consistency_errors: list[str],
    file_errors: list[str],
    file_warnings: list[str],
    total_volumes: int,
    files_checked: int = 0,
) -> dict[str, Any]:
    """Generate a structured validation report.

    Args:
        schema_errors: Errors from manifest schema validation.
        consistency_errors: Errors from manifest consistency checks.
        file_errors: Errors from staged file verification.
        file_warnings: Warnings from staged file verification.
        total_volumes: Total volume count in manifest.
        files_checked: Number of files verified.

    Returns:
        Dict with summary and error details suitable for JSON output.

    """
    all_errors: list[str] = []
    all_errors.extend(schema_errors)
    all_errors.extend(consistency_errors)
    all_errors.extend(file_errors)

    return {
        "validated_at": datetime.now(UTC).isoformat(),
        "manifest": {
            "total_volumes": total_volumes,
            "files_checked": files_checked,
        },
        "results": {
            "passed": len(all_errors) == 0,
            "total_errors": len(all_errors),
            "total_warnings": len(file_warnings),
        },
        "errors": {
            "schema": {
                "count": len(schema_errors),
                "messages": schema_errors,
            },
            "consistency": {
                "count": len(consistency_errors),
                "messages": consistency_errors,
            },
            "file_integrity": {
                "count": len(file_errors),
                "messages": file_errors,
            },
        },
        "warnings": {
            "file_integrity": {
                "count": len(file_warnings),
                "messages": file_warnings,
            },
        },
    }


def write_report(report: dict[str, Any], report_path: Path) -> None:
    """Write validation report to a JSON file.

    Args:
        report: Validation report dict.
        report_path: Path to write the report.

    """
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    logger.info("Validation report written to {}", report_path)


# ---------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------


def _compute_sha256(file_path: Path) -> str | None:
    """Compute SHA-256 digest of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hex digest string or None if file doesn't exist.

    """
    if not file_path.exists():
        return None
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


# ---------------------------------------------------------------
# CLI
# ---------------------------------------------------------------


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments.

    Args:
        args: Optional list of argument strings (for testing). Defaults to sys.argv.

    Returns:
        Parsed namespace.

    """
    parser = argparse.ArgumentParser(
        description="Validate the volume catalog manifest and staged dataset.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("manifests/latest_manifest.json"),
        help="Path to the volume manifest JSON.",
    )
    parser.add_argument(
        "--stage-dir",
        type=Path,
        default=None,
        help="Optional: verify staged files against manifest.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=SCHEMA_PATH,
        help="Path to the JSON Schema file.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("data/_state/validation_report.json"),
        help="Path to write the validation report.",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Treat warnings as errors (non-zero exit).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args(args)


def validate(
    *,
    manifest_path: Path,
    schema_path: Path,
    stage_dir: Path | None = None,
    fail_on_warning: bool = False,
) -> tuple[dict[str, Any], int]:
    """Run the full validation pipeline and return (report, exit_code).

    Args:
        manifest_path: Path to the manifest JSON file.
        schema_path: Path to the JSON Schema file.
        stage_dir: Optional directory with staged files to verify.
        fail_on_warning: Treat warnings as errors.

    Returns:
        Tuple of (report dict, exit code).

    """
    if not manifest_path.exists():
        logger.error("Manifest not found: {}", manifest_path)
        report = generate_validation_report(
            schema_errors=[f"Manifest not found: {manifest_path}"],
            consistency_errors=[],
            file_errors=[],
            file_warnings=[],
            total_volumes=0,
        )
        return report, 1

    with manifest_path.open(encoding="utf-8") as f:
        manifest = json.load(f)

    volumes = manifest.get("volumes", [])
    if not isinstance(volumes, list):
        logger.error("Manifest 'volumes' is not a list")
        return generate_validation_report(
            schema_errors=["Manifest 'volumes' is not a list"],
            consistency_errors=[],
            file_errors=[],
            file_warnings=[],
            total_volumes=0,
        ), 1

    total_volumes = len(volumes)
    logger.info("Validating {} volumes from {}", total_volumes, manifest_path)

    # Step 1: Schema validation
    logger.info("Step 1/3: Validating manifest schema...")
    schema_errors = validate_manifest_schema(manifest, schema_path)

    # Step 2: Consistency checks
    logger.info("Step 2/3: Checking manifest consistency...")
    consistency_errors = check_manifest_consistency(volumes)

    # Step 3: File verification (optional)
    file_errors: list[str] = []
    file_warnings: list[str] = []
    files_checked = 0

    if stage_dir is not None:
        logger.info("Step 3/3: Verifying staged files in {}...", stage_dir)
        files_checked, file_errors, file_warnings = verify_staged_files(stage_dir, volumes)
    else:
        logger.info("Step 3/3: Skipped (no --stage-dir provided)")

    # Compile report
    report = generate_validation_report(
        schema_errors=schema_errors,
        consistency_errors=consistency_errors,
        file_errors=file_errors,
        file_warnings=file_warnings,
        total_volumes=total_volumes,
        files_checked=files_checked,
    )

    # Determine exit code
    exit_code = 0
    if report["results"]["total_errors"] > 0:
        exit_code = 1
    if fail_on_warning and report["results"]["total_warnings"] > 0:
        exit_code = max(exit_code, 1)

    return report, exit_code


def main() -> int:
    """CLI entry point."""
    configure_logging()
    args = parse_args()

    if args.verbose:
        configure_logging("DEBUG")

    report, exit_code = validate(
        manifest_path=args.manifest,
        schema_path=args.schema,
        stage_dir=args.stage_dir,
        fail_on_warning=args.fail_on_warning,
    )

    write_report(report, args.report)

    # Print summary
    results = report["results"]
    logger.info(
        "Validation {}: {} error(s), {} warning(s) across {} volume(s)",
        "PASSED" if results["passed"] else "FAILED",
        results["total_errors"],
        results["total_warnings"],
        report["manifest"]["total_volumes"],
    )

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
