"""
Repo Analysis router — Option 2 API endpoints.

POST /repo-analysis        Run the full Option 2 pipeline
POST /repo-analysis/stream Stream pipeline with SSE status events
POST /repo-analysis/create-session  Create Option 1 session from analysis
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from typing import Optional

from database import get_db
from agents_option2.pipeline_v2 import (
    run_option2_pipeline,
    result_to_session_context,
    RepoAnalysisResult,
)
from models import Session as ChatSession

router = APIRouter(prefix="/repo-analysis", tags=["repo-analysis"])


class RepoAnalysisRequest(BaseModel):
    repo_input: str
    learning_goal: str
    github_token: Optional[str] = None


class RankedGapResponse(BaseModel):
    rank: int
    concept: str
    gap_type: str
    gap_category: str
    consequence_for_goal: str
    urgency: str
    probing_question: str
    what_a_good_answer_shows: str


class RepoAnalysisResponse(BaseModel):
    repo_name: str
    input_type: str
    learning_goal: str
    frameworks: list[str]
    framework_context: str
    domain: str
    overall_assessment: str
    strongest_areas: list[str]
    weakest_signals: list[str]
    ranked_gaps: list[RankedGapResponse]
    analysis_summary: str
    technology_coverage_score: int
    session_context: dict


@router.post("/", response_model=RepoAnalysisResponse)
async def analyse_repo(body: RepoAnalysisRequest):
    result: RepoAnalysisResult = await run_option2_pipeline(
        repo_input=body.repo_input,
        learning_goal=body.learning_goal,
        github_token=body.github_token,
    )
    if result.error:
        raise HTTPException(status_code=400, detail=result.error)

    return _build_response(result)


@router.post("/stream")
async def analyse_repo_stream(body: RepoAnalysisRequest):
    async def event_stream():
        try:
            yield f"data: {json.dumps({'type': 'status', 'text': 'Reading repository…'})}\n\n"
            yield f"data: {json.dumps({'type': 'status', 'text': 'Extracting concepts from code…'})}\n\n"

            result = await run_option2_pipeline(
                repo_input=body.repo_input,
                learning_goal=body.learning_goal,
                github_token=body.github_token,
            )

            if result.error:
                yield f"data: {json.dumps({'type': 'error', 'text': result.error})}\n\n"
                return

            yield f"data: {json.dumps({'type': 'status', 'text': 'Ranking gaps…'})}\n\n"
            payload = _build_response(result)
            yield f"data: {json.dumps({'type': 'done', 'result': payload.model_dump()})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/create-session")
async def create_session_from_analysis(
    session_context: dict,
    db: DBSession = Depends(get_db),
):
    """
    Creates an Option 1 chat session pre-loaded with repo gaps.
    Returns session_id + the opening message to show the learner.
    """
    repo_ctx = session_context.get("repo_context", {})
    repo_name = repo_ctx.get("repo_name", "your repository")
    probing_questions = repo_ctx.get("probing_questions", [])
    first_question = probing_questions[0] if probing_questions else None

    # Build a contextual opening message referencing the repo and first gap
    if first_question:
        opening_message = (
            f"I've analysed your {repo_name} repository. "
            f"{first_question}"
        )
    else:
        topic = session_context.get("topic", "this topic")
        opening_message = f"I've analysed your {repo_name} repository. Walk me through what you understand about {topic}."

    session = ChatSession(
        topic=session_context.get("topic", ""),
        learning_goal=session_context.get("learning_goal", "curiosity"),
        phase="probing",
        known_concepts_json=json.dumps(session_context.get("known_concepts", [])),
        asked_gaps_json=json.dumps([]),
        open_gaps_json=json.dumps(session_context.get("open_gaps", [])),
        misconceptions_json=json.dumps([]),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "topic": session.topic,
        "phase": session.phase,
        "opening_message": opening_message,  # ← new field
    }


def _build_response(result: RepoAnalysisResult) -> RepoAnalysisResponse:
    return RepoAnalysisResponse(
        repo_name=result.repo_name,
        input_type=result.input_type,
        learning_goal=result.learning_goal,
        frameworks=result.frameworks,
        framework_context=result.framework_context,
        domain=result.domain,
        overall_assessment=result.overall_assessment,
        strongest_areas=result.strongest_areas,
        weakest_signals=result.weakest_signals,
        ranked_gaps=[
            RankedGapResponse(
                rank=g.rank,
                concept=g.concept,
                gap_type=g.gap_type,
                gap_category=g.gap_category,
                consequence_for_goal=g.consequence_for_goal,
                urgency=g.urgency,
                probing_question=g.probing_question,
                what_a_good_answer_shows=g.what_a_good_answer_shows,
            )
            for g in result.ranked_gaps
        ],
        analysis_summary=result.analysis_summary,
        technology_coverage_score=result.technology_coverage_score,
        session_context=result_to_session_context(result),
    )
