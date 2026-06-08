import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ─── Synthesis Agent ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_synthesis_agent_returns_required_keys():
    mock_output = {
        "opening": "You covered a solid range of Kubernetes concepts today.",
        "gaps_summary": [
            {"concept": "kube-scheduler", "severity": "critical", "one_line": "Core to interview questions"}
        ],
        "misconceptions_summary": [],
        "curiosity_paths": [
            {"title": "Kubernetes Networking", "description": "Explore how pods communicate", "starter_question": "How do services route traffic to pods?"},
            {"title": "etcd deep dive", "description": "Understand cluster state storage", "starter_question": "What happens if etcd goes down?"},
            {"title": "RBAC", "description": "Learn about access control", "starter_question": "How does Kubernetes decide who can do what?"},
        ],
        "closing_thought": "If Kubernetes disappeared tomorrow, what would you build instead?"
    }
    with patch("agents.synthesis_agent.call_llm", new=AsyncMock(return_value=(mock_output, 200))):
        from agents.synthesis_agent import run_synthesis_agent
        result, _ = await run_synthesis_agent(
            topic="Kubernetes",
            learning_goal="interview",
            all_gaps=[{"concept": "kube-scheduler", "severity": "critical", "why_it_matters_for_goal": "core topic"}],
            misconceptions=[],
            conversation_history=[],
        )
        assert "opening" in result
        assert "gaps_summary" in result
        assert "curiosity_paths" in result
        assert "closing_thought" in result
        assert len(result["curiosity_paths"]) == 3

@pytest.mark.asyncio
async def test_synthesis_closing_thought_is_question():
    mock_output = {
        "opening": "Good session.",
        "gaps_summary": [],
        "misconceptions_summary": [],
        "curiosity_paths": [
            {"title": "A", "description": "desc", "starter_question": "q?"},
            {"title": "B", "description": "desc", "starter_question": "q?"},
            {"title": "C", "description": "desc", "starter_question": "q?"},
        ],
        "closing_thought": "What would you do differently now?"
    }
    with patch("agents.synthesis_agent.call_llm", new=AsyncMock(return_value=(mock_output, 150))):
        from agents.synthesis_agent import run_synthesis_agent
        result, _ = await run_synthesis_agent(
            topic="Python", learning_goal="exam",
            all_gaps=[], misconceptions=[], conversation_history=[],
        )
        assert result["closing_thought"].strip().endswith("?")

# ─── Evaluation Agent ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_evaluation_agent_returns_required_keys():
    mock_output = {
        "gap_exposed": True,
        "learner_showed_understanding": False,
        "question_quality": "good",
        "evidence": "Learner gave a vague answer that did not address scheduling.",
        "recommendation": "Ask more specifically about node selection criteria."
    }
    with patch("agents.evaluation_agent.call_llm", new=AsyncMock(return_value=(mock_output, 100))):
        from agents.evaluation_agent import run_evaluation_agent
        result, _ = await run_evaluation_agent(
            question_asked="What component decides where a pod runs?",
            learner_response="The cluster handles it automatically.",
            targeted_gap="kube-scheduler",
        )
        assert "gap_exposed" in result
        assert "question_quality" in result
        assert "recommendation" in result
        assert isinstance(result["gap_exposed"], bool)

@pytest.mark.asyncio
async def test_evaluation_agent_question_quality_valid_values():
    mock_output = {
        "gap_exposed": False,
        "learner_showed_understanding": True,
        "question_quality": "too_easy",
        "evidence": "Learner knew this already.",
        "recommendation": "Escalate to structural questions."
    }
    with patch("agents.evaluation_agent.call_llm", new=AsyncMock(return_value=(mock_output, 90))):
        from agents.evaluation_agent import run_evaluation_agent
        result, _ = await run_evaluation_agent(
            question_asked="What is a pod?",
            learner_response="A pod is the smallest deployable unit in Kubernetes.",
            targeted_gap="pods",
        )
        valid_qualities = {"good", "too_easy", "too_vague", "off_topic"}
        assert result["question_quality"] in valid_qualities

# ─── Synthesis Trigger Logic ───────────────────────────────────────

def test_synthesis_triggers_on_keyword():
    from pipeline.runner import _is_synthesis_trigger
    assert _is_synthesis_trigger("wrap up", 2) is True
    assert _is_synthesis_trigger("done", 1) is True
    assert _is_synthesis_trigger("summarize", 3) is True
    assert _is_synthesis_trigger("finish", 0) is True
    assert _is_synthesis_trigger("that's all", 1) is True

def test_synthesis_triggers_on_turn_count():
    from pipeline.runner import _is_synthesis_trigger
    assert _is_synthesis_trigger("I know pods", 8) is True
    assert _is_synthesis_trigger("I know pods", 10) is True

def test_synthesis_does_not_trigger_early():
    from pipeline.runner import _is_synthesis_trigger
    assert _is_synthesis_trigger("I know pods", 3) is False
    assert _is_synthesis_trigger("tell me more", 5) is False

# ─── Delete Session API ────────────────────────────────────────────

def test_delete_session():
    # Create a session first
    create_res = client.post("/sessions/", json={
        "topic": "Delete Test",
        "learning_goal": "curiosity"
    })
    assert create_res.status_code == 200
    session_id = create_res.json()["id"]

    # Delete it
    delete_res = client.delete(f"/sessions/{session_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["deleted"] == session_id

    # Confirm it's gone
    get_res = client.get(f"/sessions/{session_id}")
    assert get_res.status_code == 404

def test_delete_nonexistent_session():
    res = client.delete("/sessions/nonexistent-id-999")
    assert res.status_code == 404
