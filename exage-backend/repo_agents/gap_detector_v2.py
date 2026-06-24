"""
Gap Detector — Option 2 Agent

Takes the skill map from the Skill Inferrer and identifies gaps:
concepts that are missing entirely, or present but at dangerously
shallow depth for the technology being used.

Unlike Option 1's gap detector (which works from self-reported knowledge),
this one works from inferred knowledge — which is more honest and harder
to game.

Two types of gaps:
1. Missing concepts — things a practitioner should know that don't appear at all
2. Shallow concepts — things that appear but show surface-level understanding
   when deeper understanding is typically required

The detector uses the technology context to know what the full concept
graph looks like. "What should someone working with dbt know?" is different
from "What should someone working with Kubernetes know?"

IMPORTANT — domain depth vs generic hygiene:
Generic software engineering gaps (testing, CI, logging, error handling)
are easy to spot because they're conspicuously absent and easy to articulate.
But they apply to almost any codebase and don't reflect what's distinctive
about THIS project.

Domain-specific gaps — shallow or missing understanding of the core
mechanisms that define what this project actually IS — are usually more
revealing of the learner's mental model and more valuable to probe.
"""

import json
from chat_agents.base import call_llm

SYSTEM_PROMPT = """
You are an expert in identifying knowledge gaps from code artifacts.

You will receive:
- A skill map: concepts observed in a codebase with inferred understanding depth
- The technology/framework context
- Absent concepts: things conspicuously missing

Your job is to identify the most significant gaps in the developer's mental model.

Two types of gaps to find:

TYPE 1 — MISSING CONCEPTS
Concepts that any practitioner of this technology should know,
but that don't appear in the codebase at all.
Example: A dbt project with no tests suggests the developer
may not understand why testing matters in data pipelines.

TYPE 2 — SHALLOW CONCEPTS
Concepts that appear in the code but at surface depth,
where deeper understanding is typically required.
Example: Uses incremental models but only with unique_key —
suggests they don't understand merge strategies or on_schema_change.

CRITICAL — PRIORITISE DOMAIN DEPTH OVER GENERIC HYGIENE:

First, identify what DOMAIN this project belongs to based on the framework_context
and structural observations. Examples of domains: container runtimes, data
pipelines, web APIs, distributed systems, compilers, ML training pipelines.

For that domain, think about the CORE MECHANISMS that define what this project
actually IS — the concepts that, if misunderstood, mean the developer doesn't
really understand what they built. Examples:
- Container runtime → namespace isolation (all types, not just one), cgroups,
  filesystem layering/overlayfs, networking isolation, security boundaries
- Data pipeline → lineage/DAG resolution, idempotency, schema evolution,
  data quality guarantees
- Web API → request lifecycle, auth/session boundaries, concurrency model,
  error propagation

Generic engineering hygiene gaps (unit testing, CI, logging, error handling,
environment variable management) are valid but SECONDARY. Include them only if:
(a) the domain-specific gaps are already well covered by the codebase, OR
(b) the hygiene gap is so severe it would be negligent not to mention it.

When in doubt, a SHALLOW understanding of a CORE DOMAIN MECHANISM is more
significant than a MISSING generic practice. A developer who built a
container runtime but only superficially understands namespace isolation
has a more revealing gap than one who simply hasn't written tests yet.

For each gap:
- Be specific about WHAT is missing or shallow
- Explain WHY it matters (what goes wrong without this understanding)
- Rate severity: critical | important | nice-to-know
- Note what the learner probably thinks vs what is actually true
- Mark whether this is a "domain_core" gap or a "general_practice" gap

Output ONLY valid JSON:
{
  "domain": "one or two words identifying the project's technical domain",
  "gaps": [
    {
      "concept": "specific concept name",
      "gap_type": "missing | shallow",
      "gap_category": "domain_core | general_practice",
      "severity": "critical | important | nice-to-know",
      "what_is_missing": "specific description of the gap",
      "why_it_matters": "what goes wrong without this understanding",
      "probable_misconception": "what the learner probably thinks is true",
      "actual_truth": "what they need to understand"
    }
  ],
  "technology_coverage_score": 0-100,
  "coverage_note": "one sentence on overall coverage of the technology"
}

Focus on the 5-8 most significant gaps, with domain_core gaps given priority
when the project clearly belongs to a specific technical domain.
"""


async def run_gap_detector_v2(
    skill_map: dict,
    extracted_concepts: dict,
    frameworks: list[str],
) -> tuple[dict, int]:
    """
    Detect gaps from the skill map.

    Args:
        skill_map: output from run_skill_inferrer()
        extracted_concepts: output from run_concept_extractor_v2()
        frameworks: list of detected framework names

    Returns:
        (gap_dict, latency_ms)
    """
    framework_hint = ", ".join(frameworks) if frameworks else "unknown"

    user_content = f"""
Technology context: {framework_hint}

Skill map (inferred understanding from code):
{json.dumps(skill_map, indent=2)}

Concepts observed (including absent ones):
{json.dumps(extracted_concepts, indent=2)}

First, identify the technical DOMAIN this project belongs to (look at the
framework_context and structural_observations for clues — e.g. is this a
container runtime, a data pipeline, a web API, etc?).

Then identify the most significant gaps in this developer's mental model,
prioritising domain-core mechanisms over generic engineering hygiene
as described in your instructions.
"""

    return await call_llm(SYSTEM_PROMPT, user_content, expect_json=True)
