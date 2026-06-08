import pytest
from unittest.mock import patch, AsyncMock

# --- Concept Extractor ---

@pytest.mark.asyncio
async def test_extractor_returns_stated_concepts():
    mock_output = {
        "stated_concepts": ["pods", "deployments", "scaling"],
        "confidence_signals": ["I understand"],
        "framing_flags": ["vague claim about scaling"]
    }
    with patch("agents.concept_extractor.call_llm", new=AsyncMock(return_value=(mock_output, 100))):
        from agents.concept_extractor import run_concept_extractor
        result, _ = await run_concept_extractor("Kubernetes", "I understand pods, deployments and scaling")
        assert "pods" in result["stated_concepts"]
        assert "deployments" in result["stated_concepts"]

@pytest.mark.asyncio
async def test_extractor_output_has_required_keys():
    mock_output = {
        "stated_concepts": [],
        "confidence_signals": [],
        "framing_flags": []
    }
    with patch("agents.concept_extractor.call_llm", new=AsyncMock(return_value=(mock_output, 50))):
        from agents.concept_extractor import run_concept_extractor
        result, _ = await run_concept_extractor("Python", "I know loops")
        assert "stated_concepts" in result
        assert "confidence_signals" in result
        assert "framing_flags" in result

# --- Gap Detector ---

@pytest.mark.asyncio
async def test_gap_detector_finds_missing_concepts():
    mock_output = {
        "missing_concepts": [
            {"concept": "kube-scheduler", "severity": "critical", "why_it_matters_for_goal": "core interview topic"}
        ],
        "likely_misconceptions": []
    }
    with patch("agents.gap_detector.call_llm", new=AsyncMock(return_value=(mock_output, 120))):
        from agents.gap_detector import run_gap_detector
        result, _ = await run_gap_detector(
            topic="Kubernetes",
            stated_concepts=["pods", "deployments"],
            learning_goal="interview",
            asked_gaps=[]
        )
        concepts = [g["concept"] for g in result["missing_concepts"]]
        assert "kube-scheduler" in concepts

@pytest.mark.asyncio
async def test_gap_detector_excludes_asked_gaps():
    mock_output = {
        "missing_concepts": [
            {"concept": "etcd", "severity": "important", "why_it_matters_for_goal": "stores cluster state"}
        ],
        "likely_misconceptions": []
    }
    with patch("agents.gap_detector.call_llm", new=AsyncMock(return_value=(mock_output, 100))):
        from agents.gap_detector import run_gap_detector
        result, _ = await run_gap_detector(
            topic="Kubernetes",
            stated_concepts=["pods"],
            learning_goal="interview",
            asked_gaps=["kube-scheduler"]  # already asked — should not appear
        )
        concepts = [g["concept"] for g in result["missing_concepts"]]
        assert "kube-scheduler" not in concepts

# --- Question Generator ---

@pytest.mark.asyncio
async def test_question_generator_returns_questions():
    mock_output = {
        "questions": [
            {"question": "What happens after kubectl apply?", "targets_concept": "kube-scheduler", "question_type": "structural", "priority": 1}
        ]
    }
    with patch("agents.question_generator.call_llm", new=AsyncMock(return_value=(mock_output, 90))):
        from agents.question_generator import run_question_generator
        result, _ = await run_question_generator(
            missing_concepts=[{"concept": "kube-scheduler", "severity": "critical", "why_it_matters_for_goal": "core topic"}],
            likely_misconceptions=[],
            learning_goal="interview",
            conversation_history=[]
        )
        assert len(result["questions"]) > 0
        assert "question" in result["questions"][0]
        assert "priority" in result["questions"][0]

# --- Response Composer ---

@pytest.mark.asyncio
async def test_composer_asks_at_most_two_questions():
    mock_response = "Interesting — what happens to traffic when a pod restarts? Also, how does Kubernetes decide where to schedule a pod?"
    with patch("agents.response_composer.call_llm", new=AsyncMock(return_value=(mock_response, 80))):
        from agents.response_composer import run_response_composer
        result, _ = await run_response_composer(
            ranked_questions=[],
            conversation_history=[],
            learner_last_message="I understand pods and deployments"
        )
        assert result.count("?") <= 2

@pytest.mark.asyncio
async def test_composer_does_not_explain_concepts():
    mock_response = "When a pod crashes, what do you think triggers its restart?"
    with patch("agents.response_composer.call_llm", new=AsyncMock(return_value=(mock_response, 80))):
        from agents.response_composer import run_response_composer
        result, _ = await run_response_composer(
            ranked_questions=[],
            conversation_history=[],
            learner_last_message="I know about pod restarts"
        )
        forbidden = ["is a", "is the", "refers to", "means that", "defined as"]
        for phrase in forbidden:
            assert phrase not in result.lower()

@pytest.mark.asyncio
async def test_composer_avoids_praise():
    mock_response = "What component do you think is responsible for detecting that failure?"
    with patch("agents.response_composer.call_llm", new=AsyncMock(return_value=(mock_response, 75))):
        from agents.response_composer import run_response_composer
        result, _ = await run_response_composer(
            ranked_questions=[],
            conversation_history=[],
            learner_last_message="I know pods can fail"
        )
        praise = ["great answer", "correct!", "well done", "exactly right", "perfect"]
        for phrase in praise:
            assert phrase not in result.lower()