"""Command entry point for deterministic Whitfield SOP index rebuilds."""

from core.services.ai.rag.retriever import SOPRetriever


def main() -> None:
    """Rebuild the approved local SOP index and print safe index statistics."""
    retriever = SOPRetriever()
    count = retriever.rebuild_index()
    print(f"Whitfield SOP index ready: {count} chunks")


if __name__ == "__main__":
    main()
