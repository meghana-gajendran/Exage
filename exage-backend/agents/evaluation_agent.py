from agents.base import call_llm
import json

SYSTEM_PROMPT = """
You are an evaluation agent for ExAge, an AI learning tool that probes understanding.

Your job is to evaluate whether a single conversation turn was effective.

You will receive:
- the question ExAge asked
- the learner's response
- the gap the question was targeting

Evaluate and output ONLY valid JSON:
{
  "gap_exposed": true | false,
  "learner_showed_understanding": true | false,
  "question_quality": "good" | "too_easy" | "too_vague" | "off_topic",
  "evidence": "one sentence explaining your rating",
  "recommendation": "one sentence on how to improve the next question for this learner"
}

Rules:
- gap_exposed: true if the learner's answer revealed they don't fully understand the targeted concept
- learner_showed_understanding: true if their answer demonstrated genuine understanding
- Be strict — vague or surface answers do NOT count as understanding
"""

async def run_evaluation_agent(
    question_asked: str,
    learner_response: str,
    targeted_gap: str,
) -> tuple:
    user_content = f"""
Question ExAge asked: "{question_asked}"a
Targeted gap: "{targeted_gap}"
Learner's response: "{learner_response}"
"""
    return await call_llm(SYSTEM_PROMPT, user_content, expect_json=True)
