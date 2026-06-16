"""
Tests for Phase 2 — Concept Extractor and Skill Inferrer agents.

LLM calls are mocked — tests validate output schema and
pipeline wiring, not LLM quality.
"""

import pytest
from unittest.mock import patch, AsyncMock


# ─── Concept Extractor tests ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_concept_extractor_returns_required_keys():
    mock_output = {
        "framework_context": "A dbt project for analytics transformations",
        "concepts": [
            {
                "concept": "incremental materialisation",
                "category": "data modelling",
                "evidence": "models/staging/stg_orders.sql",
                "usage_count": "2-5",
                "present": True
            },
            {
                "concept": "ref() function",
                "category": "dependency management",
                "evidence": "used in 3 models",
                "usage_count": "5+",
                "present": True
            }
        ],
        "absent_concepts": [
            {
                "concept": "dbt tests",
                "category": "testing",
                "reason": "no schema.yml or test files found"
            }
        ],
        "structural_observations": [
            "Models are organised by staging and marts layers"
        ]
    }

    with patch("agents_option2.concept_extractor_v2.call_llm",
               new=AsyncMock(return_value=(mock_output, 800))):
        from agents_option2.concept_extractor_v2 import run_concept_extractor_v2
        result, latency = await run_concept_extractor_v2(
            repo_summary_text="sample repo text",
            frameworks=["dbt", "SQL"]
        )

        assert "framework_context" in result
        assert "concepts" in result
        assert "absent_concepts" in result
        assert "structural_observations" in result
        assert isinstance(result["concepts"], list)
        assert latency == 800


@pytest.mark.asyncio
async def test_concept_extractor_concept_has_required_fields():
    mock_output = {
        "framework_context": "A Python FastAPI backend",
        "concepts": [
            {
                "concept": "async route handlers",
                "category": "API design",
                "evidence": "main.py",
                "usage_count": "5+",
                "present": True
            }
        ],
        "absent_concepts": [],
        "structural_observations": []
    }

    with patch("agents_option2.concept_extractor_v2.call_llm",
               new=AsyncMock(return_value=(mock_output, 600))):
        from agents_option2.concept_extractor_v2 import run_concept_extractor_v2
        result, _ = await run_concept_extractor_v2("text", ["Python", "FastAPI"])

        concept = result["concepts"][0]
        assert "concept" in concept
        assert "category" in concept
        assert "evidence" in concept
        assert "usage_count" in concept
        assert "present" in concept


@pytest.mark.asyncio
async def test_concept_extractor_handles_absent_concepts():
    mock_output = {
        "framework_context": "A dbt project with no tests",
        "concepts": [],
        "absent_concepts": [
            {
                "concept": "schema tests",
                "category": "testing",
                "reason": "no schema.yml found anywhere in the project"
            }
        ],
        "structural_observations": ["No test coverage detected"]
    }

    with patch("agents_option2.concept_extractor_v2.call_llm",
               new=AsyncMock(return_value=(mock_output, 500))):
        from agents_option2.concept_extractor_v2 import run_concept_extractor_v2
        result, _ = await run_concept_extractor_v2("text", ["dbt"])

        assert len(result["absent_concepts"]) == 1
        assert result["absent_concepts"][0]["concept"] == "schema tests"


# ─── Skill Inferrer tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_skill_inferrer_returns_required_keys():
    mock_output = {
        "skill_map": [
            {
                "concept": "incremental materialisation",
                "inferred_depth": "surface",
                "confidence": "high",
                "reasoning": "Used only with unique_key, no merge strategies observed",
                "related_gap": "merge strategies and on_schema_change handling"
            }
        ],
        "overall_assessment": "The developer has working knowledge of dbt basics but shows shallow understanding of advanced materialisation strategies.",
        "strongest_areas": ["SQL transformations", "basic dbt modelling"],
        "weakest_signals": ["testing", "incremental strategies"]
    }

    with patch("agents_option2.skill_inferrer.call_llm",
               new=AsyncMock(return_value=(mock_output, 900))):
        from agents_option2.skill_inferrer import run_skill_inferrer
        result, latency = await run_skill_inferrer(
            extracted_concepts={"concepts": [], "absent_concepts": []},
            frameworks=["dbt"]
        )

        assert "skill_map" in result
        assert "overall_assessment" in result
        assert "strongest_areas" in result
        assert "weakest_signals" in result
        assert isinstance(result["skill_map"], list)


