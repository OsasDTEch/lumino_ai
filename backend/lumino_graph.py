import json

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from typing import Dict, Any
from typing_extensions import TypedDict
import asyncio

# Import agents
from agents.resume_parser import resume_parser_agent, ResumeParsed
from agents.evaluating_agent import evaluator, Evaluated
from agents.messaging_agent import messaging_agent, EmailMessage


# ----------------------------
# Define application state
# ----------------------------
class ApplicationState(TypedDict):
    job_description: str
    resume_text: str
    parsed_resume: Dict[str, Any]
    evaluation: Dict[str, Any]
    email: Dict[str, Any]
    job_role: str
    candidate_name: str  # ✅ Add these to make data flow easier
    candidate_email: str


# ----------------------------
# Node functions
# ----------------------------

async def parse_resume(state: ApplicationState) -> ApplicationState:
    """Run resume parsing agent"""
    print("🔄 Parsing resume...")
    result = await resume_parser_agent.run(state["resume_text"])
    state["parsed_resume"] = result.output.model_dump()

    # ✅ Extract candidate info for later use
    state["candidate_name"] = state["parsed_resume"].get("full_name", "Candidate")
    state["candidate_email"] = state["parsed_resume"].get("email", "test@example.com")

    print(f"✅ Parsed resume for: {state['candidate_name']}")
    return state


async def evaluate_candidate(state: ApplicationState) -> ApplicationState:
    """Run evaluator on parsed resume + job description"""
    print("🔄 Evaluating candidate...")
    jd = state["job_description"]
    resume_text = state["resume_text"]

    prompt = f"Job description:\n{jd}\n\nCandidate resume:\n{resume_text}"
    result = await evaluator.run(prompt)

    state["evaluation"] = result.output.model_dump()

    score = state["evaluation"].get("similarity_score", 0)
    print(f"✅ Evaluation complete. Score: {score}/100")
    return state


async def send_email_node(state: ApplicationState) -> ApplicationState:
    """Generate + send email based on evaluation"""
    print("🔄 Generating and sending email...")

    eval_result = state["evaluation"]
    parsed_resume = state["parsed_resume"]

    # ✅ Create clean input data for messaging agent
    email_input = {
        "candidate_name": state["candidate_name"],
        "candidate_email": state["candidate_email"],
        "job_title": state["job_role"],
        "similarity_score": eval_result.get("similarity_score", 0),
        "evaluation_explanation": eval_result.get("reason", ""),
        "parsed_resume": parsed_resume
    }

    # ✅ Convert to clean JSON string
    prompt = f"Create and send an email for this candidate: {json.dumps(email_input)}"

    result = await messaging_agent.run(prompt)
    state["email"] = result.output.model_dump()

    print(f"✅ Email sent to: {state['candidate_email']}")
    return state


# ----------------------------
# Build graph
# ----------------------------
graph = StateGraph(ApplicationState)

graph.add_node("resume_parser", parse_resume)
graph.add_node("evaluator", evaluate_candidate)
graph.add_node("messaging", send_email_node)

graph.add_edge(START, "resume_parser")
graph.add_edge("resume_parser", "evaluator")
graph.add_edge("evaluator", "messaging")
graph.add_edge("messaging", END)

workflow = graph.compile(checkpointer=MemorySaver())


# ----------------------------
# Test runner
# ----------------------------
async def run_graph():
    init_state = {
        "job_role": "AI Engineer",  # ✅ Add job role
        "job_description": """
        We are hiring an AI Engineer with expertise in Python, ML, DL (TensorFlow or PyTorch),
        NLP, and cloud deployment experience.
        """,
        "resume_text": """
        John Doe
        📍 Lagos, Nigeria | 📞 +234 814 123 4567 | ✉️ johndoe@email.com

        Professional Summary
        Software Engineer with 4 years experience in Python, FastAPI, React, 
        built ML models, deployed apps on AWS.

        Skills: Python, TensorFlow, React, AWS, Docker

        Experience:
        Software Engineer at TechCorp (2020-2024)
        - Built ML recommendation system
        - Deployed models on AWS
        """,
        # ✅ Initialize empty fields
        "parsed_resume": {},
        "evaluation": {},
        "email": {},
        "candidate_name": "",
        "candidate_email": ""
    }

    print("🚀 Starting workflow...")
    result = await workflow.ainvoke(
        init_state,
        config={"configurable": {"thread_id": "session-123"}}
    )

    print("\n📊 Final Results:")
    print(f"Candidate: {result['candidate_name']}")
    print(f"Score: {result['evaluation'].get('similarity_score', 'N/A')}/100")
    print(f"Email sent: {result['email'].get('subject', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(run_graph())