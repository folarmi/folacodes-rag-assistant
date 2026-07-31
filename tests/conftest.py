from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

import app.routes as routes_module
from app.app import create_app


@dataclass
class FakeSource:
    title: str
    section: str
    source: str
    document_type: str
    chunk_id: str
    distance: float


@dataclass
class FakeRAGResponse:
    question: str
    answer: str
    sources: list[FakeSource]


class FakeRAGService:
    """Predictable RAG service used during API tests."""

    def ask(self, question: str) -> FakeRAGResponse:
        if question == "raise error":
            raise RuntimeError("Simulated RAG failure")

        refusal = (
            "I could not find enough information in the available "
            "company documents to answer this question."
        )

        if "cafeteria" in question.lower():
            return FakeRAGResponse(
                question=question,
                answer=refusal,
                sources=[],
            )

        return FakeRAGResponse(
            question=question,
            answer=(
                "Employees receive 20 working days of paid annual "
                "leave per calendar year."
            ),
            sources=[
                FakeSource(
                    title="Leave and Time Off Policy",
                    section="5. Annual Leave",
                    source=(
                        "documents/"
                        "04_Leave_and_Time_Off_Policy.md"
                    ),
                    document_type="policy",
                    chunk_id="leave-001",
                    distance=0.5379,
                )
            ],
        )


@pytest.fixture
def temporary_storage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Path]:
    """Redirect storage to temporary test files."""

    history_file = tmp_path / "chat_history.json"
    feedback_file = tmp_path / "feedback.json"

    history_file.write_text("[]", encoding="utf-8")
    feedback_file.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(
        routes_module,
        "CHAT_HISTORY_FILE",
        history_file,
    )

    monkeypatch.setattr(
        routes_module,
        "FEEDBACK_FILE",
        feedback_file,
    )

    return {
        "history": history_file,
        "feedback": feedback_file,
    }


@pytest.fixture
def app(temporary_storage: dict[str, Path]) -> Any:
    """Create a Flask application configured for testing."""

    flask_app = create_app(
        test_config={
            "TESTING": True,
        },
        rag_service=FakeRAGService(),
    )

    yield flask_app


@pytest.fixture
def client(app: Any) -> Any:
    """Return Flask's test client."""

    return app.test_client()