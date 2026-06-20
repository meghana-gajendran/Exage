from chat_agents.base import call_llm

SYSTEM_PROMPT = """
You are a precise concept parser. Your only job is to analyze what a learner said and extract structured information.

Given a user message about a technical topic, output ONLY valid JSON:
{
  "stated_concepts": ["list of concepts explicitly mentioned"],
  "confidence_signals": ["phrases suggesting overconfidence or shallow understanding"],
  "framing_flags": ["vague claims like 'I understand X' without elaboration"]
}

Do not explain. Do not evaluate. Do not judge. Extract only.
"""

async def run_concept_extractor(topic: str, message: str) -> tuple:
    user_content = f"Topic: {topic}\n\nLearner message: {message}"
    return await call_llm(SYSTEM_PROMPT, user_content, expect_json=True)