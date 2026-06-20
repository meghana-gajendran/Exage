"""
Consequence Ranker — Option 2 Agent

Takes the raw gap list and the learner's goal, and ranks gaps
by their consequence relative to that specific goal.

The same gap can have very different priority depending on context:

Example — "missing understanding of dbt testing":
- Interview prep → HIGH priority (commonly asked, signals maturity)
- Production deployment → CRITICAL (untested pipelines cause silent data errors)
- Teaching → MEDIUM (important but can be introduced gradually)
- General curiosity → LOW (interesting but not urgent)

IMPORTANT — domain_core vs general_practice gaps:
The Gap Detector tags each gap as "domain_core" (a core mechanism of what
this specific project IS) or "general_practice" (generic engineering hygiene
like testing/CI/logging that applies to any codebase).

For interview prep especially: candidates are almost always asked to explain
THEIR OWN PROJECT in depth. A shallow understanding of a domain_core mechanism
is something an interviewer is likely to probe directly and immediately expose.
Generic practice gaps (testing, CI, logging) are common across all candidates
and less likely to be the focus of deep follow-up questions about THIS project.

As a rule of thumb: domain_core gaps should rank above general_practice gaps
for interview prep and project-building goals, unless the domain_core gaps
are minor (nice-to-know severity) while a general_practice gap is critical.

The ranker doesn't just reorder — it also:
- Explains WHY each gap matters for the specific goal
- Generates a starter probing question for each gap
- Selects the top 3-5 to surface to the learner

This output feeds directly into the Option 1 chat as pre-loaded
session context — the gaps become the starting point for probing.
"""

import json
from chat_agents.base import call_llm

LEARNING_GOAL_CONTEXT = {
    "interview": "The learner is preparing for a technical interview. Prioritise gaps that are commonly tested in interviews, that signal engineering maturity, or that interviewers use to separate junior from senior candidates. Interviewers very often ask candidates to explain their own projects in depth — so shallow understanding of THIS project's core domain mechanisms is especially likely to be exposed.",
    "project": "The learner is building a production system. Prioritise gaps that could cause system failures, data corruption, silent errors, or production incidents. Gaps in the project's core domain mechanisms often have the highest blast radius.",
    "teaching": "The learner wants to teach this topic to others. Prioritise gaps in foundational concepts, mental models, and the ability to explain the 'why' behind decisions — especially for the core mechanisms that define this domain.",
    "exam": "The learner is preparing for an exam. Prioritise gaps in theoretical understanding, definitions, and canonical use cases.",
    "curiosity": "The learner wants to understand this topic more deeply. Prioritise gaps that unlock deeper understanding and reveal how things work under the hood — domain-core mechanisms are usually the most rewarding to explore.",
}

SYSTEM_PROMPT = """
You are ranking knowledge gaps by their consequence for a specific learning goal.

You will receive:
- A list of detected gaps, each tagged with severity and gap_category
  (domain_core = core mechanism of what this project IS,
   general_practice = generic engineering hygiene like testing/CI/logging)
- The learner's learning goal and its context
- The technology being studied
- The project's domain

Your job is to rerank and select the top 3-5 gaps that matter most
for THIS specific goal, and explain why.

RANKING PRINCIPLE:
domain_core gaps should generally rank ABOVE general_practice gaps for
interview prep and project-building goals. The reasoning: a candidate
explaining their own project will be asked to go deep on what they built,
and a shallow or missing understanding of a core mechanism will surface
immediately. Generic gaps like "no unit tests" are common across almost
every candidate and less differentiating.

Exception: if a general_practice gap is "critical" severity and all
domain_core gaps are "nice-to-know", the general_practice gap may rank higher.
But do not let easy-to-articulate generic gaps (testing, CI, logging) crowd
out the gaps that are actually distinctive to this project, unless the
domain_core gaps are genuinely well covered.

For each selected gap:
- Restate the gap clearly and specifically
- Explain why it's high consequence for the learner's goal
- Generate one strong probing question to surface this gap
- Rate urgency: immediate | soon | eventually

The probing question should:
- Not reveal the gap directly
- Invite the learner to demonstrate their understanding
- Feel like a natural question a colleague would ask
- Have no single "correct" answer — require genuine thinking
- For domain_core gaps, reference what they actually built (be specific to their implementation)

Output ONLY valid JSON:
{
  "learning_goal": "the goal as stated",
  "ranked_gaps": [
    {
      "rank": 1,
      "concept": "gap concept name",
      "gap_type": "missing | shallow",
      "gap_category": "domain_core | general_practice",
      "consequence_for_goal": "why this gap matters for their specific goal",
      "urgency": "immediate | soon | eventually",
      "probing_question": "the question to ask the learner",
      "what_a_good_answer_shows": "what understanding looks like"
    }
  ],
  "analysis_summary": "2-3 sentences on the overall gap picture for this learner given their goal, noting the balance between domain-specific and general gaps"
}

Select 3-5 gaps maximum. Prioritise ruthlessly — only include what truly matters for the goal.
"""


async def run_consequence_ranker(
    gaps: dict,
    learning_goal: str,
    frameworks: list[str],
) -> tuple[dict, int]:
    """
    Rank gaps by consequence for the learner's goal.

    Args:
        gaps: output from run_gap_detector_v2()
        learning_goal: "interview" | "project" | "teaching" | "exam" | "curiosity"
        frameworks: list of detected framework names

    Returns:
        (ranked_gaps_dict, latency_ms)
    """
    framework_hint = ", ".join(frameworks) if frameworks else "unknown"
    goal_context = LEARNING_GOAL_CONTEXT.get(
        learning_goal,
        "The learner wants to improve their understanding of this technology."
    )
    domain = gaps.get("domain", "")

    user_content = f"""
Technology: {framework_hint}
Project domain: {domain}
Learning goal: {learning_goal}
Goal context: {goal_context}

Detected gaps:
{json.dumps(gaps, indent=2)}

Rank these gaps by consequence for a learner whose goal is: {learning_goal}
Remember: domain_core gaps generally outrank general_practice gaps for this goal,
per the ranking principle in your instructions.
Select only the 3-5 most important gaps for this goal.
"""

    return await call_llm(SYSTEM_PROMPT, user_content, expect_json=True)
