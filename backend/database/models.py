from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, DateTime, Boolean,
    Numeric, ForeignKey, Date, CheckConstraint, JSON
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declarative_base
from .db import Base

# -------------------------------
# Users
# -------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(Text, CheckConstraint("role IN ('admin','recruiter','hiring_manager','employee')"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    active = Column(Boolean, default=True)

    jobs = relationship("Job", back_populates="poster")
    employees = relationship("Employee", back_populates="user")
    leave_approvals = relationship("LeaveRequest", back_populates="approver")
    audit_logs = relationship("AuditLog", back_populates="actor")


# -------------------------------
# Jobs
# -------------------------------
class Job(Base):
    __tablename__ = "jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    department = Column(Text)
    location = Column(Text)
    salary_min = Column(Numeric)
    salary_max = Column(Numeric)
    seniority = Column(Text)
    requirements = Column(JSONB)
    status = Column(Text, CheckConstraint("status IN ('open','closed')"), server_default="open")
    posted_by = Column(BigInteger, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    poster = relationship("User", back_populates="jobs")
    applications = relationship("Application", back_populates="job")


# -------------------------------
# Candidates
# -------------------------------
class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    phone = Column(Text)
    location = Column(Text)
    linkedin = Column(Text)
    resume_url = Column(Text)
    resume_text = Column(Text)
    skills = Column(ARRAY(Text))
    years_experience = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    applications = relationship("Application", back_populates="candidate")
    employee = relationship("Employee", back_populates="candidate", uselist=False)


# -------------------------------
# Applications
# -------------------------------
class Application(Base):
    __tablename__ = "applications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(BigInteger, ForeignKey("jobs.id", ondelete="CASCADE"))
    candidate_id = Column(BigInteger, ForeignKey("candidates.id", ondelete="CASCADE"))
    stage = Column(Text, CheckConstraint(
        "stage IN ('applied','screened','shortlisted','interview','offer','rejected','hired')"
    ), server_default="applied")
    similarity_score = Column(Numeric)
    screening_score = Column(Numeric)
    reason = Column(Text)
    auto_mode = Column(Text, CheckConstraint("auto_mode IN ('auto_send','approval','hybrid')"), server_default="hybrid")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")
    emails = relationship("Email", back_populates="application")
    interviews = relationship("Interview", back_populates="application")


# -------------------------------
# Emails
# -------------------------------
class Email(Base):
    __tablename__ = "emails"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    application_id = Column(BigInteger, ForeignKey("applications.id", ondelete="CASCADE"))
    to_email = Column(Text, nullable=False)
    subject = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    status = Column(Text, CheckConstraint("status IN ('queued','sent','failed')"), server_default="queued")
    provider_id = Column(Text)
    sent_at = Column(DateTime(timezone=True))

    application = relationship("Application", back_populates="emails")


# -------------------------------
# Interviews
# -------------------------------
class Interview(Base):
    __tablename__ = "interviews"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    application_id = Column(BigInteger, ForeignKey("applications.id", ondelete="CASCADE"))
    calendly_event_id = Column(Text)
    scheduled_start = Column(DateTime(timezone=True))
    scheduled_end = Column(DateTime(timezone=True))
    location = Column(Text)
    status = Column(Text, CheckConstraint("status IN ('proposed','booked','completed','canceled')"), server_default="proposed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    application = relationship("Application", back_populates="interviews")


# -------------------------------
# Employees
# -------------------------------
class Employee(Base):
    __tablename__ = "employees"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    candidate_id = Column(BigInteger, ForeignKey("candidates.id"))
    user_id = Column(BigInteger, ForeignKey("users.id"))
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    role_title = Column(Text)
    department = Column(Text)
    start_date = Column(Date)
    salary = Column(Numeric)
    leave_balance = Column(Integer, default=21)
    status = Column(Text, CheckConstraint("status IN ('active','on_leave','terminated')"), server_default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="employee")
    user = relationship("User", back_populates="employees")
    leave_requests = relationship("LeaveRequest", back_populates="employee")


# -------------------------------
# Leave Requests
# -------------------------------
class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    employee_id = Column(BigInteger, ForeignKey("employees.id", ondelete="CASCADE"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text)
    status = Column(Text, CheckConstraint("status IN ('pending','approved','rejected','canceled')"), server_default="pending")
    approver_id = Column(BigInteger, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    employee = relationship("Employee", back_populates="leave_requests")
    approver = relationship("User", back_populates="leave_approvals")


# -------------------------------
# Audit Logs
# -------------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    actor_user_id = Column(BigInteger, ForeignKey("users.id"))
    action = Column(Text, nullable=False)
    entity = Column(Text, nullable=False)
    entity_id = Column(BigInteger, nullable=False)
    payload = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    actor = relationship("User", back_populates="audit_logs")
