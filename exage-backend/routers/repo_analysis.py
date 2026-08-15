"""
Repo Analysis router — Option 2 API endpoints.

POST /repo-analysis/anecdotes   Generate curiosity breaker anecdotes for ranked gaps
POST /repo-analysis/            Run the full Option 2 pipeline
POST /repo-analysis/stream      Stream pipeline with SSE status events
POST /repo-analysis/create-session  Create Option 1 session from analysis
"""

import json
import asyncio
import traceback
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from typing import Optional

from database import get_db
from repo_agents.pipeline_v2 import (
    run_option2_pipeline,
    result_to_session_context,
    RepoAnalysisResult,
)
from chat_agents.curiosity_breaker import run_curiosity_breaker
from models import Session as ChatSession, Message

router = APIRouter(prefix="/repo-analysis", tags=["repo-analysis"])


class RepoAnalysisRequest(BaseModel):
    repo_input: str
    learning_goal: str
    github_token: Optional[str] = None


class RankedGapRequest(BaseModel):
    concept: str
    consequence_for_goal: str
    gap_category: str


class AnecdotesRequest(BaseModel):
    gaps: list[RankedGapRequest]
    learning_goal: str
    domain: str
    framework_context: str


class AnecdoteItem(BaseModel):
    concept: str
    anecdote: str


class AnecdotesResponse(BaseModel):
    anecdotes: list[AnecdoteItem]


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


@router.post("/anecdotes", response_model=AnecdotesResponse)
async def generate_anecdotes(body: AnecdotesRequest):
    """
    Generate one curiosity breaker anecdote per ranked gap.
    Called after the analysis report is shown — generates anecdotes
    in parallel for all gaps and returns them together.
    """
    async def generate_one(gap: RankedGapRequest) -> AnecdoteItem:
        anecdote, _ = await run_curiosity_breaker(
            concept=gap.concept,
            learning_goal=body.learning_goal,
            domain=body.domain,
            repo_context=body.framework_context,
        )
        return AnecdoteItem(concept=gap.concept, anecdote=anecdote)

    # Generate all anecdotes in parallel
    anecdotes = await asyncio.gather(*[generate_one(gap) for gap in body.gaps])

    return AnecdotesResponse(anecdotes=list(anecdotes))


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
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/create-session")
async def create_session_from_analysis(
    session_context: dict,
    db: DBSession = Depends(get_db),
):
    """
    Creates an Option 1 chat session pre-loaded with repo gaps.
    Now supports creating a session for a SINGLE selected gap
    (when learner clicks "Probe this gap" on one specific gap card)
    as well as all gaps at once.
    """
    repo_ctx = session_context.get("repo_context", {})
    repo_name = repo_ctx.get("repo_name", "your repository")
    probing_questions = repo_ctx.get("probing_questions", [])
    first_question = probing_questions[0] if probing_questions else None

    if first_question:
        opening_message = f"I've analysed your {repo_name} repository. {first_question}"
    else:
        topic = session_context.get("topic", "this topic")
        opening_message = (
            f"I've analysed your {repo_name} repository. "
            f"Walk me through what you understand about {topic}."
        )

    session = ChatSession(
        topic=session_context.get("topic", ""),
        learning_goal=session_context.get("learning_goal", "curiosity"),
        phase="probing",
        known_concepts_json=json.dumps(session_context.get("known_concepts", [])),
        asked_gaps_json=json.dumps([]),
        open_gaps_json=json.dumps(session_context.get("open_gaps", [])),
        misconceptions_json=json.dumps([]),
        session_context_json=json.dumps(session_context),
    )
    db.add(session)
    db.flush()

    opening_msg = Message(
        session_id=session.id,
        role="assistant",
        content=opening_message,
    )
    db.add(opening_msg)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "topic": session.topic,
        "phase": session.phase,
        "opening_message": opening_message,
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
