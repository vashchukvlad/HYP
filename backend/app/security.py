from uuid import UUID
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_session
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
def hash_password(value:str)->str: return pwd_context.hash(value)
def verify_password(value:str, hashed:str)->bool: return pwd_context.verify(value,hashed)
def create_token(user:User)->str:
    return jwt.encode({"sub":str(user.id),"exp":datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_expire_minutes)},settings.jwt_secret,algorithm=settings.jwt_algorithm)
async def current_user(token:str=Depends(oauth2_scheme), session:AsyncSession=Depends(get_session))->User:
    try: user_id=UUID(jwt.decode(token,settings.jwt_secret,algorithms=[settings.jwt_algorithm])["sub"])
    except (JWTError, ValueError, TypeError, KeyError): user_id=None
    if not user_id: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid authentication credentials",headers={"WWW-Authenticate":"Bearer"})
    user=await session.scalar(select(User).where(User.id==user_id))
    if not user: raise HTTPException(status_code=401,detail="User not found")
    return user
