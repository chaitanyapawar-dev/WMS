"""Approved Markdown SOP loading and section-aware chunking."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re


SOP_DIRECTORY = Path(__file__).resolve().parents[4] / "data" / "warehouse_sops"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 120


@dataclass(frozen=True)
class SOPChunk:
    """Represent one stable, approved SOP chunk and safe source metadata."""

    chunk_id: str
    source: str
    title: str
    section: str
    text: str


def load_sop_chunks(directory: Path = SOP_DIRECTORY) -> list[SOPChunk]:
    """Load only approved Markdown SOP files and split them into stable chunks.

    Args:
        directory: Server-controlled SOP directory to read.

    Returns:
        list[SOPChunk]: Non-empty chunks carrying source metadata.

    Raises:
        FileNotFoundError: If the approved SOP directory is unavailable.
    """
    if not directory.is_dir():
        raise FileNotFoundError("Approved warehouse SOP directory is unavailable")

    chunks: list[SOPChunk] = []
    for path in sorted(directory.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        chunks.extend(_chunk_document(path.name, text))
    return chunks


def _chunk_document(source: str, text: str) -> list[SOPChunk]:
    """Split one Markdown SOP by headings before applying bounded text chunks.

    Args:
        source: Approved SOP filename.
        text: Markdown source content.

    Returns:
        list[SOPChunk]: Stable section-aware chunks.
    """
    lines = text.splitlines()
    title = source.removesuffix(".md").replace("-", " ").title()
    sections: list[tuple[str, str]] = []
    section = "Overview"
    buffer: list[str] = []

    for line in lines:
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        title_heading = re.match(r"^#\s+(.+?)\s*$", line)
        if title_heading:
            title = title_heading.group(1)
            continue
        if heading:
            if buffer:
                sections.append((section, "\n".join(buffer).strip()))
            section = heading.group(1)
            buffer = []
        else:
            buffer.append(line)
    if buffer:
        sections.append((section, "\n".join(buffer).strip()))

    chunks: list[SOPChunk] = []
    for section_name, section_text in sections:
        for chunk_text in _split_text(section_text):
            normalized = " ".join(chunk_text.split())
            if not normalized:
                continue
            digest = sha256(f"{source}|{section_name}|{normalized}".encode("utf-8")).hexdigest()
            chunks.append(SOPChunk(digest, source, title, section_name, chunk_text))
    return chunks


def _split_text(text: str) -> list[str]:
    """Split text near paragraph boundaries with a small overlap.

    Args:
        text: One SOP section body.

    Returns:
        list[str]: Bounded, non-empty text chunks.
    """
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > CHUNK_SIZE:
            chunks.append(current)
            current = f"{current[-CHUNK_OVERLAP:]}\n\n{paragraph}".strip()
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks

