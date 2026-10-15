# Module 2: Agentic Engine

This folder is the workspace for Module 2, responsible for the local procurement verification agent and its controlled reasoning workflow.

## Responsibilities

- Build the ReAct reasoning loop for retrieval, verification, and response generation.
- Define typed tools and state with LangGraph and Pydantic.
- Compare Standard RAG and OKF-backed reasoning paths.
- Wire the local action harness for spreadsheet and database status updates.
- Run local language models through Ollama without sending project data to external services.

## Boundary

The engine consumes prepared data from `data_pipeline/` and exposes results and controlled actions to `frontend_ui/`. It does not own document ingestion or presentation-layer layout.
