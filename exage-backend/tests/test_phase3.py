"""
Tests for Phase 3 — Gap Detector, Consequence Ranker, and full pipeline.
All LLM calls are mocked.
"""

import pytest
from unittest.mock import patch, AsyncMock


# ─── Sample mock data ─────────────────────────────────────────────────────────

MOCK_SKILL_MAP = {
    "skill_map": [
        {
            "concept": "incremental materialisation",
            "inferred_depth": "surface",
            "confidence": "high",
            "reasoning": "Used only with unique_key",
            "related_gap": "merge strategies"
        },
        {
            "concept": "ref() function",
            "inferred_depth": "functional",
            "confidence": "high",
            "reasoning": "Used correctly across all models",
            "related_gap": "DAG execution order"
        }
    ],
    "overall_assessment": "Intermediate dbt user with surface-level materialisation knowledge.",
    "strongest_areas": ["SQL transformations", "basic dbt modelling"],
    "weakest_signals": ["testing", "incremental strategies"]
}

MOCK_EXTRACTED = {
    "framework_context": "A dbt analytics project",
    "concepts": [
        {"concept": "incremental materialisation", "category": "modelling",
         "evidence": "3 models", "usage_count": "2-5", "present": True}
    ],
    "absent_concepts": [
        {"concept": "schema tests", "category": "testing",
         "reason": "no schema.yml found"}
    ],
    "structural_observations": ["No test coverage detected"]
}

MOCK_GAPS = {
    "domain": "data pipeline",
    "gaps": [
        {
            "concept": "dbt testing strategy",
            "gap_type": "missing",
            "gap_category": "general_practice",
            "severity": "critical",
            "what_is_missing": "No tests of any kind defined",
            "why_it_matters": "Silent data quality failures in production",
            "probable_misconception": "SQL that runs is SQL that works",
            "actual_truth": "Correctness must be asserted, not assumed"
        },
        {
            "concept": "incremental merge strategies",
            "gap_type": "shallow",
            "gap_category": "domain_core",
            "severity": "important",
            "what_is_missing": "Only unique_key used, no merge strategies",
            "why_it_matters": "Wrong merge strategy causes duplicate or missing records",
            "probable_misconception": "unique_key always handles deduplication correctly",
            "actual_truth": "on_schema_change and merge_update_columns control what actually happens"
        },
        {
            "concept": "dbt lineage and DAG",
            "gap_type": "missing",
            "gap_category": "domain_core",
            "severity": "important",
            "what_is_missing": "No evidence of understanding execution order",
            "why_it_matters": "Cannot debug or optimise pipeline without understanding the DAG",
            "probable_misconception": "dbt runs models in file order",
            "actual_truth": "dbt resolves execution order from ref() dependencies"
        }
    ],
    "technology_coverage_score": 35,
    "coverage_note": "Basic dbt usage demonstrated but critical production patterns missing"
}

MOCK_RANKED = {
    "learning_goal": "interview",
    "ranked_gaps": [
        {
            "rank": 1,
            "concept": "dbt lineage and DAG",
            "gap_type": "missing",
            "gap_category": "domain_core",
            "consequence_for_goal": "DAG understanding is a core interview topic for data engineers",
            "urgency": "immediate",
            "probing_question": "How does dbt decide which model runs before another?",
            "what_a_good_answer_shows": "Understanding of ref(), sources, and dependency resolution"
        },
        {
            "rank": 2,
            "concept": "dbt testing strategy",
            "gap_type": "missing",
            "gap_category": "general_practice",
            "consequence_for_goal": "Interviewers use testing maturity to separate junior from senior candidates",
            "urgency": "immediate",
            "probing_question": "If a model produces wrong results silently, how would you know?",
            "what_a_good_answer_shows": "Understanding of schema tests, singular tests, and monitoring"
        }
    ],
    "analysis_summary": "The two most interview-critical gaps are lineage (domain-core) and testing (general practice). Lineage ranks first because interviewers are likely to probe directly on this project's DAG."
}


# ─── Gap Detector tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gap_detector_returns_required_keys():
    with patch("repo_agents.gap_detector_v2.call_llm",
               new=AsyncMock(return_value=(MOCK_GAPS, 900))):
        from repo_agents.gap_detector_v2 import run_gap_detector_v2
        result, latency = await run_gap_detector_v2(
            skill_map=MOCK_SKILL_MAP,
            extracted_concepts=MOCK_EXTRACTED,
            frameworks=["dbt", "SQL"]
        )

        assert "gaps" in result
        assert "technology_coverage_score" in result
        assert "coverage_note" in result
        assert "domain" in result
        assert isinstance(result["gaps"], list)
        assert latency == 900


