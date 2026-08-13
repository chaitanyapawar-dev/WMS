"""Persistent ChromaDB store for approved Whitfield SOP chunks."""

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from core import logger
from core.services.ai.rag.document_loader import SOPChunk
from core.services.ai.rag.embeddings import embed_documents, embed_query

logging = logger(__name__)
VECTOR_DIRECTORY = Path(__file__).resolve().parents[4] / "vector_store" / "whitfield_sops"
COLLECTION_NAME = "whitfield_sops"


class SOPVectorStore:
    """Persist and query approved SOP chunk embeddings only."""

    def __init__(self, persist_directory: Path = VECTOR_DIRECTORY) -> None:
        """Initialize the server-controlled persistent SOP collection.

        Args:
            persist_directory: Local Chroma persistence directory.
        """
        logging.info("Executing SOPVectorStore.__init__")
        persist_directory.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, chunks: list[SOPChunk]) -> int:
        """Embed and upsert stable SOP chunks without duplicate growth.

        Args:
            chunks: Approved section-aware SOP chunks.

        Returns:
            int: Number of chunks indexed.
        """
        if not chunks:
            return 0
        documents = [_document_for_embedding(chunk) for chunk in chunks]
        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=documents,
            metadatas=[{"source": chunk.source, "title": chunk.title, "section": chunk.section} for chunk in chunks],
            embeddings=embed_documents(documents),
        )
        logging.info(f"Indexed approved SOP chunks: {len(chunks)}")
        return len(chunks)

    def count(self) -> int:
        """Return the current persistent SOP chunk count.

        Returns:
            int: Indexed chunk count.
        """
        return self.collection.count()

    def query(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Search approved SOP chunks using local semantic vectors.

        Args:
            query: Natural-language SOP question.
            top_k: Bounded number of matches to return.

        Returns:
            list[dict[str, Any]]: Match content, safe metadata, and cosine distance.
        """
        if self.count() == 0:
            return []
        result = self.collection.query(
            query_embeddings=[embed_query(query)],
            n_results=min(top_k, self.count()),
            include=["documents", "metadatas", "distances"],
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            {
                "content": document,
                "source": metadata["source"],
                "title": metadata["title"],
                "section": metadata["section"],
                "distance": float(distance),
            }
            for document, metadata, distance in zip(documents, metadatas, distances)
        ]


def _document_for_embedding(chunk: SOPChunk) -> str:
    """Attach approved title and section context to one stored SOP passage.

    Args:
        chunk: Approved SOP chunk to place in the local vector collection.

    Returns:
        str: Context-rich, approved text for semantic retrieval and grounding.
    """
    return f"SOP: {chunk.title}\nSection: {chunk.section}\n\n{chunk.text}"
