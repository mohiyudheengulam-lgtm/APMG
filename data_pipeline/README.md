# Module 1: Data Pipeline

This folder is the workspace for Module 1, responsible for preparing procurement knowledge for both the Standard RAG and OKF evaluation paths.

## Responsibilities

- Parse and normalize structured and unstructured procurement documents.
- Chunk, embed, and index source content in PostgreSQL with PGVector.
- Convert source documents into versioned OKF Markdown bundles.
- Keep ingestion, metadata, provenance, and retrieval inputs reproducible.

## Boundary

The pipeline produces clean retrieval inputs and OKF bundles for the agentic engine. It does not own agent reasoning, user-interface behavior, or procurement action execution.
