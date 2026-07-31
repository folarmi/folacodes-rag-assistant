from dataclasses import dataclass
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import (
    EMBEDDING_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    GROQ_TEMPERATURE,
    TOP_K,
    VECTORSTORE_PATH,
)
from app.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


MAX_DISPLAYED_SOURCES = 2
MAX_SOURCE_DISTANCE = 0.85

REFUSAL_MESSAGE = (
    "I could not find enough information in the available "
    "company documents to answer this question."
)


@dataclass
class Source:
    """A document source used to generate an answer."""

    title: str
    section: str
    source: str
    document_type: str
    chunk_id: int | str
    distance: float


@dataclass
class RAGResponse:
    """Response returned by the RAG assistant."""

    question: str
    answer: str
    sources: list[Source]


class RAGService:
    """Retrieve company documents and generate grounded answers."""

    def __init__(self) -> None:
        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is missing. Add it to your .env file."
            )

        if not VECTORSTORE_PATH.exists():
            raise FileNotFoundError(
                f"Vector database not found at {VECTORSTORE_PATH}. "
                "Run `python scripts/ingest.py` first."
            )

        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        self.vectorstore = Chroma(
            collection_name="folacodes_policies",
            persist_directory=str(VECTORSTORE_PATH),
            embedding_function=self.embeddings,
        )

        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model=GROQ_MODEL,
            temperature=GROQ_TEMPERATURE,
        )

    @staticmethod
    def get_section(metadata: dict[str, Any]) -> str:
        """Return the most specific available section heading."""

        return str(
            metadata.get("heading_3")
            or metadata.get("heading_2")
            or metadata.get("heading_1")
            or metadata.get("section")
            or "General"
        )

    def retrieve(
        self,
        question: str,
        top_k: int | None = None,
    ) -> list[tuple[Document, float]]:
        """Retrieve the most relevant document chunks."""

        clean_question = question.strip()

        if not clean_question:
            raise ValueError("Question cannot be empty.")

        return self.vectorstore.similarity_search_with_score(
            clean_question,
            k=top_k or TOP_K,
        )

    def filter_results(
        self,
        results: list[tuple[Document, float]],
    ) -> list[tuple[Document, float]]:
        """
        Remove weak results and limit how many sources are displayed.

        Chroma distance scores are lower when results are more similar.
        """

        filtered_results = [
            (document, distance)
            for document, distance in results
            if distance <= MAX_SOURCE_DISTANCE
        ]

        return filtered_results[:MAX_DISPLAYED_SOURCES]

    def format_context(
        self,
        results: list[tuple[Document, float]],
    ) -> str:
        """Format retrieved documents for the LLM prompt."""

        context_blocks: list[str] = []

        for index, (document, distance) in enumerate(
            results,
            start=1,
        ):
            metadata = document.metadata

            title = metadata.get(
                "title",
                "Unknown document",
            )
            section = self.get_section(metadata)
            source = metadata.get(
                "source",
                "Unknown source",
            )
            document_type = metadata.get(
                "document_type",
                "Unknown",
            )

            context_blocks.append(
                "\n".join(
                    [
                        f"[Source {index}]",
                        f"Title: {title}",
                        f"Section: {section}",
                        f"Document type: {document_type}",
                        f"File: {source}",
                        f"Retrieval distance: {distance:.4f}",
                        "Content:",
                        document.page_content.strip(),
                    ]
                )
            )

        return "\n\n---\n\n".join(context_blocks)

    def build_sources(
        self,
        results: list[tuple[Document, float]],
    ) -> list[Source]:
        """Convert retrieved chunks into structured source records."""

        sources: list[Source] = []

        for document, distance in results:
            metadata = document.metadata

            sources.append(
                Source(
                    title=str(
                        metadata.get(
                            "title",
                            "Unknown document",
                        )
                    ),
                    section=self.get_section(metadata),
                    source=str(
                        metadata.get(
                            "source",
                            "Unknown source",
                        )
                    ),
                    document_type=str(
                        metadata.get(
                            "document_type",
                            "Unknown",
                        )
                    ),
                    chunk_id=metadata.get(
                        "chunk_id",
                        "Unknown",
                    ),
                    distance=float(distance),
                )
            )

        return sources

    def ask(
        self,
        question: str,
        top_k: int | None = None,
    ) -> RAGResponse:
        """Retrieve context and generate a grounded answer."""

        clean_question = question.strip()

        if not clean_question:
            raise ValueError("Question cannot be empty.")

        retrieved_results = self.retrieve(
            clean_question,
            top_k=top_k,
        )

        if not retrieved_results:
            return RAGResponse(
                question=clean_question,
                answer=REFUSAL_MESSAGE,
                sources=[],
            )

        filtered_results = self.filter_results(
            retrieved_results,
        )

        # Give the model the best results even when all candidates are
        # above the display threshold. This allows it to determine
        # whether the available context is sufficient.
        context_results = (
            filtered_results
            if filtered_results
            else retrieved_results[:MAX_DISPLAYED_SOURCES]
        )

        context = self.format_context(context_results)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            context=context,
            question=clean_question,
        )

        response = self.llm.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]
        )

        answer = (
            response.content.strip()
            if isinstance(response.content, str)
            else str(response.content).strip()
        )

        # Do not show weak or irrelevant sources when the model refuses.
        if REFUSAL_MESSAGE.lower() in answer.lower():
            sources: list[Source] = []
        else:
            sources = self.build_sources(filtered_results)

        return RAGResponse(
            question=clean_question,
            answer=answer,
            sources=sources,
        )