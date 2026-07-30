import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.rag import RAGService  # noqa: E402


def main() -> None:
    try:
        rag = RAGService()
    except (ValueError, FileNotFoundError) as error:
        print(f"Startup error: {error}")
        return

    print("Folacodes RAG Assistant")
    print("Type 'exit' to stop.")

    while True:
        question = input("\nAsk a company question: ").strip()

        if question.lower() in {"exit", "quit"}:
            print("Assistant closed.")
            break

        if not question:
            print("Please enter a question.")
            continue

        try:
            response = rag.ask(question)
        except Exception as error:
            print(f"\nRequest failed: {error}")
            continue

        print("\nAnswer:")
        print(response.answer)

        print("\nRetrieved sources:")

        if not response.sources:
            print("No supporting sources found.")
            continue

        for index, source in enumerate(response.sources, start=1):
            print(
                f"{index}. {source.title} — {source.section}\n"
                f"   File: {source.source}\n"
                f"   Distance: {source.distance:.4f}"
            )


if __name__ == "__main__":
    main()