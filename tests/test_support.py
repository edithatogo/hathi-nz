"""Test support utilities for hathi-nz tests."""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path


def test_tmp_dir() -> None:
    """Return a writable root for local test artifacts and assert it's valid."""
    configured = os.environ.get("HATHI_NZ_TEST_TMP")
    candidate = (Path(configured) if configured else Path(tempfile.gettempdir())) / "hathi-nz-tests"
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        probe = candidate / f".probe-{uuid.uuid4().hex}"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError:
        if configured:
            raise
        candidate = Path(tempfile.gettempdir()) / f"hathi-nz-tests-{uuid.uuid4().hex}"
        candidate.mkdir(parents=True, exist_ok=True)
    assert candidate.exists(), f"Test directory {candidate} should exist"
