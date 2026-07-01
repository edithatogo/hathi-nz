"""Tests for the Git mirror sync workflow."""

from __future__ import annotations

from pathlib import Path

WORKFLOW_PATH = Path(".github/workflows/mirror_sync.yml")


def test_mirror_workflow_skips_when_either_secret_is_missing() -> None:
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "GIT_MIRROR_URL" in content
    assert "GIT_MIRROR_SSH_PRIVATE_KEY" in content
    assert 'if [ -z "$GIT_MIRROR_URL" ] || [ -z "$GIT_MIRROR_SSH_PRIVATE_KEY" ]; then' in content
