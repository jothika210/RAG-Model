from dataclasses import dataclass

from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.config import TOP_K
from app.embedding import embed_query
from app.vectorstore import get_client


@dataclass
class SearchHit:
    chunk_id: str
    text: str
    source_file: str
    policy_id: str
    region: str
    effective_date: str
    section: str | None
    strategy: str
    score: float


def search(
    query: str,
    collection_name: str,
    top_k: int = TOP_K,
    region: str | None = None,
) -> list[SearchHit]:
    client = get_client()
    vector = embed_query(query)

    query_filter = None
    if region:
        query_filter = Filter(must=[FieldCondition(key="region", match=MatchValue(value=region))])

    results = client.query_points(
        collection_name=collection_name,
        query=vector,
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,
    ).points

    hits = []
    for r in results:
        payload = r.payload or {}
        hits.append(
            SearchHit(
                chunk_id=payload.get("chunk_id", ""),
                text=payload.get("text", ""),
                source_file=payload.get("source_file", ""),
                policy_id=payload.get("policy_id", ""),
                region=payload.get("region", ""),
                effective_date=payload.get("effective_date", ""),
                section=payload.get("section"),
                strategy=payload.get("strategy", ""),
                score=r.score,
            )
        )
    return hits
