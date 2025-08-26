import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel, GoogleProvider
from pydantic import BaseModel
from email.message import EmailMessage as MimeEmail
import aiosmtplib
import json
import asyncio

load_dotenv()

google_key = os.getenv('GOOGLE_API_KEY')


class EmailMessage(BaseModel):
    to_email: str
    subject: str
    body: str


provider = GoogleProvider(api_key=google_key)
model = GoogleModel('gemini-1.5-flash', provider=provider)

# ✅ FIXED: Updated system prompt to focus only on email content creation
# ✅ Updated system prompt with similarity score threshold of 85
system_prompt = """
You are an expert HR assistant for Lumino AI. 

TASK: Create personalized email content for job candidates based on their application data.

You will receive candidate information as JSON input. Use the ACTUAL values from this input, especially the candidate_name and candidate_email.

Based on the similarity_score:
- similarity_score >= 85: Congratulate and invite for interview
- similarity_score < 85: Politely decline in a nice way and encourage future applications

IMPORTANT RULES:
- Do NOT mention the similarity score number or evaluation explanation in the email
- Keep it professional and friendly
- Focus ONLY on creating the email content (to_email, subject, body)
- Do NOT call any tools - just return the email structure

Email should be warm, professional, and appropriate for the candidate's score level.
"""

messaging_agent = Agent(
    model,
    output_type=EmailMessage,
    system_prompt=system_prompt
)


@messaging_agent.tool
async def email_sending(context: RunContext[None], email_info: EmailMessage) -> str:
    """Send an email to a candidate"""
    sender_email = os.getenv('SENDER_EMAIL')
    password = os.getenv('SENDER_PASSWORD')  # App Password for Gmail

    print(f"Attempting to send email from: {sender_email}")
    print(f"To: {email_info.to_email}")
    print(f"Subject: {email_info.subject}")

    if not sender_email or not password:
        error_msg = "Error: SENDER_EMAIL and SENDER_PASSWORD must be set in .env file"
        print(error_msg)
        return error_msg

    message = MimeEmail()
    message["From"] = sender_email
    message["To"] = email_info.to_email
    message["Subject"] = email_info.subject
    message.set_content(email_info.body)

    try:
        print("Connecting to Gmail SMTP server...")
        # Send asynchronously
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=sender_email,
            password=password,
        )
        success_msg = f"Email successfully sent to {email_info.to_email}"
        print(success_msg)
        return success_msg
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        print(error_msg)
        return error_msg


# ✅ NEW: Separate function to handle email sending after content creation
async def create_and_send_email(candidate_data: dict) -> dict:
    """Create email content first, then send it separately"""

    # Step 1: Create email content using the agent
    prompt = f"Create an email for this candidate: {json.dumps(candidate_data)}"

    try:
        # Generate email content
        result = await messaging_agent.run(prompt)
        email_content = result.output

        print(f"Generated email content for: {email_content.to_email}")

        # Step 2: Send the email using the tool function directly
        send_result = await email_sending(None, email_content)

        # Step 3: Return email content (not the send result)
        return {
            "to_email": email_content.to_email,
            "subject": email_content.subject,
            "body": email_content.body,
            "send_status": send_result  # Keep track of send status separately
        }

    except Exception as e:
        print(f"Error in create_and_send_email: {e}")
        return {
            "to_email": candidate_data.get("candidate_email", ""),
            "subject": "Application Update",
            "body": f"Dear {candidate_data.get('candidate_name', 'Candidate')}, thank you for your application.",
            "send_status": f"Error: {str(e)}"
        }


# ✅ UPDATED: Test function using the new approach
async def test_agent():
    # First, let's check if environment variables are set
    print("Checking environment variables...")
    sender_email = os.getenv('SENDER_EMAIL')
    password = os.getenv('SENDER_PASSWORD')
    google_key = os.getenv('GOOGLE_API_KEY')

    print(f"SENDER_EMAIL: {'✓ Set' if sender_email else '✗ Not set'}")
    print(f"SENDER_PASSWORD: {'✓ Set' if password else '✗ Not set'}")
    print(f"GOOGLE_API_KEY: {'✓ Set' if google_key else '✗ Not set'}")
    print()

    if not sender_email or not password:
        print("ERROR: Please set SENDER_EMAIL and SENDER_PASSWORD in your .env file")
        print("For Gmail, use an App Password (not your regular password)")
        print("Generate one at: https://myaccount.google.com/apppasswords")
        return

    # Test data
    test_input = {
        "candidate_name": "Omons Wisdom",
        "candidate_email": "omonswisdom.ict@gmail.com",
        "job_title": "AI Engineer",
        "similarity_score": 95,
        "evaluation_explanation": "Strong skills and impactful AI projects.",
        "parsed_resume": {
            "skills": ["Python", "TensorFlow", "PyTorch"],
            "work_experience": [
                {"company": "AI Labs", "role": "ML Engineer", "start_date": "2020", "end_date": "2023",
                 "description": "Built predictive models."}
            ],
            "highest_education": "M.Sc. Computer Science",
            "certifications": ["AWS ML Specialty"]
        }
    }

    try:
        # Use the new function
        result = await create_and_send_email(test_input)

        print("Generated Email:")
        print(json.dumps({
            "to_email": result["to_email"],
            "subject": result["subject"],
            "body": result["body"]
        }, indent=4))

        print(f"\nSend Status: {result['send_status']}")

    except Exception as e:
        print(f"Error running agent: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_agent())