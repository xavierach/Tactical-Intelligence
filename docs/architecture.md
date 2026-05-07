# Architecture

This repository is organized around a report-generation pipeline:

1. StatsBomb event data is loaded and normalized in `backend/app/data/`.
2. Tactical features are computed in `backend/app/analytics/`.
3. Structured outputs are translated into narrative in `backend/app/llm/`.
4. The final report payload is composed in `backend/app/reporting/`.
5. Flask exposes the API surface in `backend/app/routes/`.
6. React provides the demo UI in `frontend/`.

## Guiding Principles

- Keep analytical calculations deterministic.
- Keep LLM usage for interpretation and presentation, not metric generation.
- Return structured JSON from the backend so the UI can stay thin.
- Preserve extensibility for future visualizations and richer match filters.
