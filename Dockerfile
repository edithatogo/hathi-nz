FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PIXI_HOME=/opt/pixi

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://pixi.sh/install.sh | bash -s -- -y -p "${PIXI_HOME}"

WORKDIR /workspace

COPY pixi.toml pyproject.toml pixi.lock ./
COPY README.md DATASET_CARD.md .zenodo.json ./
COPY manifests ./manifests
COPY scripts ./scripts

RUN "${PIXI_HOME}/bin/pixi" install --locked -e dev

FROM ubuntu:24.04 AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PIXI_HOME=/opt/pixi \
    PATH="/opt/pixi/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY --from=builder /opt/pixi /opt/pixi
COPY --from=builder /workspace /workspace

ENTRYPOINT ["/opt/pixi/bin/pixi", "run", "-e", "dev"]
CMD ["python"]
