import json
from pathlib import Path
from typing import Any


def test_home_page_loads(client: Any) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert b"Folacodes" in response.data
    assert b"Company Policy Support" in response.data


def test_health_endpoint(client: Any) -> None:
    response = client.get("/api/health")
    data = response.get_json()

    assert response.status_code == 200
    assert data == {
        "status": "healthy",
        "service": "Folacodes RAG Assistant",
        "rag_ready": True,
    }


def test_ask_returns_answer_and_sources(client: Any) -> None:
    question = "How many annual leave days do employees receive?"

    response = client.post(
        "/api/ask",
        json={"question": question},
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["question"] == question
    assert data["answer"] == (
        "Employees receive 20 working days of paid annual "
        "leave per calendar year."
    )

    assert isinstance(data["id"], str)
    assert data["id"]
    assert isinstance(data["created_at"], str)

    assert len(data["sources"]) == 1

    source = data["sources"][0]

    assert source["title"] == "Leave and Time Off Policy"
    assert source["section"] == "5. Annual Leave"
    assert source["document_type"] == "policy"
    assert source["chunk_id"] == "leave-001"
    assert source["distance"] == 0.5379


def test_ask_strips_question_whitespace(client: Any) -> None:
    response = client.post(
        "/api/ask",
        json={"question": "   How many annual leave days?   "},
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["question"] == "How many annual leave days?"


def test_ask_returns_refusal_without_sources(client: Any) -> None:
    response = client.post(
        "/api/ask",
        json={"question": "What is the cafeteria menu today?"},
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["answer"].startswith(
        "I could not find enough information"
    )
    assert data["sources"] == []


def test_ask_rejects_missing_question(client: Any) -> None:
    response = client.post(
        "/api/ask",
        json={},
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "The 'question' field is required and must be "
        "a non-empty string."
    )


def test_ask_rejects_empty_question(client: Any) -> None:
    response = client.post(
        "/api/ask",
        json={"question": "   "},
    )

    data = response.get_json()

    assert response.status_code == 400
    assert "non-empty string" in data["error"]


def test_ask_rejects_non_string_question(client: Any) -> None:
    response = client.post(
        "/api/ask",
        json={"question": 20},
    )

    data = response.get_json()

    assert response.status_code == 400
    assert "non-empty string" in data["error"]


def test_ask_rejects_non_json_request(client: Any) -> None:
    response = client.post(
        "/api/ask",
        data="question=How many leave days?",
        content_type="application/x-www-form-urlencoded",
    )

    data = response.get_json()

    assert response.status_code == 415
    assert data["error"] == (
        "Request body must be JSON with a 'question' field."
    )


def test_ask_handles_rag_failure(client: Any) -> None:
    response = client.post(
        "/api/ask",
        json={"question": "raise error"},
    )

    data = response.get_json()

    assert response.status_code == 500
    assert data["error"] == (
        "The assistant could not process your question. "
        "Please try again."
    )


def test_successful_question_is_saved_to_history(
    client: Any,
    temporary_storage: dict[str, Path],
) -> None:
    question = "How many annual leave days do employees receive?"

    response = client.post(
        "/api/ask",
        json={"question": question},
    )

    assert response.status_code == 200

    records = json.loads(
        temporary_storage["history"].read_text(
            encoding="utf-8",
        )
    )

    assert len(records) == 1
    assert records[0]["question"] == question
    assert records[0]["sources"][0]["title"] == (
        "Leave and Time Off Policy"
    )


def test_history_endpoint_returns_recent_records(
    client: Any,
) -> None:
    client.post(
        "/api/ask",
        json={"question": "First question"},
    )
    client.post(
        "/api/ask",
        json={"question": "Second question"},
    )

    response = client.get("/api/history")
    data = response.get_json()

    assert response.status_code == 200
    assert len(data["history"]) == 2

    # The newest record should be returned first.
    assert data["history"][0]["question"] == "Second question"
    assert data["history"][1]["question"] == "First question"


def test_feedback_is_saved(
    client: Any,
    temporary_storage: dict[str, Path],
) -> None:
    response = client.post(
        "/api/feedback",
        json={
            "response_id": "response-123",
            "rating": "helpful",
            "question": "How many leave days?",
            "answer": "Employees receive 20 working days.",
        },
    )

    data = response.get_json()

    assert response.status_code == 201
    assert data["message"] == "Feedback saved successfully."
    assert data["feedback"]["rating"] == "helpful"
    assert data["feedback"]["response_id"] == "response-123"

    records = json.loads(
        temporary_storage["feedback"].read_text(
            encoding="utf-8",
        )
    )

    assert len(records) == 1
    assert records[0]["rating"] == "helpful"


def test_feedback_accepts_not_helpful(client: Any) -> None:
    response = client.post(
        "/api/feedback",
        json={
            "response_id": "response-456",
            "rating": "not_helpful",
        },
    )

    assert response.status_code == 201
    assert response.get_json()["feedback"]["rating"] == (
        "not_helpful"
    )


def test_feedback_rejects_invalid_rating(client: Any) -> None:
    response = client.post(
        "/api/feedback",
        json={
            "response_id": "response-123",
            "rating": "average",
        },
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == (
        "Rating must be either 'helpful' or 'not_helpful'."
    )


def test_feedback_requires_response_id(client: Any) -> None:
    response = client.post(
        "/api/feedback",
        json={
            "rating": "helpful",
        },
    )

    data = response.get_json()

    assert response.status_code == 400
    assert data["error"] == "A response ID is required."


def test_feedback_rejects_non_json_request(client: Any) -> None:
    response = client.post(
        "/api/feedback",
        data="rating=helpful",
        content_type="application/x-www-form-urlencoded",
    )

    assert response.status_code == 415
    assert response.get_json()["error"] == (
        "Request body must be JSON."
    )