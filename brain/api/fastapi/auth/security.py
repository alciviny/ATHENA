from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import os

# Set environment to avoid bcrypt bug detection before importing passlib
os.environ['PASSLIB_BUFSIZE'] = '1024'

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from brain.config.settings import settings
from brain.infrastructure.persistence.database import get_async_db
from brain.application.ports.repositories import StudentRepository
from brain.infrastructure.persistence.postgres_repositories import PostgresStudentRepository

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Security scheme
security = HTTPBearer()

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    student_id: Optional[UUID] = None

class UserCredentials(BaseModel):
    email: str  # Changed from student_id to email
    password: str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    # Truncate password to 72 bytes to avoid bcrypt limitation
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    truncated_password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(truncated_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        student_id: str = payload.get("sub")
        if student_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(student_id=UUID(student_id))
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data

async def get_current_student(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UUID:
    """Dependency to get current authenticated student."""
    token_data = verify_token(credentials.credentials)
    return token_data.student_id

async def authenticate_student(email: str, password: str, db: AsyncSession) -> Optional[UUID]:
    """
    Authenticate a student using email and password.
    Checks against the database.
    """
    repo = PostgresStudentRepository(db)
    student = await repo.get_by_email(email)

    if not student:
        return None

    if not student.is_authenticated():
        return None

    if not verify_password(password, student.password_hash):
        return None

    # Update last login
    await repo.update_last_login(student.id)

    return student.id