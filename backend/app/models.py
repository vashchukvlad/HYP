import enum
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase): pass
class MajorCategory(str, enum.Enum): STEM="STEM"; BUSINESS="Business"; HUMANITIES="Humanities"; MEDICAL="Medical"; ARTS="Arts"
class YearOfStudy(str, enum.Enum): FRESHMAN="Freshman"; SOPHOMORE="Sophomore"; JUNIOR="Junior"; SENIOR="Senior"; GRADUATE="Graduate"
class PrimaryUseCase(str, enum.Enum): COPYWRITING="Copywriting/Drafting"; SUMMARIZING="Summarizing_Reading"; DEBUGGING="Debugging/Troubleshooting"; IDEATION="Ideation"; DIRECT_ANSWER="Direct_Answer_Generation"
class SkillLevel(str, enum.Enum): BEGINNER="Beginner"; INTERMEDIATE="Intermediate"; ADVANCED="Advanced"
class Policy(str, enum.Enum): ALLOWED="Allowed_With_Citation"; BAN="Strictly_Ban"; ENCOURAGED="Actively_Encouraged"
class Burnout(str, enum.Enum): LOW="Low"; MEDIUM="Medium"; HIGH="High"

class User(Base):
    __tablename__="users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class StudentRecord(Base):
    __tablename__="student_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_student_id: Mapped[int] = mapped_column(Integer, index=True)
    major_category: Mapped[MajorCategory] = mapped_column(Enum(MajorCategory), index=True)
    year_of_study: Mapped[YearOfStudy] = mapped_column(Enum(YearOfStudy), index=True)
    pre_semester_gpa: Mapped[float] = mapped_column(Float)
    post_semester_gpa: Mapped[float] = mapped_column(Float)
    weekly_genai_hours: Mapped[float] = mapped_column(Float)
    primary_use_case: Mapped[PrimaryUseCase] = mapped_column(Enum(PrimaryUseCase))
    prompt_engineering_skill: Mapped[SkillLevel] = mapped_column(Enum(SkillLevel))
    tool_diversity: Mapped[int] = mapped_column(Integer)
    paid_subscription: Mapped[bool] = mapped_column(Boolean)
    traditional_study_hours: Mapped[float] = mapped_column(Float)
    perceived_ai_dependency: Mapped[int] = mapped_column(Integer)
    institutional_policy: Mapped[Policy] = mapped_column(Enum(Policy), index=True)
    anxiety_level_during_exams: Mapped[int] = mapped_column(Integer)
    skill_retention_score: Mapped[float] = mapped_column(Float)
    burnout_risk_level: Mapped[Burnout] = mapped_column(Enum(Burnout))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class SavedFilter(Base):
    __tablename__="saved_filters"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    filter_json: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
