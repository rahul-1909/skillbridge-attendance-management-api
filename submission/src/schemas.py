from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SignupRequest(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=6)
    role: str
    institution_id: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MonitoringTokenRequest(BaseModel):
    key: str


class InstitutionCreate(BaseModel):
    name: str = Field(min_length=2)


class BatchCreate(BaseModel):
    name: str = Field(min_length=2)
    institution_id: Optional[int] = None


class BatchInviteCreate(BaseModel):
    expires_in_hours: int = Field(default=24, ge=1, le=168)


class BatchJoinRequest(BaseModel):
    token: str


class SessionCreate(BaseModel):
    batch_id: int
    title: str = Field(min_length=2)
    date: date
    start_time: time
    end_time: time


class AttendanceMarkRequest(BaseModel):
    session_id: int
    status: str


class SessionAttendanceItem(BaseModel):
    student_id: int
    student_name: str
    student_email: EmailStr
    status: str
    marked_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceListResponse(BaseModel):
    session_id: int
    records: list[SessionAttendanceItem]


class MessageResponse(BaseModel):
    message: str


class BatchSummaryResponse(BaseModel):
    batch_id: int
    batch_name: str
    total_sessions: int
    present: int
    absent: int
    late: int


class InstitutionSummaryResponse(BaseModel):
    institution_id: int
    institution_name: str
    total_batches: int
    total_sessions: int
    total_students: int
    present: int
    absent: int
    late: int


class ProgrammeSummaryResponse(BaseModel):
    total_institutions: int
    total_batches: int
    total_sessions: int
    total_students: int
    present: int
    absent: int
    late: int
