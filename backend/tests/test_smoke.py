"""Run against a disposable PostgreSQL database configured with DATABASE_URL."""
import pytest
from app.schemas import StudentRecordIn

def test_student_validation():
    record=StudentRecordIn(source_student_id=1,major_category="STEM",year_of_study="Freshman",pre_semester_gpa=3,post_semester_gpa=3.2,weekly_genai_hours=4,primary_use_case="Ideation",prompt_engineering_skill="Beginner",tool_diversity=1,paid_subscription=False,traditional_study_hours=8,perceived_ai_dependency=3,institutional_policy="Allowed_With_Citation",anxiety_level_during_exams=4,skill_retention_score=80,burnout_risk_level="Low")
    assert record.post_semester_gpa-record.pre_semester_gpa==pytest.approx(.2)

# Integration coverage to run after `docker compose up -d postgres`:
# register/login, 401, filtered /students, and /stats/summary are exercised with curl
# in the README; production CI should use a dedicated disposable PostgreSQL service.
