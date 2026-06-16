"""
Concept Extractor — Option 2 Agent

Takes a formatted repo summary string and extracts every concept,
pattern, and abstraction that is actually present in the code.

This agent does NOT infer understanding depth — that's the Skill Inferrer's job.
It only answers: what is here?

Key distinction from Option 1's concept extractor:
- Option 1: extracts concepts from what a learner *says*
- Option 2: extracts concepts from what a learner *built*

The output is deliberately granular. "dbt" is not a concept —
"incremental materialisation with unique_key strategy" is a concept.
"""

import json
from agents.base import call_llm

SYSTEM_PROMPT = """
You are a senior engineer doing a technical concept inventory of a codebase.

Your job is to read repository files and identify every technical concept,
pattern, abstraction, and practice that is demonstrably present in the code.

Rules:
- Only report what you can directly observe in the provided files
- Be specific — not "uses dbt" but "uses dbt incremental materialisation"
- Not "writes SQL" but "uses CTEs with multiple transformation layers"
- Not "has tests" but "uses dbt schema tests with not_null and unique constraints"
- If something is conspicuously absent (e.g. a dbt project with no tests), note it
- Do not infer intent — only observe evidence

For each concept, provide:
- concept: the specific technical concept name
- category: which area it belongs to (e.g. "data modelling", "testing", "orchestration")
- evidence: the specific file or code pattern that demonstrates it
- usage_count: how many times it appears (approximate — "1", "2-5", "5+")
- present: true if used, false if conspicuously absent

Output ONLY valid JSON:
{
  "framework_context": "one sentence describing what kind of project this is",
  "concepts": [
    {
      "concept": "specific concept name",
      "category": "category name",
      "evidence": "file path or code snippet that demonstrates this",
      "usage_count": "1 | 2-5 | 5+",
      "present": true
    }
  ],
  "absent_concepts": [
    {
      "concept": "concept name",
      "category": "category name",
      "reason": "why this is notable to be missing"
    }
  ],
  "structural_observations": [
    "one observation per item about the overall project structure"
  ]
}
"""


async def run_concept_extractor_v2(
    repo_summary_text: str,
    frameworks: list[str],
) -> tuple[dict, int]:
    """
    Extract concepts from a formatted repo summary.

    Args:
        repo_summary_text: output of format_summary_for_llm()
        frameworks: list of detected framework names e.g. ["dbt", "Python"]

    Returns:
        (extracted_concepts_dict, latency_ms)
    """
    framework_hint = ", ".join(frameworks) if frameworks else "unknown"

    user_content = f"""
Detected technologies in this repository: {framework_hint}

Repository content for analysis:
{repo_summary_text}

Extract every technical concept you can observe in the code above.
Be specific and granular. Focus on what the code actually does, not what it could do.
"""

    return await call_llm(SYSTEM_PROMPT, user_content, expect_json=True)
