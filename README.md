# Tactical Intelligence

AI-powered football tactical report generator built on StatsBomb open data.

## Product Flow

1. Select a match.
2. Load and structure event data.
3. Run tactical analytics.
4. Generate visualisations.
5. Use the LLM to turn structured findings into analyst-style prose.
6. Present the report in the UI.

## Repository Layout

- `backend/` Flask API and pipeline modules
- `backend/app/data/` StatsBomb ingestion and normalisation helpers
- `backend/app/analytics/` Passing, defensive, player, and tempo analysis
- `backend/app/llm/` Prompt construction and narrative orchestration
- `backend/app/reporting/` Final report assembly
- `frontend/` React demo interface
- `docs/` Architecture notes and future report examples

## Run the Backend

```bash
cd backend
python run.py
```

Useful endpoints:

- `GET /api/competitions`
- `GET /api/health`
- `GET /api/matches`
- `POST /api/reports/generate`

To enable the Qwen-backed report text, install the backend requirements and set
`QWEN_MODEL_NAME` if you want a different model. The default is
`Qwen/Qwen2.5-0.5B-Instruct`.

## Run the React UI

```bash
cd frontend
npm install
npm run dev
```

If your Flask API is not running on `http://localhost:8000`, set `VITE_API_BASE_URL`
in a local `.env` file inside `frontend/`.

## Notes

The current implementation is a scaffold. The analytics modules and LLM layer are intentionally structured so real StatsBomb processing and report generation can be added without changing the high-level architecture.
