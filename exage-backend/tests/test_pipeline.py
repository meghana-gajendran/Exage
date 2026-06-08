import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import json

@pytest.mark.asyncio
async def test_pipeline_returns_string_response():
    mock_session = MagicMock()
    mock_session.id = "test-session-1"
    mock_session.topic = "Kubernetes"
    mock_session.learning_goal = "interview"
    mock_session.turn_count = 0
    mock_session.phase = "onboarding"
    mock_session.known_concepts_json = "[]"
    mock_session.asked_gaps_json = "[]"
    mock_session.open_gaps_json = "[]"
    mock_session.misconceptions_json = "[]"
    mock_session.messages = []

    mock_db = MagicMock()

    extractor_out = {"stated_concepts": ["pods"], "confidence_signals": [], "framing_flags": []}
    detector_out = {"missing_concepts": [{"concept": "kube-scheduler", "severity": "critical", "why_it_matters_for_goal": "core topic"}], "likely_misconceptions": []}
    generator_out = {"questions": [{"question": "What happens after kubectl apply?", "targets_concept": "kube-scheduler", "question_type": "structural", "priority": 1}]}
    composer_out = "What happens after kubectl apply?"

    with patch("pipeline.runner.run_concept_extractor", new=AsyncMock(return_value=(extractor_out, 100))), \
         patch("pipeline.runner.run_gap_detector", new=AsyncMock(return_value=(detector_out, 100))), \
         patch("pipeline.runner.run_question_generator", new=AsyncMock(return_value=(generator_out, 100))), \
         patch("pipeline.runner.run_response_composer", new=AsyncMock(return_value=(composer_out, 100))):

        from pipeline.runner import run_pipeline
        response = await run_pipeline(mock_session, "I understand pods", mock_db)

        assert isinstance(response, str)
        assert len(response) > 0

@pytest.mark.asyncio
async def test_pipeline_updates_asked_gaps():
    mock_session = MagicMock()
    mock_session.id = "test-session-2"
    mock_session.topic = "Kubernetes"
    mock_session.learning_goal = "interview"
    mock_session.turn_count = 0
    mock_session.phase = "probing"
    mock_session.known_concepts_json = "[]"
    mock_session.asked_gaps_json = "[]"
    mock_session.open_gaps_json = "[]"
    mock_session.misconceptions_json = "[]"
    mock_session.messages = []

    mock_db = MagicMock()

    extractor_out = {"stated_concepts": ["pods"], "confidence_signals": [], "framing_flags": []}
    detector_out = {"missing_concepts": [
        {"concept": "etcd", "severity": "critical", "why_it_matters_for_goal": "stores state"},
        {"concept": "kubelet", "severity": "important", "why_it_matters_for_goal": "runs on nodes"}
    ], "likely_misconceptions": []}
    generator_out = {"questions": []}
    composer_out = "What do you think stores the cluster state?"

    with patch("pipeline.runner.run_concept_extractor", new=AsyncMock(return_value=(extractor_out, 100))), \
         patch("pipeline.runner.run_gap_detector", new=AsyncMock(return_value=(detector_out, 100))), \
         patch("pipeline.runner.run_question_generator", new=AsyncMock(return_value=(generator_out, 100))), \
         patch("pipeline.runner.run_response_composer", new=AsyncMock(return_value=(composer_out, 100))):

        from pipeline.runner import run_pipeline
        await run_pipeline(mock_session, "I know pods", mock_db)

        asked = json.loads(mock_session.asked_gaps_json)
        assert len(asked) > 0  # gaps were marked as asked