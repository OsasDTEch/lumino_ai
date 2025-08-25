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
system_prompt = """
You are an expert HR assistant for Lumino AI. 

TASK: You must both craft a personalized email AND send it using the email_sending tool.

PROCESS:
1. First, create the email content based on the candidate data provided
2. Then, immediately call the email_sending tool to send the email

You will receive candidate information as JSON input. Use the ACTUAL values from this input, especially the candidate_name and candidate_email.

Based on the similarity_score:
- similarity_score >= 90: Congratulate and invite for interview
- 50 <= similarity_score < 90: Thank them and mention application is under review  
- similarity_score < 50: Politely decline and encourage future applications

Do NOT mention the similarity score number or evaluation explanation in the email. Keep it professional and friendly.

IMPORTANT: After creating the email content, you MUST call the email_sending tool to actually send it.
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


async def send_email(email_info: EmailMessage):
    """Send email directly without using the agent tool"""
    sender_email = os.getenv('SENDER_EMAIL')
    password = os.getenv('SENDER_PASSWORD')  # App Password for Gmail

    if not sender_email or not password:
        print("Error: SENDER_EMAIL and SENDER_PASSWORD must be set in .env file")
        return

    message = MimeEmail()
    message["From"] = sender_email
    message["To"] = email_info.to_email
    message["Subject"] = email_info.subject
    message.set_content(email_info.body)

    try:
        # Send asynchronously
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=sender_email,
            password=password,
        )
        print(f"Email successfully sent to {email_info.to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")


# Sample input to the messaging agent
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

    # Convert the input to a JSON string for the agent
    prompt = f"Create and send an email for this candidate: {json.dumps(test_input)}"

    try:
        # Ask the agent to craft and send the email
        result = await messaging_agent.run(prompt)

        print("Generated Email:")
        print(result.output.model_dump_json(indent=4))

        print(f"\nFull result: {result}")

    except Exception as e:
        print(f"Error running agent: {e}")
        import traceback
        traceback.print_exc()




if __name__ == "__main__":
    asyncio.run(test_agent())