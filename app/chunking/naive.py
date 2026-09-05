import re

from app.chunking.base import Chunk, Chunker, RawDoc

_SECTION_HINT = re.compile(r"(\d+(?:\.\d+)*)\s+[A-Z]")


class NaiveChunker(Chunker):
    """Fixed-size chunking with overlap, splitting on paragraph boundaries
    where possible. Does not treat section headers specially -- a clause and
    its section number can end up in different chunks if the boundary falls
    between them.
    """

    name = "naive"

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, doc: RawDoc) -> list[Chunk]:
        paragraphs = [p.strip() for p in doc.text.split("\n\n") if p.strip()]

        raw_chunks: list[str] = []
        current = ""
        for para in paragraphs:
            candidate = f"{current}\n\n{para}" if current else para
            if len(candidate) <= self.chunk_size:
                current = candidate
                continue
            if current:
                raw_chunks.append(current)
            if len(para) <= self.chunk_size:
                current = para
            else:
                # paragraph itself exceeds chunk_size, hard-split it
                for i in range(0, len(para), self.chunk_size - self.chunk_overlap):
                    raw_chunks.append(para[i : i + self.chunk_size])
                current = ""
        if current:
            raw_chunks.append(current)

        # apply char-level overlap between consecutive chunks
        overlapped: list[str] = []
        for i, text in enumerate(raw_chunks):
            if i == 0:
                overlapped.append(text)
                continue
            prev = raw_chunks[i - 1]
            tail = prev[-self.chunk_overlap :] if len(prev) > self.chunk_overlap else prev
            overlapped.append(f"{tail}\n\n{text}")

        chunks: list[Chunk] = []
        for i, text in enumerate(overlapped):
            match = _SECTION_HINT.search(text)
            section = match.group(1) if match else None
            chunks.append(
                Chunk(
                    chunk_id=f"{doc.source_file}::naive::{i}",
                    text=text,
                    source_file=doc.source_file,
                    policy_id=doc.policy_id,
                    region=doc.region,
                    effective_date=doc.effective_date,
                    section=section,
                    strategy=self.name,
                )
            )
        return chunks
