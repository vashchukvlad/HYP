from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import case, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models import Burnout, MajorCategory, Policy, SavedFilter, StudentRecord, User, YearOfStudy
from app.schemas import LoginIn, SavedFilterIn, SavedFilterOut, StudentOut, StudentPage, StudentPatch, StudentRecordIn, TokenOut, UserCreate, UserOut
from app.security import create_token, current_user, hash_password, verify_password

app=FastAPI(title="AI Impact on Students API",version="0.1.0")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173","http://localhost:3000"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

def filters(major_category:MajorCategory|None=None,year_of_study:YearOfStudy|None=None,institutional_policy:Policy|None=None,search:str|None=None):
    values=[]
    if major_category: values.append(StudentRecord.major_category==major_category)
    if year_of_study: values.append(StudentRecord.year_of_study==year_of_study)
    if institutional_policy: values.append(StudentRecord.institutional_policy==institutional_policy)
    if search and search.isdigit(): values.append(StudentRecord.source_student_id==int(search))
    return values
def student_out(row:StudentRecord)->dict:
    data={c.name:getattr(row,c.name) for c in StudentRecord.__table__.columns}; data["gpa_delta"]=round(row.post_semester_gpa-row.pre_semester_gpa,3); return data

@app.get("/health")
async def health(): return {"status":"ok"}
@app.post("/auth/register",response_model=UserOut,status_code=201)
async def register(body:UserCreate,session:AsyncSession=Depends(get_session)):
    if await session.scalar(select(User).where((User.username==body.username)|(User.email==body.email))): raise HTTPException(409,"Username or email already exists")
    user=User(username=body.username,email=str(body.email),hashed_password=hash_password(body.password)); session.add(user); await session.commit(); await session.refresh(user); return user
@app.post("/auth/login",response_model=TokenOut)
async def login(body:LoginIn,session:AsyncSession=Depends(get_session)):
    user=await session.scalar(select(User).where(User.username==body.username))
    if not user or not verify_password(body.password,user.hashed_password): raise HTTPException(status_code=401,detail="Incorrect username or password")
    return TokenOut(access_token=create_token(user))
@app.get("/users/me",response_model=UserOut)
async def me(user:User=Depends(current_user)): return user

@app.get("/students",response_model=StudentPage)
async def list_students(major_category:MajorCategory|None=None,year_of_study:YearOfStudy|None=None,institutional_policy:Policy|None=None,search:str|None=None,sort_by:str="source_student_id",sort_dir:str="asc",page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),session:AsyncSession=Depends(get_session)):
    where=filters(major_category,year_of_study,institutional_policy,search); total=await session.scalar(select(func.count()).select_from(StudentRecord).where(*where)) or 0
    allowed={"source_student_id", "pre_semester_gpa", "post_semester_gpa", "weekly_genai_hours", "traditional_study_hours", "skill_retention_score"}; column=getattr(StudentRecord,sort_by if sort_by in allowed else "source_student_id")
    rows=(await session.scalars(select(StudentRecord).where(*where).order_by(column.desc() if sort_dir.lower()=="desc" else column.asc()).offset((page-1)*page_size).limit(page_size))).all()
    return StudentPage(items=[StudentOut(**student_out(x)) for x in rows],total=total,page=page,page_size=page_size)
@app.get("/students/{record_id}",response_model=StudentOut)
async def detail(record_id:int,session:AsyncSession=Depends(get_session)):
    row=await session.get(StudentRecord,record_id)
    if not row: raise HTTPException(404,"Student record not found")
    return StudentOut(**student_out(row))
@app.post("/students",response_model=StudentOut,status_code=201)
async def create_student(body:StudentRecordIn,_:User=Depends(current_user),session:AsyncSession=Depends(get_session)):
    row=StudentRecord(**body.model_dump()); session.add(row); await session.commit(); await session.refresh(row); return StudentOut(**student_out(row))
@app.patch("/students/{record_id}",response_model=StudentOut)
async def patch_student(record_id:int,body:StudentPatch,_:User=Depends(current_user),session:AsyncSession=Depends(get_session)):
    row=await session.get(StudentRecord,record_id)
    if not row: raise HTTPException(404,"Student record not found")
    for key,value in body.model_dump(exclude_none=True).items(): setattr(row,key,value)
    await session.commit(); await session.refresh(row); return StudentOut(**student_out(row))
