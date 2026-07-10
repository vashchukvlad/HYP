# AI Impact on Students dashboard

A full-stack demo for exploring an illustrative, potentially synthetic Kaggle dataset about generative-AI usage, academic outcomes, and wellbeing. It shows correlations only; it does not make causal claims about students.

## Run locally

1. Copy `.env.example` to `.env` and change `JWT_SECRET`.
2. Start the stack: `docker compose up --build`.
3. Download `laveshjadon/ai-impact-on-students` from Kaggle and place its CSV at `data/raw/ai_impact_on_students.csv` (or pass its path explicitly below).
4. Seed the database after services start:

   `docker compose exec backend python /app/scripts/seed_db.py /app/data/raw/ai_impact_on_students.csv`

   If using the repository script outside Docker: `cd backend && uv run python ../scripts/seed_db.py ../data/raw/ai_impact_on_students.csv`.

The frontend is at http://localhost:5173 and API docs are at http://localhost:8000/docs. The seed process drops duplicate and null rows, validates every remaining row, logs failures, then truncate/reloads in 1,000-row Core insert batches. This makes it safe to rerun.

## API

- `POST /auth/register`, `POST /auth/login`, `GET /users/me`
- `GET`, `POST /students`; `GET`, `PATCH`, `DELETE /students/{id}`
- `GET /stats/summary`, `/stats/burnout-by-usage`, `/stats/study-vs-gpa`, `/stats/major-distribution`
- `GET /filters/options`; `POST`, `GET /filters`; `DELETE /filters/{id}`

Example:

```sh
curl -X POST http://localhost:8000/auth/register -H 'content-type: application/json' \
  -d '{"username":"demo","email":"demo@example.com","password":"safe-password"}'
curl 'http://localhost:8000/students?major_category=STEM&page=1&page_size=10'
```

All data routes share `major_category`, `year_of_study`, `institutional_policy`, and `search` filtering. Protected routes accept `Authorization: Bearer <token>`.

## Development and tests

Backend dependencies are managed by `uv` when installed: `cd backend && uv sync --extra dev`. Run `uv run pytest`. The included validation smoke test is database-independent; for API integration tests, run PostgreSQL via Compose and configure `DATABASE_URL` before executing tests.

The browser client stores the JWT in `localStorage` to keep this take-home app simple. That is vulnerable to XSS token theft; a production application should use secure httpOnly, SameSite cookies with CSRF protections.
