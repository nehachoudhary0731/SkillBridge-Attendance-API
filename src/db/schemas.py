from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, time, datetime
from src.db.models import RoleEnum, AttendanceStatus



class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: RoleEnum
    institution_id: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MonitoringTokenRequest(BaseModel):
    key: str



class BatchCreate(BaseModel):
    name: str
    institution_id: str

class BatchResponse(BaseModel):
    id: str
    name: str
    institution_id: str
    created_at: datetime

    class Config:
        from_attributes = True



class InviteResponse(BaseModel):
    token: str
    expires_at: datetime

class JoinBatchRequest(BaseModel):
    token: str



class SessionCreate(BaseModel):
    batch_id: str
    title: str
    date: date
    start_time: time
    end_time: time

class SessionResponse(BaseModel):
    id: str
    batch_id: str
    trainer_id: str
    title: str
    date: date
    start_time: time
    end_time: time
    created_at: datetime

    class Config:
        from_attributes = True



class MarkAttendanceRequest(BaseModel):
    session_id: str
    status: AttendanceStatus

class AttendanceRecord(BaseModel):
    student_id: str
    student_name: str
    status: str
    marked_at: datetime

class AttendanceListResponse(BaseModel):
    session_id: str
    records: list[AttendanceRecord]
