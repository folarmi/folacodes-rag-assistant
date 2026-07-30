import sys
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import (  # noqa: E402
    EMBEDDING_MODEL,
    TOP_K,
    VECTORSTORE_PATH,
)


def get_heading(metadata: dict) -> str:
    """Return the most specific available Markdown heading."""

    return (
        metadata.get("heading_3")
        or metadata.get("heading_2")
        or metadata.get("heading_1")
        or "Unknown section"
    )


def main() -> None:
    if not VECTORSTORE_PATH.exists():
        raise FileNotFoundError(
            f"Vector database not found at: {VECTORSTORE_PATH}\n"
            "Run `python scripts/ingest.py` first."
        )

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    vectorstore = Chroma(
        collection_name="folacodes_policies",
        persist_directory=str(VECTORSTORE_PATH),
        embedding_function=embeddings,
    )

    print("Folacodes retrieval test")
    print("Type 'exit' to stop.")

    while True:
        query = input("\nAsk a policy question: ").strip()

        if query.lower() in {"exit", "quit"}:
            print("Retrieval test closed.")
            break

        if not query:
            print("Please enter a question.")
            continue

        results = vectorstore.similarity_search_with_score(
            query,
            k=TOP_K,
        )

        if not results:
            print("No matching documents were found.")
            continue

        for index, (document, score) in enumerate(results, start=1):
            metadata = document.metadata

            title = metadata.get("title", "Unknown document")
            source = metadata.get("source", "Unknown source")
            document_type = metadata.get("document_type", "Unknown")
            heading = get_heading(metadata)
            chunk_id = metadata.get("chunk_id", "Unknown")

            print(f"\n--- Result {index} ---")
            print(f"Distance score: {score:.4f}")
            print(f"Title: {title}")
            print(f"Section: {heading}")
            print(f"Document type: {document_type}")
            print(f"Chunk ID: {chunk_id}")
            print(f"Source: {source}")
            print("\nContent:")
            print(document.page_content[:700])

            if len(document.page_content) > 700:
                print("...")


if __name__ == "__main__":
    main()