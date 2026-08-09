from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_registry_readiness_is_rights_aware() -> None:
    text = (ROOT / "docs" / "registry-readiness.md").read_text(encoding="utf-8")
    assert "repository_ready_external_gates_pending" in text
    assert "metadata-only" in text
    assert "#36" in text and "#37" in text and "#38" in text
    assert "does not relicense" in text
