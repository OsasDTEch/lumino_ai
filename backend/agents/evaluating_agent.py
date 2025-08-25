import os
from typing import Optional, List

from dotenv import load_dotenv

load_dotenv()
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel, GoogleProvider

from pydantic import BaseModel

google_key = os.getenv('GOOGLE_API_KEY')


class Evaluated(BaseModel):
    similarity_score: int  # ✅ This matches what you use in system_prompt
    reason: str           # ✅ This matches what you use in system_prompt


provider = GoogleProvider(api_key=google_key)
model = GoogleModel('gemini-1.5-flash', provider=provider)
system_prompt = """
You are an expert HR assistant. 
Your task: evaluate how well a candidate matches a job description for **any role**.  

Steps:
1. Carefully read the job description.  
2. Carefully read the candidate's resume.  
3. Compare:
   - Skills listed in the JD vs skills on resume
   - Years and relevance of experience
   - Projects and accomplishments (real-world, impactful projects should score higher than small or educational exercises)
   - Education and certifications
   - Leadership, communication, or other extra skills relevant to the role
4. Assign a similarity score from 0–100 based on overall match.  
   - Highlight practical experience and impactful projects; treat toy or generic exercises as lower impact.
5. Provide a short explanation of why you gave that score.  

Return your response in this exact format:
{
    "similarity_score": [number 0-100],
    "reason": "[short explanation]"
}
"""

evaluator = Agent(model,
                  output_type=Evaluated,
                  system_prompt=system_prompt)


async def main():
    job_description = """
    We are hiring an AI Engineer with expertise in Python, Machine Learning, Deep Learning (TensorFlow or PyTorch),
    NLP, and model deployment experience. The candidate should have experience in building scalable AI systems
    and working with cloud platforms.
    """

    candidate_resume = """
    John Smith – AI Engineer

    Professional Summary:
    3 years experience developing ML and DL models using Python, TensorFlow, and PyTorch.
    Built NLP pipelines for text classification and sentiment analysis.
    Experience deploying AI models on AWS and GCP.
    Projects include a real-time recommendation system for e-commerce and a chatbot for customer support.

    Skills:
    Python, TensorFlow, PyTorch, NLP, Scikit-learn, AWS, GCP, Docker, Kubernetes

    Education:
    M.Sc. Artificial Intelligence – University of Lagos

    Certifications:
    AWS Certified Machine Learning – 2023
    """

    result = await evaluator.run(f"Job description:\n{job_description}\n\nCandidate resume:\n{candidate_resume}")

    print(result)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())