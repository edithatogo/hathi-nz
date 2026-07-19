# HathiTrust-NZ Structured Extraction Plan

## Objective

Use `edithatogo/nlp-policy-nz` as the governed transformation layer between the HathiTrust-NZ archive registry and reusable, structured Hugging Face datasets. Processing runs on cloud workers initiated by GitHub Actions; the local repository stores contracts, manifests, tests, and small fixtures rather than the corpus.

## Source Boundary

The canonical input is `manifests/hathitrust-nz/archive_registry.json` plus source-specific manifests. Every admitted item must carry its HTID, source identifier, source checksum, rights decision, acquisition route, and publication eligibility. Endpoint availability is not evidence of content completeness. Restricted material remains metadata- and provenance-only.

## Processing Graph

1. Resolve each archive-registry row to immutable source objects and page images or PDFs where permitted.
2. Preserve supplied OCR as one observation, never as unquestioned ground truth.
3. Render pages deterministically and run document preprocessing, layout detection, reading-order recovery, and independent OCR engines.
4. Compare supplied OCR and re-OCR at page, line, and token level. Retain alternatives, confidence, disagreement metrics, and visual coordinates.
5. Reconstruct document hierarchy, including volume, sitting, date, page, debate, speech, speaker, role, question, interjection, table, illustration, header, and marginal note.
6. Apply `nlp-policy-nz` entity, relation, topic, citation, rules-as-code, embedding, knowledge-graph, and provenance stages only after OCR quality gates pass.
7. Materialize versioned Parquet, JSONL, JSON-LD/PROV-O, Markdown, vector, graph, and quality-report views.
8. Publish eligible derivatives as configurations of the existing HathiTrust-NZ Hugging Face datasets and reference immutable Zenodo releases from collection manifests.

## OCR Strategy

Adopt a benchmarked ensemble rather than selecting a single engine in advance:

- Docling provides a normalized document model, layout, reading order, tables, and lossless JSON.
- PaddleOCR PP-StructureV3 provides document orientation, layout regions, multi-column order, tables, and structured JSON/Markdown.
- Surya is a second layout, reading-order, table, and multilingual OCR observation.
- olmOCR is the GPU/VLM candidate for difficult pages, complex formatting, handwriting, and low-confidence escalation.
- Existing embedded/Hathi OCR remains the baseline observation.

The deterministic cascade runs inexpensive engines first and invokes GPU/VLM OCR only for pages that fail calibrated quality thresholds. Engine/model revisions, prompts, parameters, container digests, and checksums are recorded for every observation. Human-reviewed benchmark pages remain isolated from model fitting and production evaluation.

## Hugging Face Data Products

Each product is partitioned by source dataset, document ID, year, and access class where useful:

| Configuration | Grain | Purpose |
| --- | --- | --- |
| `inventory` | volume | Discovery, rights, source, acquisition, and completeness |
| `documents` | volume | Canonical metadata and document-level summaries |
| `pages` | page | Page image references, OCR variants, quality, and layout |
| `blocks` | layout block | Reading order, bounding boxes, block types, and text alternatives |
| `tokens` | token | Coordinates, confidence, normalization, and alignment |
| `speeches` | parliamentary turn | Speaker-attributed Hansard analysis |
| `entities_relations` | assertion | Named entities, citations, relationships, and source spans |
| `topics_embeddings` | chunk | Topics, multilingual embeddings, and retrieval identifiers |
| `knowledge_graph` | node/edge | JSON-LD/RDF-compatible graph exports |
| `quality_provenance` | run/item | OCR comparisons, gates, lineage, model cards, and known gaps |

Large page images remain in their lawful source archive or a dedicated object/LFS-compatible store; dataset rows use content-addressed references. Public Hugging Face configurations contain only redistribution-eligible content.

## Orchestration

GitHub Actions validates manifests, creates work shards, dispatches CPU or GPU jobs, collects signed result manifests, runs quality/security gates, and publishes. GPU execution may use Hugging Face Jobs or another pinned cloud runner, but no workflow may silently fall back to processing the corpus on a developer workstation. Jobs are resumable and idempotent using `(source_sha256, pipeline_version, model_digest)` cache keys.

## Acceptance Gates

- All 510 curated Hansard rows are represented without conflation with broader NZ discovery results.
- Every published text span resolves to a source object, page, coordinates where available, and processing run.
- OCR benchmark reporting includes CER, WER, reading-order, layout-region, table, speaker-attribution, calibration, and cost/throughput metrics.
- Supplied OCR versus re-OCR disagreement is retained; no destructive overwrite occurs.
- Restricted or uncertain records fail closed before content publication.
- Dataset cards report coverage by source, year, document type, rights class, OCR route, and quality band.
- Re-runs are deterministic or explicitly record nondeterministic model/runtime factors.

## Delivery

Implementation is governed in `nlp-policy-nz` by Tracks 86-91. The tracks deliberately extend its existing provenance, extraction, semantic, graph, quality, Hugging Face, and Zenodo capabilities instead of duplicating those systems here.

## Technical References

- [Docling](https://github.com/docling-project/docling)
- [olmOCR](https://github.com/allenai/olmocr)
- [Surya](https://github.com/datalab-to/surya)
- [PP-StructureV3](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/PP-StructureV3.html)