@app.delete("/students/{record_id}",status_code=204)
async def delete_student(record_id:int,_:User=Depends(current_user),session:AsyncSession=Depends(get_session)):
    if not await session.get(StudentRecord,record_id): raise HTTPException(404,"Student record not found")
    await session.execute(delete(StudentRecord).where(StudentRecord.id==record_id)); await session.commit()

@app.get("/stats/summary")
async def summary(major_category:MajorCategory|None=None,year_of_study:YearOfStudy|None=None,institutional_policy:Policy|None=None,search:str|None=None,session:AsyncSession=Depends(get_session)):
    where=filters(major_category,year_of_study,institutional_policy,search); q=select(func.count(),func.avg(StudentRecord.weekly_genai_hours),func.avg(StudentRecord.post_semester_gpa-StudentRecord.pre_semester_gpa)).where(*where); count,hours,delta=(await session.execute(q)).one()
    mode=await session.scalar(select(StudentRecord.burnout_risk_level).where(*where).group_by(StudentRecord.burnout_risk_level).order_by(func.count().desc()).limit(1))
    return {"total_count":count,"avg_weekly_genai_hours":round(hours or 0,2),"most_common_burnout":mode,"avg_gpa_delta":round(delta or 0,3)}
@app.get("/stats/burnout-by-usage")
async def burnout_usage(major_category:MajorCategory|None=None,year_of_study:YearOfStudy|None=None,institutional_policy:Policy|None=None,search:str|None=None,session:AsyncSession=Depends(get_session)):
    bucket=case((StudentRecord.weekly_genai_hours<5,"0–5"),(StudentRecord.weekly_genai_hours<10,"5–10"),(StudentRecord.weekly_genai_hours<20,"10–20"),else_="20–40").label("bucket"); rows=(await session.execute(select(bucket,StudentRecord.burnout_risk_level,func.count()).where(*filters(major_category,year_of_study,institutional_policy,search)).group_by(bucket,StudentRecord.burnout_risk_level))).all(); return [{"bucket":b,"burnout_risk_level":r,"count":c} for b,r,c in rows]
@app.get("/stats/study-vs-gpa")
async def study_gpa(major_category:MajorCategory|None=None,year_of_study:YearOfStudy|None=None,institutional_policy:Policy|None=None,search:str|None=None,session:AsyncSession=Depends(get_session)):
    rows=(await session.execute(select(StudentRecord.traditional_study_hours,(StudentRecord.post_semester_gpa-StudentRecord.pre_semester_gpa).label("gpa_delta")).where(*filters(major_category,year_of_study,institutional_policy,search)).order_by(func.random()).limit(400))).all(); return [{"traditional_study_hours":x,"gpa_delta":round(y,3)} for x,y in rows]
@app.get("/stats/major-distribution")
async def major_distribution(major_category:MajorCategory|None=None,year_of_study:YearOfStudy|None=None,institutional_policy:Policy|None=None,search:str|None=None,session:AsyncSession=Depends(get_session)):
    rows=(await session.execute(select(StudentRecord.major_category,func.count()).where(*filters(major_category,year_of_study,institutional_policy,search)).group_by(StudentRecord.major_category))).all(); return [{"major_category":x,"count":y} for x,y in rows]
@app.get("/filters/options")
async def options(): return {"major_category":[x.value for x in MajorCategory],"year_of_study":[x.value for x in YearOfStudy],"institutional_policy":[x.value for x in Policy]}
@app.post("/filters",response_model=SavedFilterOut,status_code=201)
async def save_filter(body:SavedFilterIn,user:User=Depends(current_user),session:AsyncSession=Depends(get_session)):
    row=SavedFilter(user_id=user.id,**body.model_dump()); session.add(row); await session.commit(); await session.refresh(row); return row
@app.get("/filters",response_model=list[SavedFilterOut])
async def saved_filters(user:User=Depends(current_user),session:AsyncSession=Depends(get_session)): return (await session.scalars(select(SavedFilter).where(SavedFilter.user_id==user.id).order_by(SavedFilter.created_at.desc()))).all()
@app.delete("/filters/{filter_id}",status_code=204)
async def remove_filter(filter_id:int,user:User=Depends(current_user),session:AsyncSession=Depends(get_session)):
    row=await session.get(SavedFilter,filter_id)
    if not row or row.user_id!=user.id: raise HTTPException(404,"Saved filter not found")
    await session.delete(row); await session.commit()
