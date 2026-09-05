import json

from app.config import COLLECTIONS, HIT_RATE_K, QUESTIONS_PATH, RAW_DUMP_PATH, RESULTS_PATH, TOP_K
from app.hybrid_retrieval import hybrid_search
from app.refusal import answer_question
from app.retrieval import SearchHit, search


def _load_questions() -> dict:
    return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))


def _hit(hits: list[SearchHit], known_policy_id: str, known_section: str) -> bool:
    return any(h.policy_id == known_policy_id and h.section == known_section for h in hits)


def _hit_summary(hits: list[SearchHit]) -> list[dict]:
    return [
        {
            "chunk_id": h.chunk_id,
            "policy_id": h.policy_id,
            "section": h.section,
            "score": round(h.score, 4),
        }
        for h in hits
    ]


def run_hit_rate_comparison() -> dict:
    """Runs all 8 answerable questions, search-only, against both chunking
    strategy collections. Returns per-question hit/miss detail plus the
    aggregate X/8 for each strategy.
    """
    questions = _load_questions()["answerable"]

    per_question: list[dict] = []
    totals = {key: 0 for key in COLLECTIONS}

    for q in questions:
        row = {
            "id": q["id"],
            "question": q["question"],
            "known_policy_id": q["known_policy_id"],
            "known_section": q["known_section"],
            "depends_on_table": q["depends_on_table"],
            "results": {},
        }
        for strategy_key, collection_name in COLLECTIONS.items():
            hits = search(q["question"], collection_name, top_k=TOP_K)
            is_hit = _hit(hits, q["known_policy_id"], q["known_section"])
            row["results"][strategy_key] = {
                "hit": is_hit,
                "ranked": _hit_summary(hits),
            }
            if is_hit:
                totals[strategy_key] += 1
        per_question.append(row)

    return {
        "per_question": per_question,
        "totals": {k: f"{v}/{len(questions)}" for k, v in totals.items()},
        "totals_raw": totals,
        "num_questions": len(questions),
    }


def run_filter_demo(collection_key: str = "structure_aware") -> dict:
    """Finds a region-scoped query where filtering by region changes the
    top-1 result vs unfiltered search, and returns both full ranked lists
    with scores.
    """
    questions = _load_questions()["answerable"]
    collection_name = COLLECTIONS[collection_key]

    for q in questions:
        region = q.get("region")
        if not region:
            continue

        unfiltered = search(q["question"], collection_name, top_k=TOP_K)
        filtered = search(q["question"], collection_name, top_k=TOP_K, region=region)

        if not unfiltered or not filtered:
            continue

        if unfiltered[0].chunk_id != filtered[0].chunk_id:
            return {
                "question_id": q["id"],
                "question": q["question"],
                "region": region,
                "collection": collection_key,
                "unfiltered": _hit_summary(unfiltered),
                "filtered": _hit_summary(filtered),
                "top1_changed": True,
            }

    # fallback: no question naturally demonstrated a change; report the
    # first region-scoped question's lists honestly rather than fabricating
    q = next(q for q in questions if q.get("region"))
    region = q["region"]
    unfiltered = search(q["question"], collection_name, top_k=TOP_K)
    filtered = search(q["question"], collection_name, top_k=TOP_K, region=region)
    return {
        "question_id": q["id"],
        "question": q["question"],
        "region": region,
        "collection": collection_key,
        "unfiltered": _hit_summary(unfiltered),
        "filtered": _hit_summary(filtered),
        "top1_changed": bool(unfiltered and filtered and unfiltered[0].chunk_id != filtered[0].chunk_id),
    }


# ---------------------------------------------------------------------------
# Week 4 -- hybrid search before/after measurement and failure labeling.
# Nothing above this line is modified: run_hit_rate_comparison() (k=5, both
# collections, semantic-only) and run_filter_demo() are Week 3 functions
# that results.md sections 1-10 already depend on verbatim.
# ---------------------------------------------------------------------------


def _hit_at_k(hits: list[SearchHit], known_policy_id: str, known_section: str, k: int) -> tuple[bool, int | None]:
    """Like _hit() but also returns the 1-indexed rank of the first match
    within the first k hits, or None if no match. Used by the Week 4
    before/after comparison, which needs rank position, not just a
    boolean, to explain WHY a question is a hit or a miss at a given k.
    """
    for i, h in enumerate(hits[:k], start=1):
        if h.policy_id == known_policy_id and h.section == known_section:
            return True, i
    return False, None


