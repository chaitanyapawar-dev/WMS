"""Bounded retrieval and missing-evidence decisions for Whitfield SOPs."""

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from core import logger
from core.services.ai.rag.document_loader import load_sop_chunks
from core.services.ai.rag.vector_store import SOPVectorStore

logging = logger(__name__)
TOP_K = 3
# Calibrated against the required supported and unsupported MVP question set.
MAX_RELEVANT_DISTANCE = 0.67


@dataclass(frozen=True)
class SOPRetrievalResult:
    """Represent a bounded RAG lookup result without internal vector details."""

    found: bool
    matches: list[dict[str, Any]]


class SOPRetriever:
    """Retrieve approved SOP context from the local persistent collection."""

    def __init__(self) -> None:
        """Initialize the local SOP vector-store facade."""
        logging.info("Executing SOPRetriever.__init__")
        self.store = SOPVectorStore()

    def ensure_index(self) -> int:
        """Build the SOP index only when it is missing.

        Returns:
            int: Current indexed chunk count.
        """
        if self.store.count() == 0:
            self.store.upsert(load_sop_chunks())
        return self.store.count()

    def rebuild_index(self) -> int:
        """Upsert every approved SOP chunk using stable IDs for safe rebuilds.

        Returns:
            int: Indexed chunk count after rebuild.
        """
        return self.store.upsert(load_sop_chunks())

    def retrieve(self, query: str, top_k: int = TOP_K) -> SOPRetrievalResult:
        """Return relevant approved SOP evidence or an honest no-source result.

        Args:
            query: Natural-language SOP question.
            top_k: Maximum relevant matches to return.

        Returns:
            SOPRetrievalResult: Relevant approved evidence, if any.
        """
        self.ensure_index()
        matches = [item for item in self.store.query(query, top_k) if item["distance"] <= MAX_RELEVANT_DISTANCE]
        logging.info(f"SOP retrieval completed matches={len(matches)}")
        return SOPRetrievalResult(found=bool(matches), matches=matches)


@lru_cache(maxsize=1)
def get_sop_retriever() -> SOPRetriever:
    """Return the process-local retriever backed by persistent SOP storage.

    Returns:
        SOPRetriever: Cached retriever for approved warehouse SOPs.
    """
    return SOPRetriever()
