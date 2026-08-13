"""Cached local SentenceTransformers embeddings for the SOP corpus."""

from functools import lru_cache
from typing import Sequence

from core import logger

logging = logger(__name__)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    """Load the local embedding model once per backend process.

    Returns:
        SentenceTransformer: Cached model used for document and query vectors.
    """
    logging.info("Loading local Whitfield SOP embedding model")
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def embed_documents(texts: Sequence[str]) -> list[list[float]]:
    """Create normalized vectors for SOP chunks.

    Args:
        texts: Approved SOP chunk text.

    Returns:
        list[list[float]]: Local normalized embedding vectors.
    """
    if not texts:
        return []
    return get_embedding_model().encode(list(texts), normalize_embeddings=True).tolist()


def embed_query(text: str) -> list[float]:
    """Create a normalized vector for one SOP search query.

    Args:
        text: Natural-language SOP question.

    Returns:
        list[float]: Local query embedding vector.
    """
    return get_embedding_model().encode(text, normalize_embeddings=True).tolist()

