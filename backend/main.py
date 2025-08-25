import sys, os

from fastapi.params import Depends
from typing import List,Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fastapi import FastAPI, UploadFile, BackgroundTasks, Form, HTTPException
from database import schema
from database.db import engine, Base, get_db
from database import models
from auth.auth import hash_password, verify_password
# Import from your actual file name
from lumino_graph import workflow
from database.storage import save_to_supabase
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
from utils.extract_text import extract_text_from_pdf
import urllib.parse

from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()  # initiate fastapi app--server

# ✅ Add CORS middleware if you need it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.get('/')
async def health():
    return {"message": 'API IS WORKING FINE'}

@app.post('/hr_create', response_model=schema.UserResponse)
async def create_user(user: schema.UserCreate, db:Session= Depends(get_db)):
    try:
        new_user=models.User(
            name= user.name,
            email=user.email,
            password_hash= hash_password(user.password),
            role=user.role,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    except Exception as e:
        return e



@app.post('/jobs', response_model=schema.JobResponse)
async def add_jobs(jobs: schema.JobBase, db: Session = Depends(get_db)):
    try:
        new_job = models.Job(
            title=jobs.title,
            description=jobs.description,
            department=jobs.department,
            location=jobs.location,
            salary_min=jobs.salary_min,
            salary_max=jobs.salary_max,
            seniority=jobs.seniority,
            requirements=jobs.requirements,
            posted_by= jobs.posted_by
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        return new_job
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating job: {str(e)}")


@app.post('/apply', response_model=schema.CandidateResponse)
async def apply_candidates(
        file: UploadFile,
        name: str = Form(...),
        email: str = Form(...),
        linkedin: str = Form(None),
        location: str = Form(None),
        phone: str = Form(None),
        job_id: int = Form(...),
        db: Session = Depends(get_db)
):
    try:
        # ✅ Check job exists
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # ✅ Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # ✅ Save resume to Supabase
        resume_path = f"resume/{email}_{file.filename}{uuid.uuid4()}"
        file_content = await file.read()

        # ✅ Extract text from resume
        resume_text = extract_text_from_pdf(file_content)
        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF or resume too short")

        resume_url = save_to_supabase(file_content, resume_path)

        # ✅ Create candidate record
        new_candidate = models.Candidate(
            name=name,
            email=email,
            phone=phone,
            location=location,
            linkedin=linkedin,
            resume_url=resume_url,
            resume_text=resume_text,
        )
        db.add(new_candidate)
        db.commit()
        db.refresh(new_candidate)

        # ✅ Prepare workflow data with ALL required fields
        candidate_data = {
            "job_role": job.title,
            "job_description": job.description,
            "resume_text": resume_text,
            "candidate_name": name,
            "candidate_email": email,
            # ✅ Initialize empty fields that the workflow expects
            "parsed_resume": {},
            "evaluation": {},
            "email": {}
        }

        print(f"Running workflow for candidate: {name}")

        # ✅ Run AI workflow with error handling
        try:
            result = await workflow.ainvoke(
                candidate_data,
                config={"configurable": {"thread_id": f"apply_{email}_{job_id}"}}
            )
            print(result)
            print("Workflow completed successfully")
        except Exception as workflow_error:
            print(f"Workflow error: {workflow_error}")
            # ✅ Don't fail the entire application if AI workflow fails
            result = {
                "parsed_resume": {"full_name": name, "email": email, "skills": [], "years_experience": 0},
                "evaluation": {"similarity_score": 50, "reason": "Could not evaluate due to processing error"},
                "email": {"subject": "Application Received", "body": f"Dear {name}, we have received your application.",
                          "to_email": email}
            }

        # ✅ Unpack AI results safely
        parsed_resume = result.get("parsed_resume", {})
        evaluation = result.get("evaluation", {})
        email_data = result.get("email", {})

        # ✅ Update candidate with AI-extracted info
        if parsed_resume:
            new_candidate.skills = parsed_resume.get("skills", [])
            new_candidate.years_experience = parsed_resume.get("years_experience", 0)
            db.commit()
            db.refresh(new_candidate)

        # ✅ Create application entry
        new_application = models.Application(
            job_id=job.id,
            candidate_id=new_candidate.id,
            similarity_score=evaluation.get("similarity_score", 0),
            screening_score=evaluation.get("similarity_score", 0),
            reason=evaluation.get("reason", "Application processed"),
        )
        db.add(new_application)
        db.commit()
        db.refresh(new_application)

        # Store generated email with correct field names
        if email_data and email_data.get("subject"):
            try:
                print(email_data)
                new_email = models.Email(
                    application_id=new_application.id,  # Correct field name
                    to_email=email_data.get("to_email", email),
                    subject=email_data.get("subject", "Application Update"),
                    body=email_data.get("body", "Thank you for your application."),
                    status="sent"  # Assuming the email was sent successfully
                )
                db.add(new_email)
                db.commit()
                db.refresh(new_email)
                print("Email record saved successfully")
            except Exception as email_error:
                print(f"Could not save email record: {email_error}")
                # Don't fail the entire process if email logging fails
                pass

        print(f"Application processed successfully for {name}")
        return new_candidate

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing application: {str(e)}")





@app.get('/jobs', response_model=List[schema.JobOut])
async def get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(models.Job).all()
    return jobs

@app.get('/jobs/{id}', response_model=schema.JobOut)
async def get_jobs_by_id(id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
@app.get('/candidates', response_model=List[schema.CandidateBase])
async def get_candidates(db:Session= Depends(get_db)):
    candidates= db.query(models.Candidate).all()
    if not candidates:
        raise HTTPException(status_code=404, detail='candidate not found')
    return candidates

@app.get('/candidates/{id}', response_model= schema.CandidateBase)
async def get_candidates_by_id(id:int, db: Session=Depends(get_db)):
    candidate= db.query(models.Candidate).filter(models.Candidate.id==id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail='Candidate not found')
    return candidate

@app.get('/email', response_model=schema.EmailBase)
async def get_email(db:Session= Depends(get_db)):
    email= db.query(models.Email).all()
    if not email:
        raise HTTPException(status_code=404,detail='email not found')
    return email

@app.get('/email/app/{id}', response_model=schema.EmailBase)
async def get_email_for_app(id:int, db:Session= Depends(get_db)):
    email= db.query(models.Email).filter(models.Email.application_id== id).first()
    if not email:
        raise HTTPException(status_code=404, detail='Email not found')
    return email


# ✅ Add endpoint to test if workflow is working
@app.get('/test-workflow')
async def test_workflow():
    """Test endpoint to verify the AI workflow is working"""
    try:
        test_data = {
            "job_role": "Software Engineer",
            "job_description": "We need a Python developer with 2+ years experience",
            "resume_text": "John Doe, Software Engineer with 3 years Python experience",
            "candidate_name": "John Doe",
            "candidate_email": "test@example.com",
            "parsed_resume": {},
            "evaluation": {},
            "email": {}
        }

        result = await workflow.ainvoke(
            test_data,
            config={"configurable": {"thread_id": "test-123"}}
        )

        return {
            "status": "success",
            "workflow_result": {
                "candidate": result.get("candidate_name"),
                "score": result.get("evaluation", {}).get("similarity_score"),
                "email_sent": bool(result.get("email", {}).get("subject"))
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}