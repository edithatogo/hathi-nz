# Specification: Containerization

## 1. Overview
Provide a Dockerfile that packages the pixi environment and pipeline scripts for reproducible execution across any platform or cloud environment.

## 2. Components

### 2.1 Dockerfile
- Use pixi-based Docker image (prefix-dev/pixi or custom)
- Multi-stage build:
  - Stage 1 (pixi-env): Install pixi, create environment, cache deps
  - Stage 2 (runtime): Copy environment and scripts, set entrypoint
- Exclude data/ directories (mounted at runtime)

### 2.2 Docker Compose
- docker-compose.yml for local development with:
  - Volume mounts for data/ and manifests/
  - Environment variable passthrough (.env)

### 2.3 Documentation
- Update README.md with Docker usage instructions

## 3. Acceptance Criteria
- docker build -t hathi-nz . succeeds
- docker run hathi-nz python scripts/validate_catalog.py --help works
- Data directories mountable from host
