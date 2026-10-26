FROM python:3.12-slim AS base
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

FROM base AS test
RUN pip install --no-cache-dir '.[dev]'
COPY . .
CMD ["sh", "-c", "alembic upgrade head && pytest -q tests/test_postgres_import.py"]

FROM base AS runtime
COPY . .
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
