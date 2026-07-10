"""Idempotently load data/raw/ai_impact_on_students.csv. Null rows are dropped: the source is specified as complete, so imputing would manufacture demo data."""
import asyncio, logging, sys
from pathlib import Path
import pandas as pd
from sqlalchemy import delete, insert
# In Docker the backend source is /app/app and this script is mounted at
# /app/scripts; locally it is <repo>/scripts and source is <repo>/backend/app.
root = Path(__file__).resolve().parents[1]
source_root = root if (root / "app").is_dir() else root / "backend"
sys.path.insert(0, str(source_root))
from app.database import SessionLocal
from app.models import StudentRecord
from app.schemas import StudentRecordIn

COLUMNS={"Student_ID":"source_student_id","Major_Category":"major_category","Year_of_Study":"year_of_study","Pre_Semester_GPA":"pre_semester_gpa","Post_Semester_GPA":"post_semester_gpa","Weekly_GenAI_Hours":"weekly_genai_hours","Primary_Use_Case":"primary_use_case","Prompt_Engineering_Skill":"prompt_engineering_skill","Tool_Diversity":"tool_diversity","Paid_Subscription":"paid_subscription","Traditional_Study_Hours":"traditional_study_hours","Perceived_AI_Dependency":"perceived_ai_dependency","Institutional_Policy":"institutional_policy","Anxiety_Level_During_Exams":"anxiety_level_during_exams","Skill_Retention_Score":"skill_retention_score","Burnout_Risk_Level":"burnout_risk_level"}
async def main(path:Path):
    df=pd.read_csv(path).rename(columns=COLUMNS).drop_duplicates(); before=len(df); df=df.dropna(); logging.info("Dropped %s duplicate/null rows",before-len(df)); valid=[]
    for index,row in df.iterrows():
        try: valid.append(StudentRecordIn(**row.to_dict()).model_dump())
        except Exception as exc: logging.warning("Skipping CSV row %s: %s",index,exc)
    async with SessionLocal() as session:
        await session.execute(delete(StudentRecord))
        for i in range(0,len(valid),1000): await session.execute(insert(StudentRecord).values(valid[i:i+1000]))
        await session.commit()
    logging.info("Inserted %s validated rows",len(valid))
if __name__=="__main__":
    logging.basicConfig(level=logging.INFO); file=Path(sys.argv[1]) if len(sys.argv)>1 else Path("data/raw/ai_impact_on_students.csv"); asyncio.run(main(file))
