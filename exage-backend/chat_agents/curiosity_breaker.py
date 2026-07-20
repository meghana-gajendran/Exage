"""
Curiosity Breaker Agent

Takes a detected gap, learning goal, and repo context and generates
a short realistic anecdote that makes the learner curious about the gap
WITHOUT explaining or hinting at the answer.

The anecdote is shown BEFORE Socratic questioning begins.
Its only job is to create genuine curiosity — not to teach.

Design principle:
- A good anecdote makes the learner ask "why did that happen?"
- A bad anecdote explains "this happened because of X"
"""

from chat_agents.base import call_llm

SYSTEM_PROMPT = """
You are writing a short scenario for a learning tool called ExAge.

Your job is to write a single realistic anecdote that shows the CONSEQUENCE
of a knowledge gap — without explaining the gap or its solution.

The learner will read this scenario and feel curious about why it happened.
That curiosity is what motivates them to explore the gap through Socratic questioning.

Rules:
- Write a scenario, not an explanation
- Include at least one concrete detail (a number, a name, a specific event)
- Do NOT explain why the problem happened
- Do NOT suggest a solution or hint at the answer
- End the scenario before resolving it — leave it open
- Keep it between 40 and 150 words
- Write in second person ("you") or third person — whichever feels more natural
- Match the tone to the learning goal:
  - interview: frame it as something an interviewer asked or exposed
  - production: frame it as something that happened in a real system
  - teaching: frame it as something a student or colleague misunderstood
  - exam: frame it as a question you couldn't answer
  - curiosity: frame it as something surprising you encountered

Output ONLY the anecdote text. No title, no label, no explanation.
"""


async def run_curiosity_breaker(
    concept: str,
    learning_goal: str,
    domain: str,
    repo_context: str,
) -> tuple[str, int]:
    """
    Generate one curiosity breaker anecdote for a specific gap.

    Args:
        concept: the gap concept (e.g. "dbt testing strategy")
        learning_goal: "interview" | "production" | "teaching" | "exam" | "curiosity"
        domain: the project domain (e.g. "data pipeline")
        repo_context: brief description of what the repo does

    Returns:
        (anecdote_text, latency_ms)
    """
    user_content = f"""
Learning goal: {learning_goal}
Domain: {domain}
Repository context: {repo_context}
Knowledge gap to create curiosity about: {concept}

Write a short realistic scenario that would make someone curious
about "{concept}" without explaining what it is or how to fix it.
"""

    return await call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_content=user_content,
        expect_json=False,
    )
