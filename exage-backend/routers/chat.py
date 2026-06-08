import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession
from database import get_db
from models import Session
from pipeline.runner import run_pipeline_streaming
from schemas import ChatRequest

router = APIRouter(prefix="/sessions", tags=["chat"])

@router.post("/{session_id}/chat")
async def chat(session_id: str, body: ChatRequest, db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_stream():
        try:
            async for event in run_pipeline_streaming(session, body.message, db):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            # Send error event so frontend can handle it gracefully
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
