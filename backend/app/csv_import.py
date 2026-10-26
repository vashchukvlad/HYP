"""Validate the complete CSV before changing any records."""
import csv
import io
from pydantic import ValidationError
from app.schemas import StudentRecordIn

COLUMNS = {'Student_ID': 'source_student_id', 'Major_Category': 'major_category', 'Year_of_Study': 'year_of_study', 'Pre_Semester_GPA': 'pre_semester_gpa', 'Post_Semester_GPA': 'post_semester_gpa', 'Weekly_GenAI_Hours': 'weekly_genai_hours', 'Primary_Use_Case': 'primary_use_case', 'Prompt_Engineering_Skill': 'prompt_engineering_skill', 'Tool_Diversity': 'tool_diversity', 'Paid_Subscription': 'paid_subscription', 'Traditional_Study_Hours': 'traditional_study_hours', 'Perceived_AI_Dependency': 'perceived_ai_dependency', 'Institutional_Policy': 'institutional_policy', 'Anxiety_Level_During_Exams': 'anxiety_level_during_exams', 'Skill_Retention_Score': 'skill_retention_score', 'Burnout_Risk_Level': 'burnout_risk_level'}


def parse_students(content: bytes) -> list[dict]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("CSV must use UTF-8 encoding")
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        headers = reader.fieldnames or []
        mapped = [COLUMNS.get(h.strip(), h.strip()) for h in headers]
        required = set(StudentRecordIn.model_fields)
        if len(mapped) != len(set(mapped)):
            raise ValueError("Duplicate CSV columns")
        missing = required - set(mapped)
        if missing:
            raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
        records = {}
        for row in reader:
            line = reader.line_num
            if None in row or None in row.values():
                raise ValueError(f"Row {line}: incorrect number of columns")
            values = {COLUMNS.get(k.strip(), k.strip()): v.strip() for k, v in row.items()}
            try:
                record = StudentRecordIn.model_validate(values).model_dump()
            except ValidationError as exc:
                error = exc.errors()[0]
                raise ValueError(f"Row {line}, {error['loc'][0]}: {error['msg']}") from exc
            student_id = record["source_student_id"]
            if student_id in records:
                raise ValueError(f"Row {line}: duplicate Student_ID {student_id}")
            records[student_id] = record
            if len(records) > 50000:
                raise ValueError("Maximum 50,000 students per import")
    except csv.Error as exc:
        raise ValueError(f"Invalid CSV: {exc}") from exc
    if not records:
        raise ValueError("CSV contains no student records")
    return list(records.values())
