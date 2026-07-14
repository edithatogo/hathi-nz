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


def test_mirror_workflow_skips_when_no_target_is_configured() -> None:
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "GIT_MIRROR_URL" in content
    assert "GIT_MIRROR_SSH_PRIVATE_KEY" in content
    assert 'if [ "${#urls[@]}" -eq 0 ]; then' in content
    assert "No mirror URLs configured; skipping mirror." in content


def test_mirror_workflow_supports_both_named_targets_and_legacy_secret() -> None:
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "GITLAB_MIRROR_URL" in content
    assert "GITLAB_MIRROR_TOKEN" in content
    assert "CODEBERG_MIRROR_URL" in content
    assert "GIT_MIRROR_KNOWN_HOSTS" in content
    assert "refs/remotes/origin/*:refs/heads/*" in content
    assert "refs/tags/*:refs/tags/*" in content
    assert "mirror_targets_pushed" in content
    assert 'gitlab_token="${GITLAB_MIRROR_TOKEN//' in content
    assert 'http.extraheader=PRIVATE-TOKEN: $gitlab_token' in content
    assert '-c credential.helper=' in content


def test_mirror_workflow_fails_closed_for_configured_target_without_key_pinning() -> None:
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "No pinned SSH host key" in content
    assert "exit 1" in content
