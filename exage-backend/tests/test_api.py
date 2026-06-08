import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app

client = TestClient(app)

def test_create_session():
    response = client.post("/sessions/", json={
        "topic": "Kubernetes",
        "learning_goal": "interview"
    })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["topic"] == "Kubernetes"
    assert data["phase"] == "onboarding"
    assert data["turn_count"] == 0

def test_get_session():
    # First create a session
    create_response = client.post("/sessions/", json={
        "topic": "Python",
        "learning_goal": "exam"
    })
    session_id = create_response.json()["id"]

    # Then fetch it
    get_response = client.get(f"/sessions/{session_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == session_id

def test_get_nonexistent_session():
    response = client.get("/sessions/nonexistent-id-000")
    assert response.status_code == 404

def test_chat_endpoint():
    # Create session first
    session = client.post("/sessions/", json={
        "topic": "Kubernetes",
        "learning_goal": "interview"
    }).json()

    mock_response = "What do you think happens after kubectl apply?"

    with patch("routers.chat.run_pipeline", new=AsyncMock(return_value=mock_response)):
        response = client.post(f"/sessions/{session['id']}/chat", json={
            "message": "I understand pods and deployments"
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "phase" in data
        assert "turn" in data

def test_chat_endpoint():
    session = client.post("/sessions/", json={
        "topic": "Kubernetes",
        "learning_goal": "interview"
    }).json()

    async def mock_stream(*args, **kwargs):
        yield {"type": "token", "text": "What do you think happens after kubectl apply?"}
        yield {"type": "done", "phase": "probing", "turn": 1, "gaps": []}

    with patch("pipeline.runner.run_pipeline_streaming", new=mock_stream):
        response = client.post(f"/sessions/{session['id']}/chat", json={
            "message": "I understand pods and deployments"
        })
        assert response.status_code == 200