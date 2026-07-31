from typing import Any

from langchain_core.documents import Document

from app.rag import RAGService


def make_document(
    title: str,
    content: str,
    **metadata: Any,
) -> Document:
    return Document(
        page_content=content,
        metadata={
            "title": title,
            "source": metadata.pop(
                "source",
                "documents/test.md",
            ),
            **metadata,
        },
    )


def test_get_section_prefers_heading_3() -> None:
    metadata = {
        "heading_1": "Leave",
        "heading_2": "Annual Leave",
        "heading_3": "Leave Entitlement",
    }

    section = RAGService.get_section(metadata)

    assert section == "Leave Entitlement"


def test_get_section_falls_back_to_heading_2() -> None:
    metadata = {
        "heading_1": "Leave",
        "heading_2": "Annual Leave",
    }

    section = RAGService.get_section(metadata)

    assert section == "Annual Leave"


def test_get_section_returns_general_when_missing() -> None:
    assert RAGService.get_section({}) == "General"


def test_filter_results_removes_weak_sources() -> None:
    service = object.__new__(RAGService)

    results = [
        (
            make_document(
                "Leave Policy",
                "Employees receive annual leave.",
            ),
            0.45,
        ),
        (
            make_document(
                "Glossary",
                "Annual leave is paid time off.",
            ),
            0.72,
        ),
        (
            make_document(
                "Sick Leave",
                "Employees receive sick leave.",
            ),
            0.91,
        ),
    ]

    filtered = service.filter_results(results)

    assert len(filtered) == 2
    assert filtered[0][1] == 0.45
    assert filtered[1][1] == 0.72


def test_filter_results_limits_displayed_sources() -> None:
    service = object.__new__(RAGService)

    results = [
        (make_document("One", "Content one"), 0.30),
        (make_document("Two", "Content two"), 0.40),
        (make_document("Three", "Content three"), 0.50),
    ]

    filtered = service.filter_results(results)

    assert len(filtered) == 2


def test_filter_results_returns_empty_for_weak_results() -> None:
    service = object.__new__(RAGService)

    results = [
        (make_document("One", "Content one"), 1.10),
        (make_document("Two", "Content two"), 1.20),
    ]

    filtered = service.filter_results(results)

    assert filtered == []


def test_format_context_contains_source_labels() -> None:
    service = object.__new__(RAGService)

    results = [
        (
            make_document(
                "Leave and Time Off Policy",
                "Employees receive 20 working days.",
                heading_2="5. Annual Leave",
                source="documents/leave.md",
            ),
            0.42,
        )
    ]

    context = service.format_context(results)

    assert "[Source 1]" in context
    assert "Title: Leave and Time Off Policy" in context
    assert "Section: 5. Annual Leave" in context
    assert "File: documents/leave.md" in context
    assert "Employees receive 20 working days." in context


def test_build_sources_maps_document_metadata() -> None:
    service = object.__new__(RAGService)

    document = make_document(
        "Leave and Time Off Policy",
        "Employees receive 20 working days.",
        heading_2="5. Annual Leave",
        source="documents/leave.md",
        document_type="policy",
        chunk_id="chunk-001",
    )

    sources = service.build_sources([(document, 0.53789)])

    assert len(sources) == 1

    source = sources[0]

    assert source.title == "Leave and Time Off Policy"
    assert source.section == "5. Annual Leave"
    assert source.source == "documents/leave.md"
    assert source.document_type == "policy"
    assert source.chunk_id == "chunk-001"
    assert source.distance == 0.53789