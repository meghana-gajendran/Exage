from agents.base import call_llm
import json

SYSTEM_PROMPT = """
You are a concept graph analyst. You understand the given topic deeply.

You will be given:
- stated_concepts: what the learner claims to know
- learning_goal: why they are studying this
- asked_gaps: gaps already probed in this session

Your job is to identify what the learner is NOT saying that they should know, given their stated goal.

Output ONLY valid JSON:
{
  "missing_concepts": [
    {
      "concept": "name",
      "severity": "critical|important|nice-to-know",
      "why_it_matters_for_goal": "one sentence"
    }
  ],
  "likely_misconceptions": [
    {
      "concept": "name",
      "probable_misunderstanding": "what they likely think vs what is true"
    }
  ]
}

Do not probe. Do not explain. Identify only.
Exclude any concepts already in asked_gaps.
"""

async def run_gap_detector(topic: str, stated_concepts: list, learning_goal: str, asked_gaps: list) -> tuple:
    user_content = f"""
Topic: {topic}
Learning goal: {learning_goal}
Stated concepts: {json.dumps(stated_concepts)}
Already asked gaps (exclude these): {json.dumps(asked_gaps)}
"""
    return await call_llm(SYSTEM_PROMPT, user_content, expect_json=True)