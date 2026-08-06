"""
Unit tests for the curiosity breaker agent and eval pipeline.

These tests do NOT make real API calls — all LLM calls are mocked.
They validate:
- Objective eval logic (pure Python, always free)
- Agent output schema
- LLM judge schema
- Eval runner wiring
"""

import pytest
from unittest.mock import patch, AsyncMock

from eval.objective_eval import run_objective_eval
from eval.test_cases import TEST_CASES


# ─── Objective eval — known good anecdote ────────────────────────────────────

GOOD_ANECDOTE = (
    "Your pipeline ran successfully every day for 3 months. "
    "Last Tuesday, a senior engineer asked during your interview: "
    "'Your orders model showed 40,000 rows on Monday and 12 on Tuesday. "
    "How would you have caught that automatically?' "
    "You had no answer."
)

BAD_ANECDOTE = (
    "Testing is important in dbt. Without schema tests, "
    "your data quality will suffer. You should add not_null "
    "and unique tests to your models to ensure correctness."
)

TOO_SHORT_ANECDOTE = "Data pipelines can fail."

RESOLVING_ANECDOTE = (
    "Your model had 40,000 rows on Monday and 12 on Tuesday. "
    "After fixing the schema test configuration, the issue was resolved "
    "and the pipeline ran correctly again."
)


def test_good_anecdote_passes_all_checks():
    result = run_objective_eval(GOOD_ANECDOTE)
    assert result.length_pass is True
    assert result.concrete_detail_pass is True
    assert result.no_forbidden_phrases_pass is True
    assert result.ends_open_pass is True
    assert result.passed is True
    assert result.checks_passed == 4


def test_bad_anecdote_fails_forbidden_phrases():
    result = run_objective_eval(BAD_ANECDOTE)
    assert result.no_forbidden_phrases_pass is False
    assert "you should" in result.forbidden_phrases_found
    assert result.passed is False


def test_too_short_anecdote_fails_length():
    result = run_objective_eval(TOO_SHORT_ANECDOTE)
    assert result.length_pass is False
    assert result.passed is False


def test_resolving_anecdote_fails_ends_open():
    result = run_objective_eval(RESOLVING_ANECDOTE)
    assert result.ends_open_pass is False
    assert result.passed is False


def test_anecdote_without_concrete_detail_fails():
    no_detail = (
        "Something went wrong in the pipeline and the data was incorrect. "
        "Nobody knew why the model failed to produce the right output. "
        "The team spent days investigating the issue without finding a cause."
    )
    result = run_objective_eval(no_detail)
    assert result.concrete_detail_pass is False
    assert result.passed is False


def test_word_count_is_accurate():
    result = run_objective_eval(GOOD_ANECDOTE)
    expected = len(GOOD_ANECDOTE.split())
    assert result.word_count == expected


def test_failure_reasons_populated_on_fail():
    result = run_objective_eval(BAD_ANECDOTE)
    assert len(result.failure_reasons) > 0


def test_no_failure_reasons_on_pass():
    result = run_objective_eval(GOOD_ANECDOTE)
    assert result.failure_reasons == []


def test_custom_forbidden_phrases_respected():
    """Test that test_case-specific forbidden phrases are applied."""
    tc = TEST_CASES[0]
    anecdote_with_dbt_test = (
        "Your dbt test ran for 3 months without issues. "
        "Last Tuesday an interviewer asked about schema tests "
        "and unique tests in your pipeline."
    )
    result = run_objective_eval(
        anecdote_with_dbt_test,
        checks=tc["objective_checks"]
    )
    assert result.no_forbidden_phrases_pass is False
    assert any("schema test" in p or "unique test" in p
               for p in result.forbidden_phrases_found)


# ─── Curiosity breaker agent ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_curiosity_breaker_returns_string():
    mock_anecdote = GOOD_ANECDOTE
    with patch("chat_agents.curiosity_breaker.call_llm",
               new=AsyncMock(return_value=(mock_anecdote, 800))):
        from chat_agents.curiosity_breaker import run_curiosity_breaker
        result, latency = await run_curiosity_breaker(
            concept="dbt testing strategy",
            learning_goal="interview",
            domain="data pipeline",
            repo_context="A dbt project with 12 models and no schema tests",
        )
        assert isinstance(result, str)
        assert len(result) > 0
        assert latency == 800


