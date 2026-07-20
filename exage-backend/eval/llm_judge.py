"""
LLM-as-judge eval for curiosity breaker anecdotes.

Uses a second LLM call to grade the anecdote on a rubric.
Run less frequently than objective evals — costs API calls.

The judge is given:
- The anecdote to grade
- The input context (concept, goal, domain)
- The rubric dimensions and what each means
- An example of an acceptable and unacceptable anecdote for calibration

The judge scores each dimension 1-5 and explains its reasoning.
"""

import json
from dataclasses import dataclass
from chat_agents.base import call_llm


JUDGE_SYSTEM_PROMPT = """
You are an expert evaluator for an AI learning tool called ExAge.

ExAge shows learners short "curiosity breaker" scenarios before Socratic questioning begins.
A curiosity breaker should make the learner ask "why did that happen?" — without explaining it.

You will be given:
- A curiosity breaker anecdote to evaluate
- The context it was generated for (concept, learning goal, domain)
- An example of an acceptable anecdote (for calibration)
- An example of an unacceptable anecdote (for calibration)

Score the anecdote on 5 dimensions, each from 1 to 5:

1. curiosity (1-5)
   5 = strongly makes you want to know why
   1 = no curiosity created at all

2. relevance (1-5)
   5 = clearly about the identified knowledge gap
   1 = unrelated to the gap

3. realism (1-5)
   5 = could plausibly happen in a real system or interview
   1 = unrealistic or contrived

4. non_explanatory (1-5)
   5 = completely avoids explaining the gap or hinting at the answer
   1 = directly explains the concept or gives away the solution

5. goal_alignment (1-5)
   5 = perfectly matches the learner's stated goal (interview/production/teaching/etc)
   1 = completely ignores the learning goal

Output ONLY valid JSON:
{
  "curiosity": <1-5>,
  "relevance": <1-5>,
  "realism": <1-5>,
  "non_explanatory": <1-5>,
  "goal_alignment": <1-5>,
  "total": <sum of all 5>,
  "reasoning": "2-3 sentences explaining the scores",
  "strongest_aspect": "what the anecdote does best",
  "weakest_aspect": "what most needs improvement"
}
"""


@dataclass
class LLMJudgeResult:
    curiosity: int
    relevance: int
    realism: int
    non_explanatory: int
    goal_alignment: int
    total: int
    reasoning: str
    strongest_aspect: str
    weakest_aspect: str
    passed: bool
    threshold: int
    latency_ms: int


async def run_llm_judge(
    anecdote: str,
    concept: str,
    learning_goal: str,
    domain: str,
    example_acceptable: str,
    example_unacceptable: str,
    thresholds: dict | None = None,
) -> LLMJudgeResult:
    """
    Grade an anecdote using an LLM judge.

    Args:
        anecdote: the generated anecdote to evaluate
        concept: the gap concept (e.g. "dbt testing strategy")
        learning_goal: "interview" | "production" | "teaching" | "exam" | "curiosity"
        domain: the project domain
        example_acceptable: a known-good reference anecdote
        example_unacceptable: a known-bad reference anecdote
        thresholds: optional override from test_cases.py

    Returns:
        LLMJudgeResult with scores and pass/fail
    """
    cfg = thresholds or {}
    total_minimum = cfg.get("total_minimum", 18)

    user_content = f"""
Context:
- Knowledge gap: {concept}
- Learning goal: {learning_goal}
- Domain: {domain}

Anecdote to evaluate:
\"\"\"{anecdote}\"\"\"

For calibration:
ACCEPTABLE example (what a good anecdote looks like):
\"\"\"{example_acceptable}\"\"\"

UNACCEPTABLE example (what a bad anecdote looks like):
\"\"\"{example_unacceptable}\"\"\"

Grade the anecdote to evaluate on all 5 dimensions.
"""

    result_dict, latency = await call_llm(
        system_prompt=JUDGE_SYSTEM_PROMPT,
        user_content=user_content,
        expect_json=True,
    )

    total = result_dict.get("total", sum([
        result_dict.get("curiosity", 0),
        result_dict.get("relevance", 0),
        result_dict.get("realism", 0),
        result_dict.get("non_explanatory", 0),
        result_dict.get("goal_alignment", 0),
    ]))

    return LLMJudgeResult(
        curiosity=result_dict.get("curiosity", 0),
        relevance=result_dict.get("relevance", 0),
        realism=result_dict.get("realism", 0),
        non_explanatory=result_dict.get("non_explanatory", 0),
        goal_alignment=result_dict.get("goal_alignment", 0),
        total=total,
        reasoning=result_dict.get("reasoning", ""),
        strongest_aspect=result_dict.get("strongest_aspect", ""),
        weakest_aspect=result_dict.get("weakest_aspect", ""),
        passed=total >= total_minimum,
        threshold=total_minimum,
        latency_ms=latency,
    )


def format_judge_result(result: LLMJudgeResult) -> str:
    """Human-readable summary of the LLM judge result."""
    lines = []
    lines.append(f"LLM judge: {'PASS' if result.passed else 'FAIL'} ({result.total}/{result.threshold} threshold)")
    lines.append(f"  Curiosity:        {result.curiosity}/5")
    lines.append(f"  Relevance:        {result.relevance}/5")
    lines.append(f"  Realism:          {result.realism}/5")
    lines.append(f"  Non-explanatory:  {result.non_explanatory}/5")
    lines.append(f"  Goal alignment:   {result.goal_alignment}/5")
    lines.append(f"  Total:            {result.total}/25")
    lines.append(f"  Reasoning: {result.reasoning}")
    lines.append(f"  Strongest: {result.strongest_aspect}")
    lines.append(f"  Weakest:   {result.weakest_aspect}")
    return "\n".join(lines)
