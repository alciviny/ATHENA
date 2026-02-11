from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from uuid import uuid4, UUID

from brain.api.fastapi.auth.security import (
    authenticate_student,
    create_access_token,
    Token,
    get_current_student,
    get_password_hash
)
from brain.infrastructure.persistence.database import get_async_db
from brain.config.settings import settings

router = APIRouter()

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    goal: str

class UpdateGoalRequest(BaseModel):
    goal: str

@router.post("/auth/register")
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Register a new student."""
    from brain.infrastructure.persistence.models import StudentModel, CognitiveProfileModel
    
    # Check if email already exists
    existing = await db.execute(
        db.query(StudentModel).filter(StudentModel.email == request.email)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create cognitive profile
    profile = CognitiveProfileModel(
        id=uuid4(),
        student_id=uuid4(),  # Will be updated
        retention_rate=0.5,
        learning_speed=0.5,
        stress_sensitivity=0.5
    )
    db.add(profile)
    await db.flush()
    
    # Create student
    student = StudentModel(
        id=profile.student_id,
        name=request.name,
        email=request.email,
        password_hash=get_password_hash(request.password),
        goal=request.goal,
        cognitive_profile_id=profile.id
    )
    db.add(student)
    await db.commit()
    
    return {"message": "Student registered successfully", "student_id": str(student.id)}

@router.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Authenticate student and return JWT token.

    - username: student email
    - password: student password
    """
    student_id = await authenticate_student(form_data.username, form_data.password, db)
    if not student_id:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(student_id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me")
async def get_current_user_info(current_student: str = Depends(get_current_student)):
    """Get current authenticated student info."""
    return {"student_id": current_student}

@router.post("/auth/refresh", response_model=Token)
async def refresh_token(current_student: str = Depends(get_current_student)):
    """Refresh JWT token."""
    access_token = create_access_token(data={"sub": current_student})
    return {"access_token": access_token, "token_type": "bearer"}

@router.put("/auth/goal")
async def update_goal(
    request: UpdateGoalRequest,
    current_student: UUID = Depends(get_current_student),
    db: AsyncSession = Depends(get_async_db)
):
    """Update student's study goal."""
    from brain.infrastructure.persistence.models import StudentModel
    
    student_id = current_student
    student = await db.get(StudentModel, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student.goal = request.goal
    await db.commit()
    return {"message": "Goal updated successfully"}