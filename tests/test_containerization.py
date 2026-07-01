"""Tests for the repository containerization artifacts."""

from __future__ import annotations

from pathlib import Path


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())
DOCKERFILE_PATH = ROOT / "Dockerfile"
COMPOSE_PATH = ROOT / "docker-compose.yml"
DOCKERIGNORE_PATH = ROOT / ".dockerignore"
README_PATH = ROOT / "README.md"


def test_containerization_files_exist() -> None:
    assert DOCKERFILE_PATH.exists()
    assert COMPOSE_PATH.exists()
    assert DOCKERIGNORE_PATH.exists()


def test_dockerfile_uses_pixi_multi_stage_runtime() -> None:
    dockerfile = DOCKERFILE_PATH.read_text(encoding="utf-8")

    assert "FROM ubuntu:24.04 AS builder" in dockerfile
    assert "FROM ubuntu:24.04 AS runtime" in dockerfile
    assert "pixi.sh/install.sh" in dockerfile
    assert "install --locked -e dev" in dockerfile
    assert 'ENTRYPOINT ["/opt/pixi/bin/pixi", "run", "-e", "dev"]' in dockerfile
    assert 'CMD ["python"]' in dockerfile


def test_compose_mounts_data_and_manifests() -> None:
    compose = COMPOSE_PATH.read_text(encoding="utf-8")

    assert "env_file:" in compose
    assert "./data:/workspace/data" in compose
    assert "./manifests:/workspace/manifests" in compose
    assert "./generated:/workspace/generated" in compose
    assert "ZENODO_TOKEN" in compose
    assert "OSF_PROJECT_ID" in compose
    assert 'command: ["python", "scripts/validate_catalog.py", "--help"]' in compose


def test_dockerignore_excludes_generated_and_local_state() -> None:
    dockerignore = DOCKERIGNORE_PATH.read_text(encoding="utf-8")

    assert ".pixi" in dockerignore
    assert "data/raw" in dockerignore
    assert "data/processed" in dockerignore
    assert "data/metadata" in dockerignore
    assert "data/_state" in dockerignore
    assert "generated" in dockerignore


def test_readme_documents_container_usage() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "Containerization" in readme
    assert "docker build -t hathi-nz ." in readme
    assert "docker run --rm hathi-nz python scripts/validate_catalog.py --help" in readme
    assert "docker compose up --build" in readme
