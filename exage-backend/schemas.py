import json
from pydantic import BaseModel, ConfigDict, model_validator
from datetime import datetime
from typing import Any

class SessionCreate(BaseModel):
    topic: str
    learning_goal: str  # "exam" | "interview" | "project" | "teaching" | "curiosity"

class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    topic: str
    learning_goal: str
    phase: str
    turn_count: int
    session_context: dict = {}

    @model_validator(mode="before")
    @classmethod
    def parse_session_context(cls, data: Any) -> Any:
        """
        Parses session_context_json (stored as a string in the DB)
        into a dict before validation. Handles both ORM objects
        (attribute access) and plain dicts (e.g. in tests).
        Falls back to {} for legacy sessions with no context,
        and for normal chat sessions where the field is unused.
        """
        raw_json = None

        if hasattr(data, "session_context_json"):
            raw_json = getattr(data, "session_context_json", None)
        elif isinstance(data, dict):
            raw_json = data.get("session_context_json")

        if raw_json:
            try:
                parsed = json.loads(raw_json)
            except (json.JSONDecodeError, TypeError):
                parsed = {}
        else:
            parsed = {}

        # If data is an ORM object, convert to plain dict FastAPI/Pydantic can validate
        if hasattr(data, "__dict__") and not isinstance(data, dict):
            return {
                "id": data.id,
                "topic": data.topic,
                "learning_goal": data.learning_goal,
                "phase": data.phase,
                "turn_count": data.turn_count,
                "session_context": parsed,
            }

        if isinstance(data, dict):
            data = {**data, "session_context": parsed}

        return data

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    phase: str
    turn: int

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    role: str
    content: str
    created_at: datetime
