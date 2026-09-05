import json

from fastapi import APIRouter, HTTPException

from app.chunking.naive import NaiveChunker
from app.chunking.structure_aware import StructureAwareChunker
from app.config import COLLECTIONS, HIT_RATE_K, RAW_DUMP_PATH
from app.hybrid_retrieval import clear_bm25_cache, hybrid_search
from app.indexing import build_index
from app.refusal import answer_question
from app.report import run_full_evaluation
from app.retrieval import search

router = APIRouter()


@router.post("/api/admin/reindex")
def reindex() -> dict:
    naive_count = build_index(NaiveChunker(), COLLECTIONS["naive"], recreate=True)
    structured_count = build_index(StructureAwareChunker(), COLLECTIONS["structure_aware"], recreate=True)
    # the in-memory BM25 index is rebuilt from the same source documents, so
    # it can't actually drift in content -- but clear it anyway so a manual
    # reindex can never leave it stale relative to a freshly rebuilt
    # Qdrant collection (e.g. if chunking logic itself changes at runtime).
    clear_bm25_cache()
    return {"naive_chunks": naive_count, "structure_aware_chunks": structured_count}


@router.post("/api/admin/evaluate")
def evaluate() -> dict:
    dump = run_full_evaluation()
    return {
        "hit_rate_totals": dump["hit_rate"]["totals"],
        "filter_demo_top1_changed": dump["filter_demo"]["top1_changed"],
        "cited_answers": dump["cited_answers"],
        "refusals": dump["refusals"],
    }


@router.get("/api/admin/evaluate/latest")
def evaluate_latest() -> dict:
    if not RAW_DUMP_PATH.exists():
        raise HTTPException(status_code=404, detail="No evaluation has been run yet.")
    return json.loads(RAW_DUMP_PATH.read_text(encoding="utf-8"))


@router.get("/api/admin/inspect")
def inspect(collection: str = "structure_aware", mode: str = "hybrid", k: int = HIT_RATE_K) -> dict:
    """Week 4 inspection view: for each of the 8 answerable questions,
    shows the question, what was fetched (with semantic_rank/bm25_rank/
    fused_score when mode=hybrid), and the final generated answer +
    citations, side by side. Pure aggregation over existing
    search()/hybrid_search()/answer_question() -- no new retrieval or
    generation logic here.
    """
    if collection not in COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"unknown collection {collection!r}")
    if mode not in ("semantic", "hybrid"):
        raise HTTPException(status_code=400, detail=f"unknown mode {mode!r}")

    from app.evaluation import _load_questions

    questions = _load_questions()["answerable"]
    rows = []
    for q in questions:
        if mode == "hybrid":
            hits = hybrid_search(q["question"], collection, top_k=k)
        else:
            hits = search(q["question"], COLLECTIONS[collection], top_k=k)

        result = answer_question(q["question"], strategy=collection, top_k=k, retrieval_mode=mode)

        fetched = []
        for h in hits:
            entry = {
                "chunk_id": h.chunk_id,
                "policy_id": h.policy_id,
                "section": h.section,
                "score": round(h.score, 4),
            }
            if getattr(h, "semantic_rank", None) is not None:
                entry["semantic_rank"] = h.semantic_rank
            if getattr(h, "bm25_rank", None) is not None:
                entry["bm25_rank"] = h.bm25_rank
            if getattr(h, "fused_score", None) is not None:
                entry["fused_score"] = round(h.fused_score, 5)
            fetched.append(entry)

        rows.append(
            {
                "id": q["id"],
                "question": q["question"],
                "known_policy_id": q["known_policy_id"],
                "known_section": q["known_section"],
                "fetched": fetched,
                "answer": {
                    "refused": result.refused,
                    "reason": result.reason,
                    "answer": result.answer,
                    "citations": [c.model_dump() for c in result.citations],
                },
            }
        )

    return {"collection": collection, "mode": mode, "k": k, "rows": rows}
