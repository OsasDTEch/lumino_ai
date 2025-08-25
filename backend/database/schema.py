from datetime import datetime, date
from typing import List, Optional, Any
from pydantic import BaseModel, EmailStr


# -------------------------------
# Users
# -------------------------------
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str
    active: Optional[bool] = True


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# -------------------------------
# Jobs
# -------------------------------
class JobBase(BaseModel):
    title: str
    description: str
    department: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    seniority: Optional[str] = None
    requirements: Optional[dict] = None
    poster:int
    status: Optional[str] = "open"


class JobCreate(JobBase):
    pass
class JobOut(BaseModel):
    id: int
    title: str
    description: str

    class Config:
        from_attributes= True


class JobResponse(JobBase):
    id: int
    posted_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True



# -------------------------------
# Candidates
# -------------------------------
class CandidateBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    resume_url: Optional[str] = None
    resume_text: Optional[str] = None
    skills: Optional[List[str]] = []
    years_experience: Optional[int] = None


class CandidateCreate(CandidateBase):
    pass


class CandidateResponse(CandidateBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

#candidate out



# -------------------------------
# Applications
# -------------------------------
class ApplicationBase(BaseModel):
    job_id: int
    candidate_id: int
    stage: Optional[str] = "applied"
    similarity_score: Optional[float] = None
    screening_score: Optional[float] = None
    reason: Optional[str] = None
    auto_mode: Optional[str] = "hybrid"


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationResponse(ApplicationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# -------------------------------
# Emails
# -------------------------------
class EmailBase(BaseModel):
    application_id: int
    to_email: str
    subject: str
    body: str
    status: Optional[str] = "queued"
    provider_id: Optional[str] = None


class EmailCreate(EmailBase):
    pass


class EmailResponse(EmailBase):
    id: int
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True


# -------------------------------
# Interviews
# -------------------------------
class InterviewBase(BaseModel):
    application_id: int
    calendly_event_id: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    location: Optional[str] = None
    status: Optional[str] = "proposed"


class InterviewCreate(InterviewBase):
    pass


class InterviewResponse(InterviewBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# -------------------------------
# Employees
# -------------------------------
class EmployeeBase(BaseModel):
    candidate_id: int
    user_id: int
    name: str
    email: str
    role_title: Optional[str] = None
    department: Optional[str] = None
    start_date: Optional[date] = None
    salary: Optional[float] = None
    leave_balance: Optional[int] = 21
    status: Optional[str] = "active"


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeResponse(EmployeeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# -------------------------------
# Leave Requests
# -------------------------------
class LeaveRequestBase(BaseModel):
    employee_id: int
    start_date: date
    end_date: date
    reason: Optional[str] = None
    status: Optional[str] = "pending"
    approver_id: Optional[int] = None


class LeaveRequestCreate(LeaveRequestBase):
    pass


class LeaveRequestResponse(LeaveRequestBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# -------------------------------
# Audit Logs
# -------------------------------
class AuditLogBase(BaseModel):
    actor_user_id: Optional[int]
    action: str
    entity: str
    entity_id: int
    payload: Optional[Any]


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogResponse(AuditLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
