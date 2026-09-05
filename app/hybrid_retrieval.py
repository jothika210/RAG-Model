import re
from dataclasses import dataclass

from rank_bm25 import BM25Okapi

from app.chunking.base import Chunk
from app.chunking.naive import NaiveChunker
from app.chunking.structure_aware import StructureAwareChunker
from app.config import COLLECTIONS, HYBRID_SEMANTIC_POOL, RRF_K, TOP_K
from app.loader import load_addenda
from app.retrieval import SearchHit, search

_CHUNKERS = {"naive": NaiveChunker(), "structure_aware": StructureAwareChunker()}

# collection_key -> (BM25Okapi index, chunks in the same order as the index)
_bm25_cache: dict[str, tuple[BM25Okapi, list[Chunk]]] = {}


@dataclass
class HybridSearchHit(SearchHit):
    """Adds rank-transparency fields on top of SearchHit so the inspection
    view can show *why* a chunk ranked where it did under hybrid search.
    Because this subclasses SearchHit (rather than adding optional fields
    to SearchHit itself), every existing SearchHit-typed call site keeps
    working unmodified -- a HybridSearchHit IS a SearchHit.
    """

    semantic_rank: int | None = None
    bm25_rank: int | None = None
    fused_score: float | None = None


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def clear_bm25_cache() -> None:
    """Called from the reindex admin route so a manual reindex can't leave
    the in-memory BM25 index stale relative to a freshly rebuilt Qdrant
    collection."""
    _bm25_cache.clear()


def _get_bm25_index(collection_key: str) -> tuple[BM25Okapi, list[Chunk]]:
    """Lazily builds and caches a BM25 index per collection key, rebuilt
    from the same source documents + chunker used to populate that Qdrant
    collection. Not persisted to disk -- the corpus is tiny (under 60
    chunks), so rebuilding tokenization at first use costs milliseconds,
    consistent with the existing singleton pattern for the embedding model
    and Qdrant client.
    """
    if collection_key not in _bm25_cache:
        chunker = _CHUNKERS[collection_key]
        docs = load_addenda()
        all_chunks = [c for doc in docs for c in chunker.chunk(doc)]
        tokenized = [_tokenize(c.text) for c in all_chunks]
        _bm25_cache[collection_key] = (BM25Okapi(tokenized), all_chunks)
    return _bm25_cache[collection_key]


def bm25_search(query: str, collection_key: str, top_k: int, region: str | None = None) -> list[SearchHit]:
    """Pure lexical search over the same chunk corpus, scored by BM25.
    Returns SearchHit objects (score = the raw BM25 score, not comparable
    across collections or against cosine similarity)."""
    bm25_index, all_chunks = _get_bm25_index(collection_key)
    scores = bm25_index.get_scores(_tokenize(query))
    ranked = sorted(zip(all_chunks, scores), key=lambda pair: -pair[1])
    if region:
        ranked = [(c, s) for c, s in ranked if c.region == region]

    hits = []
    for chunk, score in ranked[:top_k]:
        hits.append(
            SearchHit(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                source_file=chunk.source_file,
                policy_id=chunk.policy_id,
                region=chunk.region,
                effective_date=chunk.effective_date,
                section=chunk.section,
                strategy=chunk.strategy,
                score=float(score),
            )
        )
    return hits


def _rrf_fuse(semantic_ranked_ids: list[str], bm25_ranked_ids: list[str], k: int = RRF_K) -> dict[str, float]:
    """Reciprocal Rank Fusion: fused_score(id) = sum over each ranked list
    containing id of 1/(k + rank), rank is 1-indexed. Pure function, no I/O
    -- unit-testable in isolation from any real search/embedding calls.
    """
    scores: dict[str, float] = {}
    for rank, cid in enumerate(semantic_ranked_ids, start=1):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
    for rank, cid in enumerate(bm25_ranked_ids, start=1):
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
    return scores


def hybrid_search(
    query: str,
    collection_key: str,
    top_k: int = TOP_K,
    region: str | None = None,
    semantic_pool: int = HYBRID_SEMANTIC_POOL,
) -> list[HybridSearchHit]:
    """Combines the existing semantic search() with a parallel BM25 lexical
    search over the same chunk corpus, fused via Reciprocal Rank Fusion.
    Note the parameter is `collection_key` ("naive" | "structure_aware"),
    not the raw Qdrant collection name -- BM25 needs the chunker + key to
    rebuild its index, not just the Qdrant collection string. This does NOT
    modify app.retrieval.search() in any way; it is a fully additive,
    parallel code path.
    """
    collection_name = COLLECTIONS[collection_key]
    semantic_hits = search(query, collection_name, top_k=semantic_pool, region=region)
    bm25_hits = bm25_search(query, collection_key, top_k=semantic_pool, region=region)

    semantic_ranked_ids = [h.chunk_id for h in semantic_hits]
    bm25_ranked_ids = [h.chunk_id for h in bm25_hits]
    fused_scores = _rrf_fuse(semantic_ranked_ids, bm25_ranked_ids)

    by_id_semantic = {h.chunk_id: h for h in semantic_hits}
    by_id_bm25 = {h.chunk_id: h for h in bm25_hits}
    sem_rank = {cid: i + 1 for i, cid in enumerate(semantic_ranked_ids)}
    bm25_rank = {cid: i + 1 for i, cid in enumerate(bm25_ranked_ids)}

    fused_order = sorted(fused_scores.items(), key=lambda item: -item[1])[:top_k]

    results: list[HybridSearchHit] = []
    for cid, fscore in fused_order:
        base = by_id_semantic.get(cid) or by_id_bm25.get(cid)
        if base is None:
            continue  # defensive; should not happen since fused_scores only contains ids from one of the two lists
        results.append(
            HybridSearchHit(
                chunk_id=base.chunk_id,
                text=base.text,
                source_file=base.source_file,
                policy_id=base.policy_id,
                region=base.region,
                effective_date=base.effective_date,
                section=base.section,
                strategy=base.strategy,
                score=base.score,
                semantic_rank=sem_rank.get(cid),
                bm25_rank=bm25_rank.get(cid),
                fused_score=fscore,
            )
        )
    return results
