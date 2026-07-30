from dataclasses import asdict
from typing import Any

from flask import Blueprint, current_app, jsonify, render_template, request

main_bp = Blueprint("main", __name__)


def get_rag_service() -> Any:
    """Return the RAG service attached to the Flask application."""

    rag_service = current_app.extensions.get("rag_service")

    if rag_service is None:
        raise RuntimeError("RAG service has not been initialized.")

    return rag_service


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

    try:
        rag_service = get_rag_service()
        response = rag_service.ask(question.strip())

        sources = [
            {
                **asdict(source),
                "distance": round(source.distance, 4),
            }
            for source in response.sources
        ]

        return jsonify(
            {
                "question": response.question,
                "answer": response.answer,
                "sources": sources,
            }
        )

    except Exception:
        current_app.logger.exception(
            "Failed to answer question: %s",
            question,
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