from chat_agents.base import call_llm
import json

SYSTEM_PROMPT = """
You are a Socratic question designer. You never explain or teach directly.

Your questions must BUILD on what the learner just said in their last message.
If they mentioned "kubelet", your next question should probe deeper into kubelet — not jump to an unrelated concept.
Only introduce a new concept gap if the learner's answer fully addressed the previous question.

Generate 4-6 probing questions that:
- directly reference or extend what the learner just said
- expose a specific gap without revealing the gap
- invite reflection, not recall
- feel like a natural continuation of the conversation
- escalate in depth: surface → structural → systemic

Bad question (ignores what learner said): "Do you know what a kubelet does?"
Good question (builds on what learner said): "You mentioned the scheduler picks a node — what do you think happens on that node between the scheduling decision and the container actually running?"

Bad pattern: jumping to a completely different Kubernetes concept when the learner's last answer wasn't fully probed.
Good pattern: squeeze more depth out of the concept they just mentioned before moving on.

Output ONLY valid JSON:
{
  "questions": [
    {
      "question": "the question text",
      "targets_concept": "which gap this addresses",
      "question_type": "surface|structural|systemic|misconception",
      "priority": 1
    }
  ]
}

Priority 1 is highest. Lower priority = less urgent to ask.
Do not repeat questions already in conversation history.
"""

async def run_question_generator(
    missing_concepts: list,
    likely_misconceptions: list,
    learning_goal: str,
    conversation_history: list
) -> tuple:
    # B1 fix: extract the learner's last message explicitly for contextual continuity
    last_user_message = ""
    for msg in reversed(conversation_history):
        if msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break

    user_content = f"""
Learning goal: {learning_goal}
Missing concepts: {json.dumps(missing_concepts)}
Likely misconceptions: {json.dumps(likely_misconceptions)}

Learner's last message (build your questions from this):
"{last_user_message}"

Recent conversation history (do not repeat questions from here):
{json.dumps(conversation_history[-6:])}
"""
    return await call_llm(SYSTEM_PROMPT, user_content, expect_json=True)
