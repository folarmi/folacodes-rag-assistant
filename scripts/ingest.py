from datetime import date, datetime
from typing import Any

import shutil
import sys
from pathlib import Path
from typing import Any

import yaml
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import (  # noqa: E402
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DOCUMENTS_PATH,
    EMBEDDING_MODEL,
    VECTORSTORE_PATH,
)


def parse_front_matter(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML front matter and return metadata plus Markdown body."""

    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)

    if len(parts) < 3:
        return {}, content

    raw_metadata = parts[1]
    body = parts[2].strip()

    metadata = yaml.safe_load(raw_metadata) or {}

    if not isinstance(metadata, dict):
        metadata = {}

    return metadata, body

def sanitize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Convert metadata into values supported by ChromaDB.

    Chroma supports scalar metadata such as strings, integers,
    floats and booleans. YAML dates are converted to ISO strings.
    """

    sanitized: dict[str, Any] = {}

    for key, value in metadata.items():
        if value is None:
            continue

        if isinstance(value, (date, datetime)):
            sanitized[key] = value.isoformat()
        elif isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
        elif isinstance(value, list):
            sanitized[key] = ", ".join(str(item) for item in value)
        else:
            sanitized[key] = str(value)

    return sanitized

def load_markdown_documents(directory: Path) -> list[Document]:
    """Recursively load Markdown files from the documents directory."""

    documents: list[Document] = []

    for file_path in sorted(directory.rglob("*.md")):
        content = file_path.read_text(encoding="utf-8")
        metadata, body = parse_front_matter(content)

        relative_path = file_path.relative_to(PROJECT_ROOT)

        metadata.update(
          {
        "source": str(relative_path),
        "filename": file_path.name,
        "document_type": (
            "knowledge"
            if file_path.parent.name == "knowledge"
            else "form"
            if file_path.parent.name == "forms"
            else "policy"
        ),
    }
        )

        documents.append(
            Document(
                page_content=body,
                metadata=metadata,
            )
        )

    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    """Split documents by Markdown headings, then by character length."""

    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "heading_1"),
            ("##", "heading_2"),
            ("###", "heading_3"),
        ],
        strip_headers=False,
    )

    size_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[Document] = []

    for document in documents:
        header_sections = header_splitter.split_text(document.page_content)

        for section in header_sections:
            combined_metadata = sanitize_metadata(
                {
                **document.metadata,
                **section.metadata,
                }
            ) 

            section_document = Document(
                page_content=section.page_content,
                metadata=combined_metadata,
            )

            section_chunks = size_splitter.split_documents([section_document])
            chunks.extend(section_chunks)

    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = index

    return chunks


def build_vectorstore(chunks: list[Document]) -> Chroma:
    """Generate embeddings and persist them in ChromaDB."""

    if VECTORSTORE_PATH.exists():
        shutil.rmtree(VECTORSTORE_PATH)

    VECTORSTORE_PATH.mkdir(parents=True, exist_ok=True)

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(VECTORSTORE_PATH),
        collection_name="folacodes_policies",
    )

    return vectorstore


def main() -> None:
    if not DOCUMENTS_PATH.exists():
        raise FileNotFoundError(
            f"Documents folder not found: {DOCUMENTS_PATH}"
        )

    documents = load_markdown_documents(DOCUMENTS_PATH)

    if not documents:
        raise RuntimeError("No Markdown documents were found.")

    chunks = split_documents(documents)
    build_vectorstore(chunks)

    print(f"Loaded documents: {len(documents)}")
    print(f"Created chunks: {len(chunks)}")
    print(f"Vector database: {VECTORSTORE_PATH}")

    print("\nSample chunk metadata:")
    for chunk in chunks[:3]:
        print(chunk.metadata)


if __name__ == "__main__":
    main()