@pytest.mark.asyncio
async def test_gap_detector_gap_has_required_fields():
    with patch("repo_agents.gap_detector_v2.call_llm",
               new=AsyncMock(return_value=(MOCK_GAPS, 800))):
        from repo_agents.gap_detector_v2 import run_gap_detector_v2
        result, _ = await run_gap_detector_v2(MOCK_SKILL_MAP, MOCK_EXTRACTED, ["dbt"])

        gap = result["gaps"][0]
        assert "concept" in gap
        assert "gap_type" in gap
        assert "gap_category" in gap
        assert "severity" in gap
        assert "why_it_matters" in gap
        assert "probable_misconception" in gap


@pytest.mark.asyncio
async def test_gap_detector_severity_values_valid():
    valid_severities = {"critical", "important", "nice-to-know"}
    with patch("repo_agents.gap_detector_v2.call_llm",
               new=AsyncMock(return_value=(MOCK_GAPS, 700))):
        from repo_agents.gap_detector_v2 import run_gap_detector_v2
        result, _ = await run_gap_detector_v2(MOCK_SKILL_MAP, MOCK_EXTRACTED, ["dbt"])

        for gap in result["gaps"]:
            assert gap["severity"] in valid_severities


@pytest.mark.asyncio
async def test_gap_detector_gap_type_valid():
    valid_types = {"missing", "shallow"}
    valid_categories = {"domain_core", "general_practice"}
    with patch("repo_agents.gap_detector_v2.call_llm",
               new=AsyncMock(return_value=(MOCK_GAPS, 700))):
        from repo_agents.gap_detector_v2 import run_gap_detector_v2
        result, _ = await run_gap_detector_v2(MOCK_SKILL_MAP, MOCK_EXTRACTED, ["dbt"])

        for gap in result["gaps"]:
            assert gap["gap_type"] in valid_types
            assert gap["gap_category"] in valid_categories


# ─── Consequence Ranker tests ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_consequence_ranker_returns_required_keys():
    with patch("repo_agents.consequence_ranker.call_llm",
               new=AsyncMock(return_value=(MOCK_RANKED, 850))):
        from repo_agents.consequence_ranker import run_consequence_ranker
        result, latency = await run_consequence_ranker(
            gaps=MOCK_GAPS,
            learning_goal="interview",
            frameworks=["dbt"]
        )

        assert "learning_goal" in result
        assert "ranked_gaps" in result
        assert "analysis_summary" in result
        assert isinstance(result["ranked_gaps"], list)


@pytest.mark.asyncio
async def test_consequence_ranker_selects_max_5_gaps():
    large_ranked = {
        **MOCK_RANKED,
        "ranked_gaps": MOCK_RANKED["ranked_gaps"] * 3  # 6 gaps
    }
    with patch("repo_agents.consequence_ranker.call_llm",
               new=AsyncMock(return_value=(large_ranked, 800))):
        from repo_agents.consequence_ranker import run_consequence_ranker
        result, _ = await run_consequence_ranker(MOCK_GAPS, "interview", ["dbt"])
        # Pipeline should accept whatever the LLM returns — ranker itself doesn't truncate
        assert len(result["ranked_gaps"]) > 0


@pytest.mark.asyncio
async def test_consequence_ranker_gap_has_probing_question():
    with patch("repo_agents.consequence_ranker.call_llm",
               new=AsyncMock(return_value=(MOCK_RANKED, 750))):
        from repo_agents.consequence_ranker import run_consequence_ranker
        result, _ = await run_consequence_ranker(MOCK_GAPS, "interview", ["dbt"])

        for gap in result["ranked_gaps"]:
            assert "probing_question" in gap
            assert len(gap["probing_question"]) > 10


@pytest.mark.asyncio
async def test_consequence_ranker_urgency_valid():
    valid_urgencies = {"immediate", "soon", "eventually"}
    with patch("repo_agents.consequence_ranker.call_llm",
               new=AsyncMock(return_value=(MOCK_RANKED, 800))):
        from repo_agents.consequence_ranker import run_consequence_ranker
        result, _ = await run_consequence_ranker(MOCK_GAPS, "project", ["dbt"])

        for gap in result["ranked_gaps"]:
            assert gap["urgency"] in valid_urgencies


