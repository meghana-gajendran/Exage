from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from typing import List
from database import get_db
from models import Session, Message, AgentTrace
from schemas import SessionCreate, SessionResponse, MessageResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.get("/", response_model=List[SessionResponse])
def get_all_sessions(db: DBSession = Depends(get_db)):
    return db.query(Session).order_by(Session.created_at).all()

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.get("/{session_id}/messages", response_model=List[MessageResponse])
def get_messages(session_id: str, db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at).all()

@router.post("/", response_model=SessionResponse)
def create_session(body: SessionCreate, db: DBSession = Depends(get_db)):
    session = Session(topic=body.topic, learning_goal=body.learning_goal)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.delete("/{session_id}")
def delete_session(session_id: str, db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # Delete related records first
    db.query(AgentTrace).filter(AgentTrace.session_id == session_id).delete()
    db.query(Message).filter(Message.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return {"deleted": session_id}