@pytest.mark.asyncio
async def test_curiosity_breaker_output_passes_objective_eval():
    """Generated anecdote (mocked) should pass objective checks."""
    with patch("chat_agents.curiosity_breaker.call_llm",
               new=AsyncMock(return_value=(GOOD_ANECDOTE, 750))):
        from chat_agents.curiosity_breaker import run_curiosity_breaker
        anecdote, _ = await run_curiosity_breaker(
            concept="dbt testing strategy",
            learning_goal="interview",
            domain="data pipeline",
            repo_context="A dbt project with 12 models and no schema tests",
        )
        result = run_objective_eval(anecdote)
        assert result.passed is True


# ─── LLM judge ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_llm_judge_returns_required_keys():
    mock_output = {
        "curiosity": 5,
        "relevance": 4,
        "realism": 4,
        "non_explanatory": 5,
        "goal_alignment": 4,
        "total": 22,
        "reasoning": "The anecdote creates genuine curiosity with a specific scenario.",
        "strongest_aspect": "Concrete numbers and unresolved ending",
        "weakest_aspect": "Could be more specific to dbt domain",
    }
    with patch("eval.llm_judge.call_llm",
               new=AsyncMock(return_value=(mock_output, 900))):
        from eval.llm_judge import run_llm_judge
        tc = TEST_CASES[0]
        result = await run_llm_judge(
            anecdote=GOOD_ANECDOTE,
            concept=tc["input"]["concept"],
            learning_goal=tc["input"]["learning_goal"],
            domain=tc["input"]["domain"],
            example_acceptable=tc["example_acceptable"],
            example_unacceptable=tc["example_unacceptable"],
            thresholds=tc["llm_judge_thresholds"],
        )
        assert result.curiosity == 5
        assert result.total == 22
        assert result.passed is True
        assert result.reasoning != ""


@pytest.mark.asyncio
async def test_llm_judge_fails_below_threshold():
    mock_output = {
        "curiosity": 2,
        "relevance": 3,
        "realism": 2,
        "non_explanatory": 2,
        "goal_alignment": 3,
        "total": 12,
        "reasoning": "The anecdote explains the concept directly.",
        "strongest_aspect": "Mentions the domain",
        "weakest_aspect": "Gives away the answer",
    }
    with patch("eval.llm_judge.call_llm",
               new=AsyncMock(return_value=(mock_output, 700))):
        from eval.llm_judge import run_llm_judge
        tc = TEST_CASES[0]
        result = await run_llm_judge(
            anecdote=BAD_ANECDOTE,
            concept=tc["input"]["concept"],
            learning_goal=tc["input"]["learning_goal"],
            domain=tc["input"]["domain"],
            example_acceptable=tc["example_acceptable"],
            example_unacceptable=tc["example_unacceptable"],
            thresholds=tc["llm_judge_thresholds"],
        )
        assert result.passed is False
        assert result.total < result.threshold


# ─── Test cases sanity check ─────────────────────────────────────────────────

def test_test_cases_have_required_fields():
    for tc in TEST_CASES:
        assert "id" in tc
        assert "input" in tc
        assert "example_acceptable" in tc
        assert "example_unacceptable" in tc
        assert "objective_checks" in tc
        assert "llm_judge_thresholds" in tc
        assert "concept" in tc["input"]
        assert "learning_goal" in tc["input"]
        assert "domain" in tc["input"]
        assert "repo_context" in tc["input"]


def test_example_acceptable_passes_objective_eval():
    """The 'good' reference anecdote in each test case should pass objective checks."""
    for tc in TEST_CASES:
        result = run_objective_eval(
            tc["example_acceptable"],
            checks=tc["objective_checks"],
        )
        assert result.passed is True, (
            f"Test case {tc['id']}: example_acceptable failed objective eval: "
            f"{result.failure_reasons}"
        )


def test_example_unacceptable_fails_objective_eval():
    """The 'bad' reference anecdote in each test case should fail objective checks."""
    for tc in TEST_CASES:
        result = run_objective_eval(
            tc["example_unacceptable"],
            checks=tc["objective_checks"],
        )
        assert result.passed is False, (
            f"Test case {tc['id']}: example_unacceptable unexpectedly passed objective eval"
        )
