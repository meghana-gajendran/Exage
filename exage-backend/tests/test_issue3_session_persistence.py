"""
Tests for Issue #3 fix — repo session context persistence.

Covers:
- New repo session persists session_context and opening message
- Reload (simulated via fresh DB query) restores everything
- Legacy sessions without session_context_json still load gracefully
- Switching between chat and repo sessions works identically
"""

import json
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import Session as ChatSession, Message

client = TestClient(app)


# ─── New repo session persists context + opening message ─────────────────────

def test_repo_session_persists_session_context():
    session_context = {
        "topic": "container runtime (Python)",
        "learning_goal": "interview",
        "phase": "probing",
        "known_concepts": ["File system operations"],
        "open_gaps": [
            {"concept": "Namespace isolation", "severity": "critical",
             "why_it_matters_for_goal": "Core to container security"}
        ],
        "asked_gaps": [],
        "misconceptions": [],
        "repo_context": {
            "repo_name": "docksmith",
            "domain": "container runtime",
            "framework_context": "A Docker-like build and runtime system.",
            "overall_assessment": "Functional understanding of core Python concepts.",
            "probing_questions": [
                "Can you explain how different Linux namespaces work together?"
            ],
        },
    }

    response = client.post("/repo-analysis/create-session", json=session_context)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["phase"] == "probing"
    assert "opening_message" in data
    assert "docksmith" in data["opening_message"]

    # Fetch the session back via the normal sessions endpoint
    get_response = client.get(f"/sessions/{data['session_id']}")
    assert get_response.status_code == 200
    session_data = get_response.json()

    # session_context must be persisted and parsed correctly
    assert "session_context" in session_data
    assert session_data["session_context"]["repo_context"]["repo_name"] == "docksmith"
    assert session_data["session_context"]["repo_context"]["domain"] == "container runtime"


def test_repo_session_persists_opening_message_as_normal_message():
    session_context = {
        "topic": "data pipeline (dbt)",
        "learning_goal": "curiosity",
        "known_concepts": [],
        "open_gaps": [],
        "repo_context": {
            "repo_name": "jaffle_shop",
            "domain": "data pipeline",
            "framework_context": "A dbt analytics project.",
            "overall_assessment": "Intermediate dbt user.",
            "probing_questions": ["How does incremental materialisation work?"],
        },
    }

    create_response = client.post("/repo-analysis/create-session", json=session_context)
    session_id = create_response.json()["session_id"]
    expected_opening = create_response.json()["opening_message"]

    # The opening message must appear via the SAME endpoint used for normal chat
    messages_response = client.get(f"/sessions/{session_id}/messages")
    assert messages_response.status_code == 200
    messages = messages_response.json()

    assert len(messages) == 1
    assert messages[0]["role"] == "assistant"
    assert messages[0]["content"] == expected_opening


# ─── Reload simulation (fresh DB query, as if server restarted) ──────────────

def test_repo_session_survives_simulated_reload():
    session_context = {
        "topic": "container runtime (Python)",
        "learning_goal": "interview",
        "known_concepts": ["CLI design"],
        "open_gaps": [{"concept": "Image management", "severity": "critical",
                        "why_it_matters_for_goal": "core mechanism"}],
        "repo_context": {
            "repo_name": "docksmith",
            "domain": "container runtime",
            "framework_context": "A Docker-like tool.",
            "overall_assessment": "Functional understanding.",
            "probing_questions": ["How does your image management work?"],
        },
    }

    create_response = client.post("/repo-analysis/create-session", json=session_context)
    session_id = create_response.json()["session_id"]

    # Simulate a backend restart: open a completely fresh DB session,
    # query independently (no shared state with the request above)
    fresh_db = SessionLocal()
    try:
        reloaded_session = fresh_db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()
        assert reloaded_session is not None

        reloaded_context = json.loads(reloaded_session.session_context_json)
        assert reloaded_context["repo_context"]["repo_name"] == "docksmith"
        assert reloaded_context["topic"] == "container runtime (Python)"

        reloaded_messages = fresh_db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at).all()
        assert len(reloaded_messages) == 1
        assert "docksmith" in reloaded_messages[0].content
    finally:
        fresh_db.close()


# ─── Legacy sessions without session_context_json ─────────────────────────────

def test_legacy_session_without_context_loads_gracefully():
    """
    Simulates a session created before this fix (e.g. directly via
    POST /sessions/, which never sets session_context_json explicitly —
    it should default to '{}' and never error).
    """
    response = client.post("/sessions/", json={
        "topic": "Kubernetes",
        "learning_goal": "interview",
    })
    assert response.status_code == 200
    data = response.json()

    # Must not error, must default to empty dict
    assert "session_context" in data
    assert data["session_context"] == {}


def test_legacy_session_explicit_empty_context_in_db():
    """
    Directly creates a session in the DB the old way (no session_context_json
    set at all relies on column default) and confirms the API layer
    handles it without raising.
    """
    db = SessionLocal()
    try:
        session = ChatSession(
            topic="Legacy Topic",
            learning_goal="exam",
            phase="onboarding",
            known_concepts_json="[]",
            asked_gaps_json="[]",
            open_gaps_json="[]",
            misconceptions_json="[]",
            # Deliberately not setting session_context_json —
            # column default "{}" should kick in
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        session_id = session.id
    finally:
        db.close()

    response = client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_context"] == {}
    assert data["topic"] == "Legacy Topic"


# ─── Switching between chat and repo sessions ─────────────────────────────────

def test_switching_between_chat_and_repo_sessions():
    # Create a normal chat session
    chat_response = client.post("/sessions/", json={
        "topic": "React Hooks",
        "learning_goal": "exam",
    })
    chat_session_id = chat_response.json()["id"]

    # Create a repo session
    repo_context = {
        "topic": "container runtime (Python)",
        "learning_goal": "interview",
        "known_concepts": [],
        "open_gaps": [],
        "repo_context": {
            "repo_name": "docksmith",
            "domain": "container runtime",
            "framework_context": "A Docker-like tool.",
            "overall_assessment": "Functional understanding.",
            "probing_questions": ["Q1?"],
        },
    }
    repo_response = client.post("/repo-analysis/create-session", json=repo_context)
    repo_session_id = repo_response.json()["session_id"]

    # Both must be independently fetchable with correct, isolated context
    chat_get = client.get(f"/sessions/{chat_session_id}")
    repo_get = client.get(f"/sessions/{repo_session_id}")

    assert chat_get.json()["session_context"] == {}
    assert repo_get.json()["session_context"]["repo_context"]["repo_name"] == "docksmith"

    # Messages must also be correctly isolated
    chat_messages = client.get(f"/sessions/{chat_session_id}/messages").json()
    repo_messages = client.get(f"/sessions/{repo_session_id}/messages").json()

    assert len(chat_messages) == 0  # plain chat session has no DB messages until first turn
    assert len(repo_messages) == 1  # repo session has the persisted opening message


# ─── get_all_sessions includes session_context for every session ─────────────

def test_get_all_sessions_includes_session_context_field():
    response = client.get("/sessions/")
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) > 0
    for s in sessions:
        assert "session_context" in s
        assert isinstance(s["session_context"], dict)
