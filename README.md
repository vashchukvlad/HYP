# AI Impact on Students dashboard

A full-stack demo for exploring an illustrative, potentially synthetic Kaggle dataset about generative-AI usage, academic outcomes, and wellbeing. It shows correlations only; it does not make causal claims about students.

## Run locally

1. Copy `.env.example` to `.env` and change `JWT_SECRET`.
2. From the repository root, start all services:

   ```sh
   docker compose up -d --build --wait
   ```

3. Open http://localhost:5173, click **Create an account**, register, and sign in.
4. In **Student records**, click **Import students.csv** and select your complete dataset CSV. For a quick check, use the included `examples/students.csv` (two illustrative records). The success message reports added/updated rows; the table, record count, and charts refresh automatically.

The API and Swagger UI are at http://localhost:8000/docs. PostgreSQL 16 runs in Compose; migrations run automatically before the backend starts, and the frontend waits for the backend health check. No local Python, Node, or PostgreSQL installation is required. Ports 5173, 8000, and 5432 must be available. Use a recent Docker Compose v2 with `--wait` support.

`docker compose down` stops the stack while retaining imported records in the `postgres_data` volume. Start it again with `docker compose up -d --wait`. Avoid `down -v` if you want to keep your data.

### Verify import against PostgreSQL in Docker

```sh
docker compose --profile test run --build --rm postgres-tests
```

This builds the test image, starts a separate PostgreSQL 16 database without published ports, applies the real Alembic migrations, and checks registration/login, UUID and enum handling, authenticated CSV import, repeated import, invalid-file rejection, table/statistics results, and concurrent uploads of the same Student ID. It uses the production database/session code without mocks. The test database uses temporary storage and does not access `postgres_data` or your imported students. A successful run ends with `1 passed`.

Stop the test database afterwards:

```sh
docker compose --profile test stop postgres-test
```

The same PostgreSQL check runs in GitHub Actions on pull requests.

### Optional command-line seed

To replace all student records with a dataset downloaded from `laveshjadon/ai-impact-on-students`, put it at `data/raw/ai_impact_on_students.csv`, then run:

```sh
docker compose exec backend python /app/scripts/seed_db.py /app/data/raw/ai_impact_on_students.csv
```

Unlike the dashboard import, this seed command deletes existing students before inserting validated rows. Use the dashboard to insert/update while preserving other students.

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
