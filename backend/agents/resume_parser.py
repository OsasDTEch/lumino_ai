import os
from typing import Optional, List

from dotenv import load_dotenv

load_dotenv()
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel,GoogleProvider

from pydantic import BaseModel
google_key= os.getenv('GOOGLE_API_KEY')

provider = GoogleProvider(api_key=google_key)
model = GoogleModel('gemini-1.5-flash', provider=provider)
class WorkExperience(BaseModel): # jus for seperated
    company: Optional[str]
    role: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    description: Optional[str]

class ResumeParsed(BaseModel):
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    linkedin: Optional[str]
    years_experience: Optional[int]
    skills: List[str] = []
    highest_education: Optional[str]
    work_experience: List[WorkExperience] = []   # use model
    certifications: List[str] = []
    languages: List[str] = []
    summary: Optional[str]




system_prompt = """
You are a professional HR assistant. Your job is to analyze resumes and extract structured data. 
Always output in valid JSON. If information is missing, set the value to null.

Extract:
- full_name
- email
- phone
- location
- linkedin (or portfolio/github if available)
- years_experience (numeric, estimate if unclear)
- skills (list of unique skills, standardized e.g. ['Python', 'Django', 'SQL'])
- highest_education (degree, field, institution if possible)
- work_experience: list of jobs with {company, role, start_date, end_date, description}
- certifications (list of certifications with issuer)
- languages (list of spoken languages with proficiency if available)
- summary (1–2 sentence professional summary from the CV)
"""

resume_parser_agent= Agent(
    model,
    output_type=ResumeParsed,
    system_prompt=system_prompt

)
test ="""
John Doe
📍 Lagos, Nigeria | 📞 +234 814 123 4567 | ✉️ johndoe@email.com
 | 🔗 linkedin.com/in/johndoe

Professional Summary

Results-driven Software Engineer with 4+ years of experience building scalable web applications and APIs. Skilled in React.js, Node.js, and Python, with a strong background in designing user-friendly interfaces and optimizing backend systems. Adept at working in cross-functional teams to deliver high-quality digital products on time.

Core Skills

Frontend: React.js, Next.js, Tailwind CSS

Backend: Node.js, Express.js, Python, FastAPI

Databases: PostgreSQL, MongoDB, Firebase

Tools: Git, Docker, Jira, AWS, CI/CD pipelines

Soft Skills: Problem-solving, Collaboration, Communication

Professional Experience

Software Engineer | Osas Tech — Remote
Jan 2021 – Present

Built and deployed a real estate web app with authentication, property search, and chat functionality using React and Firebase.

Designed reusable UI components with Tailwind CSS, improving development speed by 30%.

Integrated Flutterwave payment system into an eCommerce app, enabling seamless checkout and purchase history tracking.

Collaborated with product managers and designers to refine UX/UI for multiple web platforms.

Frontend Developer (Intern) | TechLabs, Lagos
Jun 2019 – Dec 2020

Developed responsive landing pages and dashboards using HTML, CSS, and JavaScript.

Assisted in migrating legacy web apps to React.js, reducing load time by 25%.

Created documentation for frontend components, easing onboarding for new team members.

Education

B.Sc. Computer Science
University of Lagos — 2015 – 2019

Projects

NexusMart eCommerce – Full-stack marketplace with category filters, cart, payments, and admin dashboard.

HavenHomes Real Estate App – Property listing platform with Firebase backend and chat feature.

CoinMaven Crypto Platform – Crypto trading dashboard with news integration from CoinGecko API.

Certifications

AWS Cloud Practitioner – 2023

Google Data Analytics Professional Certificate – 2022
"""
async def main():
    result=await resume_parser_agent.run(test)
    print(result)
    return result

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