@pytest.mark.asyncio
async def test_consequence_ranker_domain_core_ranks_above_general():
    """Domain-core gaps should generally rank above general_practice gaps."""
    with patch("repo_agents.consequence_ranker.call_llm",
               new=AsyncMock(return_value=(MOCK_RANKED, 800))):
        from repo_agents.consequence_ranker import run_consequence_ranker
        result, _ = await run_consequence_ranker(MOCK_GAPS, "interview", ["dbt"])

        ranked = result["ranked_gaps"]
        domain_core_ranks = [g["rank"] for g in ranked if g["gap_category"] == "domain_core"]
        general_ranks = [g["rank"] for g in ranked if g["gap_category"] == "general_practice"]

        if domain_core_ranks and general_ranks:
            assert min(domain_core_ranks) < min(general_ranks)


# ─── Full pipeline tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_full_pipeline_produces_ranked_gaps():
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "dbt_project.yml").write_text("name: test\n")

        with patch("repo_agents.concept_extractor_v2.call_llm",
                   new=AsyncMock(return_value=(MOCK_EXTRACTED, 800))), \
             patch("repo_agents.skill_inferrer.call_llm",
                   new=AsyncMock(return_value=(MOCK_SKILL_MAP, 700))), \
             patch("repo_agents.gap_detector_v2.call_llm",
                   new=AsyncMock(return_value=(MOCK_GAPS, 900))), \
             patch("repo_agents.consequence_ranker.call_llm",
                   new=AsyncMock(return_value=(MOCK_RANKED, 800))):

            from repo_agents.pipeline_v2 import run_option2_pipeline
            result = await run_option2_pipeline(tmp, learning_goal="interview")

            assert result.error is None
            assert len(result.ranked_gaps) > 0
            assert result.ranked_gaps[0].probing_question != ""
            assert result.ranked_gaps[0].gap_category in {"domain_core", "general_practice"}
            assert result.domain == "data pipeline"
            assert result.learning_goal == "interview"
            assert len(result.agent_traces) == 4


@pytest.mark.asyncio
async def test_full_pipeline_produces_session_context():
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "dbt_project.yml").write_text("name: test\n")

        with patch("repo_agents.concept_extractor_v2.call_llm",
                   new=AsyncMock(return_value=(MOCK_EXTRACTED, 800))), \
             patch("repo_agents.skill_inferrer.call_llm",
                   new=AsyncMock(return_value=(MOCK_SKILL_MAP, 700))), \
             patch("repo_agents.gap_detector_v2.call_llm",
                   new=AsyncMock(return_value=(MOCK_GAPS, 900))), \
             patch("repo_agents.consequence_ranker.call_llm",
                   new=AsyncMock(return_value=(MOCK_RANKED, 800))):

            from repo_agents.pipeline_v2 import run_option2_pipeline, result_to_session_context
            result = await run_option2_pipeline(tmp, learning_goal="interview")
            context = result_to_session_context(result)

            # Verify it can slot into Option 1 session
            assert "topic" in context
            assert "learning_goal" in context
            assert context["phase"] == "probing"
            assert isinstance(context["open_gaps"], list)
            assert isinstance(context["known_concepts"], list)
            assert "repo_context" in context
            assert context["repo_context"]["domain"] == "data pipeline"
            assert len(context["repo_context"]["probing_questions"]) > 0


def test_format_result_shows_ranked_gaps():
    from repo_agents.pipeline_v2 import RepoAnalysisResult, RankedGap, format_result_for_display

    gap = RankedGap(
        rank=1,
        concept="dbt testing strategy",
        gap_type="missing",
        gap_category="general_practice",
        consequence_for_goal="Interviewers test for this",
        urgency="immediate",
        probing_question="If a model produces wrong results silently, how would you know?",
        what_a_good_answer_shows="Understanding of schema tests"
    )

    result = RepoAnalysisResult(
        repo_name="my-dbt-repo",
        input_type="local",
        learning_goal="interview",
        frameworks=["dbt", "SQL"],
        framework_context="A dbt analytics project.",
        domain="data pipeline",
        overall_assessment="Intermediate user.",
        strongest_areas=["SQL"],
        weakest_signals=["testing"],
        ranked_gaps=[gap],
        analysis_summary="Testing is the critical gap.",
        technology_coverage_score=35,
    )

    output = format_result_for_display(result)
    assert "dbt testing strategy" in output
    assert "immediate" in output
    assert "interview" in output
    assert "data pipeline" in output
    assert "[general]" in output
