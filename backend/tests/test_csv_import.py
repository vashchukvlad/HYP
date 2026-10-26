import csv
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.database import get_session
from app.security import current_user
from app.models import StudentRecord
from app.csv_import import COLUMNS, parse_students

VALUES = [1, 'STEM', 'Freshman', 3, 3.2, 4, 'Ideation', 'Beginner', 1, 'False', 8, 3, 'Allowed_With_Citation', 4, 80, 'Low']

def csv_bytes(rows=None):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(COLUMNS)
    writer.writerows(rows if rows is not None else [VALUES])
    return buffer.getvalue().encode('utf-8-sig')

@pytest.mark.asyncio
async def test_import_transaction_and_repeat(tmp_path):
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path}/test.db')
    async with engine.begin() as connection:
        await connection.run_sync(StudentRecord.__table__.create)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async def session():
        async with factory() as value:
            yield value
    app.dependency_overrides[get_session] = session
    try:
        with TestClient(app) as client:
            assert client.post('/students/import', files={'file': ('students.csv', csv_bytes())}).status_code == 401
            app.dependency_overrides[current_user] = lambda: object()
            response = client.post('/students/import', files={'file': ('students.csv', csv_bytes())})
            assert response.json() == {'inserted': 1, 'updated': 0, 'total': 1}
            changed = VALUES.copy(); changed[4] = 3.8
            response = client.post('/students/import', files={'file': ('students.csv', csv_bytes([changed]))})
            assert response.json() == {'inserted': 0, 'updated': 1, 'total': 1}
            invalid = VALUES.copy(); invalid[0] = 2; invalid[3] = 9
            assert client.post('/students/import', files={'file': ('students.csv', csv_bytes([changed, invalid]))}).status_code == 422
            data = client.get('/students').json()
            assert data['total'] == 1
            assert data['items'][0]['post_semester_gpa'] == 3.8
            assert client.get('/stats/summary').json()['total_count'] == 1
            assert client.post('/students/import', files={'file': ('students.txt', csv_bytes())}).status_code == 400
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

@pytest.mark.parametrize('content', [b'', b'ID,Major\n1,STEM', csv_bytes([]), csv_bytes([VALUES, VALUES]), b'\xff'])
def test_invalid_csv(content):
    with pytest.raises(ValueError):
        parse_students(content)