@pytest.mark.asyncio
async def test_skill_inferrer_depth_values_are_valid():
    valid_depths = {"surface", "functional", "deep"}
    mock_output = {
        "skill_map": [
            {
                "concept": "ref() function",
                "inferred_depth": "functional",
                "confidence": "high",
                "reasoning": "Used consistently and correctly across models",
                "related_gap": "understanding of DAG execution order"
            },
            {
                "concept": "macros",
                "inferred_depth": "surface",
                "confidence": "medium",
                "reasoning": "Only one macro found, wraps dbt_utils",
                "related_gap": "writing reusable macros with complex logic"
            }
        ],
        "overall_assessment": "Intermediate dbt user.",
        "strongest_areas": ["SQL"],
        "weakest_signals": ["macros"]
    }

    with patch("agents_option2.skill_inferrer.call_llm",
               new=AsyncMock(return_value=(mock_output, 700))):
        from agents_option2.skill_inferrer import run_skill_inferrer
        result, _ = await run_skill_inferrer({}, ["dbt"])

        for skill in result["skill_map"]:
            assert skill["inferred_depth"] in valid_depths


@pytest.mark.asyncio
async def test_skill_inferrer_confidence_values_are_valid():
    valid_confidences = {"high", "medium", "low"}
    mock_output = {
        "skill_map": [
            {
                "concept": "CTEs",
                "inferred_depth": "deep",
                "confidence": "high",
                "reasoning": "Complex multi-layer CTEs with clear naming conventions",
                "related_gap": "query optimisation strategies"
            }
        ],
        "overall_assessment": "Strong SQL fundamentals.",
        "strongest_areas": ["CTEs"],
        "weakest_signals": []
    }

    with patch("agents_option2.skill_inferrer.call_llm",
               new=AsyncMock(return_value=(mock_output, 650))):
        from agents_option2.skill_inferrer import run_skill_inferrer
        result, _ = await run_skill_inferrer({}, ["SQL"])

        for skill in result["skill_map"]:
            assert skill["confidence"] in valid_confidences


# ─── Pipeline v2 tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_v2_returns_result_object():
    import tempfile
    from pathlib import Path

    # Create a minimal temp repo
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "dbt_project.yml").write_text("name: test_project\n")
        Path(tmp, "requirements.txt").write_text("dbt-core==1.5.0\n")

        extractor_mock = {
            "framework_context": "A dbt analytics project",
            "concepts": [{"concept": "dbt models", "category": "modelling",
                          "evidence": "dbt_project.yml", "usage_count": "1", "present": True}],
            "absent_concepts": [],
            "structural_observations": []
        }
        skill_mock = {
            "skill_map": [{"concept": "dbt models", "inferred_depth": "surface",
                           "confidence": "medium", "reasoning": "Minimal project structure",
                           "related_gap": "materialisation strategies"}],
            "overall_assessment": "Early-stage dbt user.",
            "strongest_areas": [],
            "weakest_signals": ["testing"]
        }

        with patch("agents_option2.concept_extractor_v2.call_llm",
                   new=AsyncMock(return_value=(extractor_mock, 800))), \
             patch("agents_option2.skill_inferrer.call_llm",
                   new=AsyncMock(return_value=(skill_mock, 700))):

            from agents_option2.pipeline_v2 import run_option2_pipeline
            result = await run_option2_pipeline(tmp)

            assert result.error is None
            assert result.repo_name is not None
            assert result.input_type == "local"
            assert isinstance(result.frameworks, list)
            assert isinstance(result.extracted_concepts, dict)
            assert isinstance(result.skill_map, dict)
            assert len(result.agent_traces) == 2


@pytest.mark.asyncio
async def test_pipeline_v2_handles_invalid_path():
    from agents_option2.pipeline_v2 import run_option2_pipeline
    result = await run_option2_pipeline("/nonexistent/repo/path")
    assert result.error is not None


def test_format_result_for_display():
    from agents_option2.pipeline_v2 import RepoAnalysisResult, format_result_for_display

    result = RepoAnalysisResult(
        repo_name="my-dbt-project",
        input_type="local",
        frameworks=["dbt", "SQL"],
        framework_context="A dbt analytics project for e-commerce data.",
        extracted_concepts={},
        skill_map={},
        overall_assessment="Intermediate dbt user with strong SQL skills.",
        strongest_areas=["SQL transformations", "dbt basics"],
        weakest_signals=["testing", "incremental strategies"],
    )

    output = format_result_for_display(result)
    assert "my-dbt-project" in output
    assert "dbt" in output
    assert "SQL transformations" in output
    assert "testing" in output
    assert "Intermediate dbt user" in output


def test_format_result_handles_error():
    from agents_option2.pipeline_v2 import RepoAnalysisResult, format_result_for_display

    result = RepoAnalysisResult(
        repo_name="bad-repo",
        input_type="local",
        frameworks=[],
        framework_context="",
        extracted_concepts={},
        skill_map={},
        overall_assessment="",
        strongest_areas=[],
        weakest_signals=[],
        error="Path does not exist",
    )

    output = format_result_for_display(result)
    assert "Error" in output
    assert "Path does not exist" in output
