import hashlib

from qdrant_client.models import PointStruct

from app.chunking.base import Chunk, Chunker
from app.embedding import embed_texts, vector_size
from app.loader import load_addenda
from app.vectorstore import ensure_collection, upsert_points

REQUIRED_FIELDS = ("source_file", "policy_id", "region", "effective_date")


def _validate_chunk(chunk: Chunk) -> None:
    for field in REQUIRED_FIELDS:
        value = getattr(chunk, field)
        if not value:
            raise ValueError(f"chunk {chunk.chunk_id!r} is missing required metadata field {field!r} — failed ingest")


def _point_id(chunk_id: str) -> int:
    # Qdrant point ids must be int or UUID; derive a stable int id from the
    # deterministic chunk_id string so re-ingesting the same corpus upserts
    # the same points rather than duplicating them.
    digest = hashlib.sha256(chunk_id.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def build_index(chunker: Chunker, collection_name: str, recreate: bool = True) -> int:
    docs = load_addenda()

    all_chunks: list[Chunk] = []
    for doc in docs:
        chunks = chunker.chunk(doc)
        for c in chunks:
            _validate_chunk(c)
        all_chunks.extend(chunks)

    dim = vector_size()
    ensure_collection(collection_name, dim, recreate=recreate)

    texts = [c.text for c in all_chunks]
    vectors = embed_texts(texts)

    points = [
        PointStruct(
            id=_point_id(c.chunk_id),
            vector=vec,
            payload={
                "chunk_id": c.chunk_id,
                "text": c.text,
                "source_file": c.source_file,
                "policy_id": c.policy_id,
                "region": c.region,
                "effective_date": c.effective_date,
                "section": c.section,
                "strategy": c.strategy,
            },
        )
        for c, vec in zip(all_chunks, vectors)
    ]

    upsert_points(collection_name, points)
    return len(points)
