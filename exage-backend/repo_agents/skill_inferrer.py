"""
Skill Inferrer — Option 2 Agent

Takes the concept list from the Concept Extractor and infers what
the learner likely understands — and at what depth.

The core insight: using a feature ≠ understanding it.

Signals of shallow understanding:
- Feature used in only one way (always the same pattern)
- No error handling around a feature
- Config values copied without variation (suggests cargo-culting)
- Feature used but related concepts missing (e.g. uses incremental but no merge strategy)
- No tests for critical transformations

Signals of deeper understanding:
- Feature used in multiple ways (different configurations, edge cases)
- Related concepts are also present (shows holistic understanding)
- Error handling or fallback logic present
- Documentation or comments that explain the *why*, not just the *what*
- Tests present for the feature

Output is a skill map: concept → inferred depth + reasoning.
This feeds directly into the Gap Detector.
"""

import json
from chat_agents.base import call_llm

SYSTEM_PROMPT = """
You are an expert at inferring technical understanding from code artifacts.

You will receive a list of concepts observed in a codebase.
Your job is to infer what the developer who wrote this code likely understands
about each concept — and at what depth.

This is NOT code review. You are NOT looking for bugs or improvements.
You are trying to understand the mental model behind the code.

Depth levels:
- "surface": knows the syntax and basic usage, but likely doesn't understand why it works
- "functional": understands how to use it correctly in standard scenarios
- "deep": understands edge cases, trade-offs, and underlying mechanisms

Signals to look for:
- Used in only one way → surface
- Multiple configurations or patterns → functional to deep
- Related concepts also present → deeper understanding
- Conspicuous absence of related concepts → gap in mental model
- Copy-paste patterns with no variation → surface
- Evidence of debugging or edge case handling → deep

For each concept, produce:
- concept: the concept name
- inferred_depth: "surface" | "functional" | "deep"
- confidence: "high" | "medium" | "low" (how confident you are in your inference)
- reasoning: one sentence explaining what evidence led to this inference
- related_gap: the most likely gap adjacent to this concept (what they probably don't know yet)

Output ONLY valid JSON:
{
  "skill_map": [
    {
      "concept": "concept name",
      "inferred_depth": "surface | functional | deep",
      "confidence": "high | medium | low",
      "reasoning": "one sentence",
      "related_gap": "what they probably don't understand yet about this concept"
    }
  ],
  "overall_assessment": "2-3 sentences describing the learner's overall level with this technology",
  "strongest_areas": ["concept 1", "concept 2"],
  "weakest_signals": ["concept 1", "concept 2"]
}
"""


async def run_skill_inferrer(
    extracted_concepts: dict,
    frameworks: list[str],
) -> tuple[dict, int]:
    """
    Infer understanding depth from extracted concepts.

    Args:
        extracted_concepts: output dict from run_concept_extractor_v2()
        frameworks: list of detected framework names

    Returns:
        (skill_map_dict, latency_ms)
    """
    framework_hint = ", ".join(frameworks) if frameworks else "unknown"

    concepts_json = json.dumps(extracted_concepts, indent=2)

    user_content = f"""
Technology context: {framework_hint}

Concepts observed in the codebase:
{concepts_json}

Based on these observations, infer what the developer likely understands
about each concept and at what depth.

Remember: you are inferring mental models from code artifacts,
not reviewing code quality.
"""

    return await call_llm(SYSTEM_PROMPT, user_content, expect_json=True)
