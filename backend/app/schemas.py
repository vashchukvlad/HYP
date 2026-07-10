from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models import MajorCategory, YearOfStudy, PrimaryUseCase, SkillLevel, Policy, Burnout

class UserCreate(BaseModel): username: str = Field(min_length=3,max_length=64); email: EmailStr; password: str = Field(min_length=8,max_length=128)
class UserOut(BaseModel): model_config=ConfigDict(from_attributes=True); id: UUID; username: str; email: EmailStr; role: str; created_at: datetime
class LoginIn(BaseModel): username: str; password: str
class TokenOut(BaseModel): access_token: str; token_type: str="bearer"
class StudentRecordIn(BaseModel):
    source_student_id:int; major_category:MajorCategory; year_of_study:YearOfStudy; pre_semester_gpa:float=Field(ge=0,le=4); post_semester_gpa:float=Field(ge=0,le=4); weekly_genai_hours:float=Field(ge=0,le=40); primary_use_case:PrimaryUseCase; prompt_engineering_skill:SkillLevel; tool_diversity:int=Field(ge=1,le=5); paid_subscription:bool; traditional_study_hours:float=Field(ge=0); perceived_ai_dependency:int=Field(ge=1,le=10); institutional_policy:Policy; anxiety_level_during_exams:int=Field(ge=1,le=10); skill_retention_score:float=Field(ge=0,le=100); burnout_risk_level:Burnout
class StudentPatch(BaseModel): weekly_genai_hours:float|None=Field(default=None,ge=0,le=40); traditional_study_hours:float|None=Field(default=None,ge=0); perceived_ai_dependency:int|None=Field(default=None,ge=1,le=10); anxiety_level_during_exams:int|None=Field(default=None,ge=1,le=10); burnout_risk_level:Burnout|None=None
class StudentOut(StudentRecordIn): model_config=ConfigDict(from_attributes=True); id:int; gpa_delta:float
class StudentPage(BaseModel): items:list[StudentOut]; total:int; page:int; page_size:int
class SavedFilterIn(BaseModel): name:str=Field(min_length=1,max_length=100); filter_json:dict
class SavedFilterOut(SavedFilterIn): model_config=ConfigDict(from_attributes=True); id:int; created_at:datetime
