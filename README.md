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

### Codex cloud Docker setup

Run `bash scripts/docker-cloud-up.sh` from the existing checkout. It starts all three services with Compose, generates `.env` with a random development JWT secret if absent, and keeps cloud build helpers outside the checkout. Docker Compose with BuildKit, Python 3, and the cloud machine's trusted CA bundle are required. Existing `.env` files are preserved.

The helper forwards the injected proxy through Docker's predefined build arguments, resolves its current hostname for build networking, and adds the machine's trusted CA bundle while keeping TLS verification enabled. It does not save proxy credentials. `HYP_CLOUD_DIR` and `DOCKER_CONFIG` can override the writable helper and Docker configuration directories. Ordinary local Docker users can continue using `docker compose up --build`.

Check `docker compose ps`, request `/health`, `/students`, and `/stats/summary` on API port 8000, and verify the frontend on port 5173. PostgreSQL data persists in the Compose volume; do not use `down -v` unless you intend to delete it. Backend startup applies migrations transactionally before starting the API. Kaggle data is optional for checking startup and authentication.

## Import students.csv from the dashboard

Sign in, open **Student records**, click **Import students.csv**, and choose the full dataset CSV. Imports accept UTF-8 (including BOM), at most 10 MB and 50,000 records. Headers may use the original Kaggle names (`Student_ID`, `Major_Category`, etc.) or the API field names. All 16 student fields are required; the abbreviated visible-table export is not an import template.

The entire file is validated before any changes. Invalid rows or duplicate Student IDs reject the upload with a row-specific error. New Student IDs are inserted; existing IDs are updated in a single transaction. Other students are preserved. The dashboard refreshes its table and charts and reports inserted/updated counts.

The authenticated API is `POST /students/import`, with multipart field `file`.

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
