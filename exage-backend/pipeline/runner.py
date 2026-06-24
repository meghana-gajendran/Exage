import json
from typing import AsyncGenerator
from sqlalchemy.orm import Session as DBSession
from models import Session, Message, AgentTrace
from chat_agents.concept_extractor import run_concept_extractor
from chat_agents.gap_detector import run_gap_detector
from chat_agents.question_generator import run_question_generator
from chat_agents.response_composer import run_response_composer
from chat_agents.synthesis_agent import run_synthesis_agent
from chat_agents.evaluation_agent import run_evaluation_agent

SYNTHESIS_TRIGGER_TURNS = 8
SYNTHESIS_KEYWORDS = {"done", "wrap up", "wrapup", "finish", "summarize", "summary", "that's all", "thats all", "end session"}


def _is_synthesis_trigger(message: str, turn_count: int) -> bool:
    lowered = message.strip().lower()
    if any(kw in lowered for kw in SYNTHESIS_KEYWORDS):
        return True
    if turn_count >= SYNTHESIS_TRIGGER_TURNS:
        return True
    return False


async def run_pipeline_streaming(
    session: Session,
    user_message: str,
    db: DBSession
) -> AsyncGenerator[dict, None]:

    known_concepts = json.loads(session.known_concepts_json)
    asked_gaps = json.loads(session.asked_gaps_json)
    open_gaps = json.loads(session.open_gaps_json)
    misconceptions = json.loads(session.misconceptions_json)
    history = [{"role": m.role, "content": m.content} for m in session.messages]
    traces = []

    # --- Check for synthesis trigger ---
    if _is_synthesis_trigger(user_message, session.turn_count):
        yield {"type": "status", "text": "Preparing your session summary…"}

        # Run evaluation on last turn if we have history
        if len(history) >= 2:
            last_question = next(
                (m["content"] for m in reversed(history) if m["role"] == "assistant"), ""
            )
            eval_out, eval_latency = await run_evaluation_agent(
                question_asked=last_question,
                learner_response=user_message,
                targeted_gap=asked_gaps[-1] if asked_gaps else "general understanding",
            )
            traces.append(("evaluation_agent", {}, eval_out, eval_latency))

        yield {"type": "status", "text": "Building synthesis…"}

        all_gaps_ever = json.loads(session.open_gaps_json)
        synthesis_out, latency = await run_synthesis_agent(
            topic=session.topic,
            learning_goal=session.learning_goal,
            all_gaps=all_gaps_ever,
            misconceptions=misconceptions,
            conversation_history=history,
        )
        traces.append(("synthesis_agent", {}, synthesis_out, latency))

        # Persist
        db.add(Message(session_id=session.id, role="user", content=user_message))
        db.add(Message(session_id=session.id, role="assistant", content=json.dumps(synthesis_out)))
        for agent_name, inp, out, lat in traces:
            db.add(AgentTrace(
                session_id=session.id,
                turn_number=session.turn_count + 1,
                agent_name=agent_name,
                input_json=json.dumps(inp),
                output_json=json.dumps(out),
                latency_ms=lat,
            ))

        session.phase = "synthesis"
        session.turn_count += 1
        db.commit()

        yield {
            "type": "synthesis",
            "data": synthesis_out,
            "phase": "synthesis",
            "turn": session.turn_count,
        }
        return

    # --- Normal probing pipeline ---
    yield {"type": "status", "text": "Analyzing your explanation…"}
    extractor_input = {"topic": session.topic, "message": user_message}
    extractor_out, latency = await run_concept_extractor(
        topic=session.topic, message=user_message
    )
    traces.append(("concept_extractor", extractor_input, extractor_out, latency))
    known_concepts = list(set(known_concepts + extractor_out.get("stated_concepts", [])))

    yield {"type": "status", "text": "Detecting gaps…"}
    detector_input = {
        "topic": session.topic,
        "stated_concepts": extractor_out.get("stated_concepts", []),
        "learning_goal": session.learning_goal,
        "asked_gaps": asked_gaps,
    }
    detector_out, latency = await run_gap_detector(**detector_input)
    traces.append(("gap_detector", detector_input, detector_out, latency))
    open_gaps = detector_out.get("missing_concepts", [])
    misconceptions = list(set(misconceptions + [
        m["concept"] for m in detector_out.get("likely_misconceptions", [])
    ]))

    # Run evaluation on previous turn if we have enough history
    if len(history) >= 2:
        last_question = next(
            (m["content"] for m in reversed(history) if m["role"] == "assistant"), ""
        )
        if last_question and asked_gaps:
            eval_out, eval_latency = await run_evaluation_agent(
                question_asked=last_question,
                learner_response=user_message,
                targeted_gap=asked_gaps[-1] if asked_gaps else "general understanding",
            )
            traces.append(("evaluation_agent", {}, eval_out, eval_latency))

    yield {"type": "status", "text": "Forming a question…"}
    generator_input = {
        "missing_concepts": open_gaps,
        "likely_misconceptions": detector_out.get("likely_misconceptions", []),
        "learning_goal": session.learning_goal,
        "conversation_history": history,
    }
    generator_out, latency = await run_question_generator(**generator_input)
    traces.append(("question_generator", generator_input, generator_out, latency))
    ranked_questions = generator_out.get("questions", [])

    yield {"type": "status", "text": "Composing response…"}
    composer_input = {
        "ranked_questions": ranked_questions,
        "conversation_history": history,
        "learner_last_message": user_message,
    }
    response_text, latency = await run_response_composer(**composer_input)
    traces.append(("response_composer", composer_input, {"response": response_text}, latency))

    # Stream tokens
    words = response_text.split(" ")
    for i, word in enumerate(words):
        token = word if i == len(words) - 1 else word + " "
        yield {"type": "token", "text": token}

    # Persist
    db.add(Message(session_id=session.id, role="user", content=user_message))
    db.add(Message(session_id=session.id, role="assistant", content=response_text))
    for agent_name, inp, out, lat in traces:
        db.add(AgentTrace(
            session_id=session.id,
            turn_number=session.turn_count + 1,
            agent_name=agent_name,
            input_json=json.dumps(inp),
            output_json=json.dumps(out),
            latency_ms=lat,
        ))

    session.known_concepts_json = json.dumps(known_concepts)
    session.asked_gaps_json = json.dumps(asked_gaps + [g["concept"] for g in open_gaps[:2]])
    session.open_gaps_json = json.dumps(open_gaps)
    session.misconceptions_json = json.dumps(misconceptions)
    session.turn_count += 1
    if session.turn_count >= 2 and session.phase == "onboarding":
        session.phase = "probing"

    db.commit()

    yield {
        "type": "done",
        "phase": session.phase,
        "turn": session.turn_count,
        "gaps": open_gaps,
    }


async def run_pipeline(session: Session, user_message: str, db: DBSession) -> str:
    response_text = ""
    async for event in run_pipeline_streaming(session, user_message, db):
        if event["type"] == "token":
            response_text += event["text"]
    return response_text