def run_hit_rate_at_k(collection_key: str, k: int, mode: str) -> dict:
    """Runs all 8 answerable questions against ONE collection, ONE mode
    ("semantic" | "hybrid"), at cutoff k. This is the reusable engine
    behind the Week 4 before/after@3 numbers.
    """
    questions = _load_questions()["answerable"]
    collection_name = COLLECTIONS[collection_key]

    per_question: list[dict] = []
    total = 0
    for q in questions:
        if mode == "semantic":
            hits = search(q["question"], collection_name, top_k=max(k, TOP_K))
        elif mode == "hybrid":
            hits = hybrid_search(q["question"], collection_key, top_k=max(k, TOP_K))
        else:
            raise ValueError(f"unknown mode {mode!r}")

        is_hit, rank = _hit_at_k(hits, q["known_policy_id"], q["known_section"], k)
        per_question.append(
            {
                "id": q["id"],
                "question": q["question"],
                "hit": is_hit,
                "rank": rank,
                "ranked": _hit_summary(hits[:k]),
            }
        )
        total += int(is_hit)

    return {
        "collection": collection_key,
        "mode": mode,
        "k": k,
        "per_question": per_question,
        "total": f"{total}/{len(questions)}",
        "total_raw": total,
    }


def run_before_after_hybrid(collection_key: str, k: int = HIT_RATE_K) -> dict:
    """The Week 4 headline comparison: same 8 questions, same collection,
    same k, semantic-only (before) vs hybrid RRF (after). Explicitly flags
    which questions flipped miss->hit ("fixed"), stayed a miss
    ("still_broken"), flipped hit->miss ("regressed", should be rare/never
    but reported honestly if it happens), or were unaffected -- this is
    the mentor-check requirement "noticed which failures did NOT get
    fixed" as a first-class field, not an afterthought.
    """
    before = run_hit_rate_at_k(collection_key, k, mode="semantic")
    after = run_hit_rate_at_k(collection_key, k, mode="hybrid")

    before_by_id = {r["id"]: r for r in before["per_question"]}
    after_by_id = {r["id"]: r for r in after["per_question"]}

    fixed, still_broken, regressed, unaffected = [], [], [], []
    for qid in before_by_id:
        b, a = before_by_id[qid]["hit"], after_by_id[qid]["hit"]
        if not b and a:
            fixed.append(qid)
        elif not b and not a:
            still_broken.append(qid)
        elif b and not a:
            regressed.append(qid)
        else:
            unaffected.append(qid)

    return {
        "collection": collection_key,
        "k": k,
        "before": before,
        "after": after,
        "fixed": fixed,
        "still_broken": still_broken,
        "regressed": regressed,
        "unaffected": unaffected,
    }


def label_failure(question: dict, collection_key: str, k: int = HIT_RATE_K) -> dict:
    """Evidence-gathering for the two-kinds-of-wrong split the assignment
    asks for:
      - wrong_document: the known-correct chunk is not in the top-k at all
        (automatic, evidence = its absence / the actual rank if present at
        a lower k).
      - right_document_used: the known-correct chunk IS in the top-k, and
        the generated answer's citations include that exact chunk_id.
      - right_document_not_used: the known-correct chunk IS in the top-k,
        but the generated answer did not cite it -- a genuine "right
        document surfaced, generation still went wrong" case.
    Whether an answer that DID use the right chunk is actually factually
    correct still needs a one-line human judgment call recorded by hand in
    results.md -- no answer-correctness grader exists in this codebase,
    and building one is out of scope for the single-approved-change
    constraint (hybrid search only).
    """
    hits = hybrid_search(question["question"], collection_key, top_k=k)
    is_hit, rank = _hit_at_k(hits, question["known_policy_id"], question["known_section"], k)

    if not is_hit:
        return {
            "question_id": question["id"],
            "label": "wrong_document",
            "evidence": {
                "known_policy_id": question["known_policy_id"],
                "known_section": question["known_section"],
                "top_k_retrieved": _hit_summary(hits[:k]),
                "rank_of_correct_chunk": None,
            },
        }

    result = answer_question(question["question"], strategy=collection_key, top_k=k, retrieval_mode="hybrid")
    correct_chunk_id = next(
        h.chunk_id for h in hits[:k] if h.policy_id == question["known_policy_id"] and h.section == question["known_section"]
    )
    cited_ids = {c.chunk_id for c in result.citations}
    used_correct_chunk = correct_chunk_id in cited_ids

    return {
        "question_id": question["id"],
        "label": "right_document_used" if used_correct_chunk else "right_document_not_used",
        "evidence": {
            "rank_of_correct_chunk": rank,
            "correct_chunk_id": correct_chunk_id,
            "refused": result.refused,
            "reason": result.reason,
            "cited_chunk_ids": list(cited_ids),
            "answer": result.answer,
        },
    }
