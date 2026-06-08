from pydantic import BaseModel, ConfigDict
from datetime import datetime

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

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    phase: str
    turn: int

# B3 fix: schema for returning message history
class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    role: str
    content: str
    created_at: datetime
