# Procurement Verification Agent

University engineering project at THWS comparing Standard Retrieval-Augmented Generation (RAG) with the Open Knowledge Format (OKF) for procurement compliance verification.

The system is designed around small local language models under 2B parameters, run through Ollama. Keeping inference and project data local supports absolute data privacy and makes the approach suitable for sensitive procurement documents.

## Problem Statement (WIP)

The final problem statement is currently being drafted. This section will define the procurement verification use case, the compliance questions to be answered, the boundaries of the agent's decisions, and the measurable research questions for comparing Standard RAG with OKF.

## Team Structure

The project is divided into three coordinated modules:

1. **Module 1 - Data Pipeline** (`data_pipeline/`)
	Document parsing, indexing, retrieval preparation, and conversion of structured and unstructured sources into OKF Markdown bundles.
2. **Module 2 - Agentic Engine** (`agentic_engine/`)
	ReAct reasoning, tool definitions, local model orchestration, and controlled procurement status updates.
3. **Module 3 - Frontend UI** (`frontend_ui/`)
	Web and chatbot experience for document uploads, verification requests, results, and user interaction.

Project planning, research, and evaluation material belongs in [`docs/`](docs/).

## Privacy and Local Development

Run language models locally with [Ollama](https://ollama.com/). Do not commit credentials, downloaded model artifacts, vector databases, test outputs, or procurement documents. The repository's `.gitignore` contains the baseline protections for local development.

## Status

This repository currently contains the project skeleton. Module-specific implementation details and the formal evaluation plan will be added as the problem statement is finalized.