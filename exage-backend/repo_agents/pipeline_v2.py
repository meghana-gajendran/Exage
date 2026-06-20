"""
Option 2 pipeline runner — Phases 1, 2, and 3.

Chains:
  Repo Ingester
    → Concept Extractor
      → Skill Inferrer
        → Gap Detector
          → Consequence Ranker

Input: repo path or GitHub URL + learning goal
Output: RepoAnalysisResult with ranked gaps and probing questions

The ranked gaps feed directly into the Option 1 chat as
pre-loaded session state — skipping onboarding and going
straight to probing.
"""

from dataclasses import dataclass, field
from typing import Optional

from repo_analysis.ingester import ingest_repo, format_summary_for_llm
from repo_analysis.ingesters.local_ingester import RepoSummary
from repo_agents.concept_extractor_v2 import run_concept_extractor_v2
from repo_agents.skill_inferrer import run_skill_inferrer
from repo_agents.gap_detector_v2 import run_gap_detector_v2
from repo_agents.consequence_ranker import run_consequence_ranker


@dataclass
class RankedGap:
    rank: int
    concept: str
    gap_type: str                  # "missing" | "shallow"
    gap_category: str              # "domain_core" | "general_practice"
    consequence_for_goal: str
    urgency: str                   # "immediate" | "soon" | "eventually"
    probing_question: str
    what_a_good_answer_shows: str


@dataclass
class RepoAnalysisResult:
    repo_name: str
    input_type: str
    learning_goal: str
    frameworks: list[str]
    framework_context: str
    domain: str
    overall_assessment: str
    strongest_areas: list[str]
    weakest_signals: list[str]
    ranked_gaps: list[RankedGap]
    analysis_summary: str
    technology_coverage_score: int
    # Raw agent outputs for debugging
    extracted_concepts: dict = field(default_factory=dict)
    skill_map: dict = field(default_factory=dict)
    raw_gaps: dict = field(default_factory=dict)
    agent_traces: list[dict] = field(default_factory=list)
    error: Optional[str] = None


async def run_option2_pipeline(
    repo_input: str,
    learning_goal: str = "curiosity",
    github_token: Optional[str] = None,
) -> RepoAnalysisResult:
    """
    Run the full Phase 1+2+3 pipeline.

    Args:
        repo_input: local folder path or GitHub URL
        learning_goal: "interview" | "project" | "teaching" | "exam" | "curiosity"
        github_token: optional GitHub personal access token

    Returns:
        RepoAnalysisResult with ranked gaps and probing questions
    """

    # ── Phase 1: Repo Ingestion ─────────────────────────────────────
    summary: RepoSummary = ingest_repo(repo_input, github_token)

    if summary.error:
        return RepoAnalysisResult(
            repo_name=summary.repo_name,
            input_type=summary.input_type,
            learning_goal=learning_goal,
            frameworks=[],
            framework_context="",
            domain="",
            overall_assessment="",
            strongest_areas=[],
            weakest_signals=[],
            ranked_gaps=[],
            analysis_summary="",
            technology_coverage_score=0,
            error=summary.error,
        )

    framework_names = [fw.name for fw in summary.frameworks]
    repo_text = format_summary_for_llm(summary)
    traces = []

    # ── Phase 2a: Concept Extraction ────────────────────────────────
    extracted, latency = await run_concept_extractor_v2(repo_text, framework_names)
    traces.append({
        "agent": "concept_extractor_v2",
        "latency_ms": latency,
        "concepts_found": len(extracted.get("concepts", [])),
        "absent_found": len(extracted.get("absent_concepts", [])),
    })

    # ── Phase 2b: Skill Inference ────────────────────────────────────
    skill_result, latency = await run_skill_inferrer(extracted, framework_names)
    traces.append({
        "agent": "skill_inferrer",
        "latency_ms": latency,
        "skill_map_count": len(skill_result.get("skill_map", [])),
    })

    # ── Phase 3a: Gap Detection ──────────────────────────────────────
    gaps_result, latency = await run_gap_detector_v2(
        skill_map=skill_result,
        extracted_concepts=extracted,
        frameworks=framework_names,
    )
    traces.append({
        "agent": "gap_detector_v2",
        "latency_ms": latency,
        "gaps_found": len(gaps_result.get("gaps", [])),
        "coverage_score": gaps_result.get("technology_coverage_score", 0),
        "domain": gaps_result.get("domain", ""),
    })

    # ── Phase 3b: Consequence Ranking ────────────────────────────────
    ranked_result, latency = await run_consequence_ranker(
        gaps=gaps_result,
        learning_goal=learning_goal,
        frameworks=framework_names,
    )
    traces.append({
        "agent": "consequence_ranker",
        "latency_ms": latency,
        "ranked_gaps_count": len(ranked_result.get("ranked_gaps", [])),
    })

    # Parse ranked gaps into dataclass objects
    ranked_gaps = [
        RankedGap(
            rank=g.get("rank", i + 1),
            concept=g.get("concept", ""),
            gap_type=g.get("gap_type", "missing"),
            gap_category=g.get("gap_category", "general_practice"),
            consequence_for_goal=g.get("consequence_for_goal", ""),
            urgency=g.get("urgency", "soon"),
            probing_question=g.get("probing_question", ""),
            what_a_good_answer_shows=g.get("what_a_good_answer_shows", ""),
        )
        for i, g in enumerate(ranked_result.get("ranked_gaps", []))
    ]

    return RepoAnalysisResult(
        repo_name=summary.repo_name,
        input_type=summary.input_type,
        learning_goal=learning_goal,
        frameworks=framework_names,
        framework_context=extracted.get("framework_context", ""),
        domain=gaps_result.get("domain", ""),
        overall_assessment=skill_result.get("overall_assessment", ""),
        strongest_areas=skill_result.get("strongest_areas", []),
        weakest_signals=skill_result.get("weakest_signals", []),
        ranked_gaps=ranked_gaps,
        analysis_summary=ranked_result.get("analysis_summary", ""),
        technology_coverage_score=gaps_result.get("technology_coverage_score", 0),
        extracted_concepts=extracted,
        skill_map=skill_result,
        raw_gaps=gaps_result,
        agent_traces=traces,
    )


