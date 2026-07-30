from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, render_template, request

from app.storage import (
    CHAT_HISTORY_FILE,
    FEEDBACK_FILE,
    append_json_record,
    read_json_list,
)


main_bp = Blueprint("main", __name__)


def get_rag_service() -> Any:
    """Return the RAG service attached to the Flask application."""

    rag_service = current_app.extensions.get("rag_service")

    if rag_service is None:
        raise RuntimeError("RAG service has not been initialized.")

    return rag_service


def utc_timestamp() -> str:
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()


@main_bp.get("/")
def index():
    """Render the assistant web interface."""

    return render_template("index.html")


@main_bp.get("/api/health")
def health():
    """Return the application health status."""

    rag_service = current_app.extensions.get("rag_service")

    return jsonify(
        {
            "status": "healthy",
            "service": "Folacodes RAG Assistant",
            "rag_ready": rag_service is not None,
        }
    )


@main_bp.get("/api/history")
def get_history():
    """Return the most recent saved conversations."""

    history = read_json_list(CHAT_HISTORY_FILE)

    recent_history = list(reversed(history[-10:]))

    return jsonify(
        {
            "history": recent_history,
        }
    )


@main_bp.post("/api/ask")
def ask():
    """Answer a company policy question."""

    if not request.is_json:
        return (
            jsonify(
                {
                    "error": (
                        "Request body must be JSON with a 'question' field."
                    )
                }
            ),
            415,
        )

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON request body."}), 400

    question = payload.get("question")

    if not isinstance(question, str) or not question.strip():
        return (
            jsonify(
                {
                    "error": (
                        "The 'question' field is required and must be "
                        "a non-empty string."
                    )
                }
            ),
            400,
        )

    clean_question = question.strip()

    try:
        rag_service = get_rag_service()
        response = rag_service.ask(clean_question)

        response_id = str(uuid4())
        created_at = utc_timestamp()

        sources = [
            {
                **asdict(source),
                "distance": round(source.distance, 4),
            }
            for source in response.sources
        ]

        history_record = {
            "id": response_id,
            "question": response.question,
            "answer": response.answer,
            "sources": sources,
            "created_at": created_at,
        }

        append_json_record(
            CHAT_HISTORY_FILE,
            history_record,
            maximum_records=100,
        )

        return jsonify(history_record)

    except Exception:
        current_app.logger.exception(
            "Failed to answer question: %s",
            clean_question,
        )

        return (
            jsonify(
                {
                    "error": (
                        "The assistant could not process your question. "
                        "Please try again."
                    )
                }
            ),
            500,
        )


@main_bp.post("/api/feedback")
def save_feedback():
    """Save user feedback for an assistant response."""

    if not request.is_json:
        return jsonify({"error": "Request body must be JSON."}), 415

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid JSON request body."}), 400

    response_id = payload.get("response_id")
    rating = payload.get("rating")
    question = payload.get("question")
    answer = payload.get("answer")

    if not isinstance(response_id, str) or not response_id.strip():
        return jsonify({"error": "A response ID is required."}), 400

    if rating not in {"helpful", "not_helpful"}:
        return (
            jsonify(
                {
                    "error": (
                        "Rating must be either 'helpful' or 'not_helpful'."
                    )
                }
            ),
            400,
        )

    feedback_record = {
        "id": str(uuid4()),
        "response_id": response_id.strip(),
        "rating": rating,
        "question": question if isinstance(question, str) else "",
        "answer": answer if isinstance(answer, str) else "",
        "created_at": utc_timestamp(),
    }

    append_json_record(
        FEEDBACK_FILE,
        feedback_record,
        maximum_records=1000,
    )

    return (
        jsonify(
            {
                "message": "Feedback saved successfully.",
                "feedback": feedback_record,
            }
        ),
        201,
    )