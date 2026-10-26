"""Run only against the disposable database in the Compose test profile."""
import csv
import io
import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from app.csv_import import COLUMNS
from app.main import app

pytestmark = pytest.mark.skipif(
    os.environ.get("POSTGRES_IMPORT_TEST") != "1",
    reason="Use docker compose --profile test run --build --rm postgres-tests",
)


def dataset(student_id, gpa=3.2):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(COLUMNS)
    writer.writerow([student_id, "STEM", "Freshman", 3, gpa, 4, "Ideation",
                     "Beginner", 1, "False", 8, 3, "Allowed_With_Citation", 4, 80, "Low"])
    return output.getvalue().encode("utf-8-sig")


def test_postgres_import():
    # Real JWT authentication, migrated PostgreSQL schema, native UUID/enum types,
    # and the production session dependency; no database/auth mocks.
    with TestClient(app) as client:
        suffix = uuid4().hex[:12]
        credentials = {"username": "csv_" + suffix, "password": "postgres-test-password"}
        response = client.post("/auth/register", json={**credentials, "email": suffix + "@example.com"})
        assert response.status_code == 201, response.text
        response = client.post("/auth/login", json=credentials)
        assert response.status_code == 200, response.text
        headers = {"Authorization": "Bearer " + response.json()["access_token"]}
        assert client.get("/users/me", headers=headers).status_code == 200
        assert client.get("/filters", headers=headers).status_code == 200
        student_id = int(suffix[:7], 16)

        def upload(content):
            return client.post("/students/import", headers=headers,
                               files={"file": ("students.csv", content, "text/csv")})

        content = dataset(student_id)
        assert client.post("/students/import", files={"file": ("students.csv", content)}).status_code == 401
        response = upload(content)
        assert response.status_code == 200, response.text
        assert response.json() == {"inserted": 1, "updated": 0, "total": 1}
        response = upload(dataset(student_id, 3.8))
        assert response.json() == {"inserted": 0, "updated": 1, "total": 1}
        assert upload(dataset(student_id, 9)).status_code == 422
        response = client.get("/students", params={"search": student_id})
        assert response.json()["total"] == 1
        row = response.json()["items"][0]
        assert row["post_semester_gpa"] == 3.8
        assert row["major_category"] == "STEM"
        assert row["paid_subscription"] is False
        assert client.get("/stats/summary", params={"search": student_id}).json()["total_count"] == 1

        # Two simultaneous imports of a new ID must create exactly one row.
        concurrent_id = student_id + 1
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(upload, [dataset(concurrent_id)] * 2))
        assert all(r.status_code == 200 for r in responses), [r.text for r in responses]
        assert sum(r.json()["inserted"] for r in responses) == 1
        assert sum(r.json()["updated"] for r in responses) == 1
        assert client.get("/students", params={"search": concurrent_id}).json()["total"] == 1
        # Importing another student preserves previously imported rows.
        assert client.get("/students", params={"search": student_id}).json()["items"][0]["post_semester_gpa"] == 3.8