def format_result_for_display(result: RepoAnalysisResult) -> str:
    """Format the full analysis result for human-readable display."""
    if result.error:
        return f"Error analysing repository: {result.error}"

    lines = []
    lines.append(f"Repository: {result.repo_name}")
    lines.append(f"Technologies: {', '.join(result.frameworks)}")
    if result.domain:
        lines.append(f"Domain: {result.domain}")
    lines.append(f"Goal: {result.learning_goal}")
    lines.append("")
    lines.append(result.framework_context)
    lines.append("")

    if result.strongest_areas:
        lines.append("Likely strong:")
        for area in result.strongest_areas:
            lines.append(f"  ● {area}")
        lines.append("")

    if result.ranked_gaps:
        lines.append(f"Top gaps for {result.learning_goal}:")
        for gap in result.ranked_gaps:
            urgency_marker = "●" if gap.urgency == "immediate" else "○"
            category_tag = "[core]" if gap.gap_category == "domain_core" else "[general]"
            lines.append(f"  {urgency_marker} {gap.concept} [{gap.urgency}] {category_tag}")
            lines.append(f"    {gap.consequence_for_goal}")
        lines.append("")

    lines.append("Analysis:")
    lines.append(result.analysis_summary)

    return "\n".join(lines)


def result_to_session_context(result: RepoAnalysisResult) -> dict:
    """
    Convert the analysis result into Option 1 session context.

    This is what gets injected into the chat session when the learner
    clicks 'Start probing' — it pre-loads the gaps so Option 1
    skips onboarding and goes straight to probing.
    """
    if result.domain:
        tech_hint = ", ".join(result.frameworks) if result.frameworks else result.repo_name
        topic = f"{result.domain} ({tech_hint})"
    else:
        topic = ", ".join(result.frameworks) if result.frameworks else result.repo_name

    return {
        "topic": topic,
        "learning_goal": result.learning_goal,
        "phase": "probing",
        "known_concepts": result.strongest_areas,
        "open_gaps": [
            {
                "concept": gap.concept,
                "severity": "critical" if gap.urgency == "immediate" else "important",
                "why_it_matters_for_goal": gap.consequence_for_goal,
            }
            for gap in result.ranked_gaps
        ],
        "asked_gaps": [],
        "misconceptions": [],
        "repo_context": {
            "repo_name": result.repo_name,
            "domain": result.domain,
            "framework_context": result.framework_context,
            "overall_assessment": result.overall_assessment,
            "probing_questions": [
                gap.probing_question for gap in result.ranked_gaps
            ],
        }
    }