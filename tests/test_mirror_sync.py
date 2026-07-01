"""Tests for the Git mirror sync workflow."""

from __future__ import annotations

from pathlib import Path


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())
WORKFLOW_PATH = ROOT / ".github/workflows/mirror_sync.yml"


def test_mirror_workflow_skips_when_either_secret_is_missing() -> None:
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "GIT_MIRROR_URL" in content
    assert "GIT_MIRROR_SSH_PRIVATE_KEY" in content
    assert 'if [ -z "$GIT_MIRROR_URL" ] || [ -z "$GIT_MIRROR_SSH_PRIVATE_KEY" ]; then' in content
