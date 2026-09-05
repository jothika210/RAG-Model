import re
from dataclasses import dataclass, field

from app.config import COLLECTIONS, SIMILARITY_THRESHOLD, TOP_K
from app.generation import generate_answer
from app.hybrid_retrieval import hybrid_search
from app.models import Citation
from app.retrieval import SearchHit, search

_CITATION_TAG = re.compile(r"\[([^\[\]]+)\]")


@dataclass
class AnswerResult:
    refused: bool
    reason: str | None
    answer: str | None
    citations: list[Citation] = field(default_factory=list)
    top_score: float | None = None
    hits: list[SearchHit] = field(default_factory=list)
    raw_llm_output: str | None = None


def _resolve_citations(text: str, hits: list[SearchHit]) -> list[Citation] | None:
    """Parses [chunk_id] tags out of the LLM response and resolves them
    against the chunks actually passed into context. Returns None if any
    tag fails to resolve or if zero citations are found -- signalling the
    caller to force a refusal instead of trusting the model's output.
    """
    by_id = {h.chunk_id: h for h in hits}
    tags = _CITATION_TAG.findall(text)
    if not tags:
        return None

    citations: list[Citation] = []
    for raw_tag in tags:
        # tolerate minor format noise like "chunk_id=X" or "see X" without
        # loosening what actually counts as a resolved citation
        tag = raw_tag.split("=", 1)[-1].strip()
        hit = by_id.get(tag)
        if hit is None:
            for candidate_id in by_id:
                if candidate_id in raw_tag:
                    hit = by_id[candidate_id]
                    break
        if hit is None:
            return None
        citations.append(Citation(chunk_id=hit.chunk_id, policy_id=hit.policy_id, section=hit.section))
    return citations


def answer_question(
    question: str,
    strategy: str = "structure_aware",
    region: str | None = None,
    top_k: int = TOP_K,
    retrieval_mode: str = "semantic",
) -> AnswerResult:
    """retrieval_mode: "semantic" (default, Week 3 behavior, unchanged) or
    "hybrid" (Week 4 -- BM25 + semantic, RRF-fused). Gate 1's similarity
    threshold is calibrated against cosine similarity scores from
    semantic-only search(); hybrid_search()'s fused_score is on a
    different scale (RRF's 1/(k+rank) sum), so under hybrid mode Gate 1
    checks the underlying semantic_rank/score signal on the top hit
    instead of comparing fused_score against SIMILARITY_THRESHOLD directly
    -- comparing incompatible scales would silently misfire the gate.
    """
    collection_name = COLLECTIONS[strategy]
    if retrieval_mode == "hybrid":
        hits = hybrid_search(question, strategy, top_k=top_k, region=region)
        # a hit with no semantic_rank was BM25-only and inherited score=0.0
        # from bm25_search()'s SearchHit construction -- fall back to a
        # fresh semantic-only top-1 score for the confidence gate so it's
        # always comparing on the calibrated cosine scale, regardless of
        # whether the fused top-1 happened to come from the BM25 side.
        top_score = hits[0].score if hits and hits[0].semantic_rank is not None else None
        if top_score is None:
            semantic_probe = search(question, collection_name, top_k=1, region=region)
            top_score = semantic_probe[0].score if semantic_probe else 0.0
    else:
        hits = search(question, collection_name, top_k=top_k, region=region)
        top_score = hits[0].score if hits else 0.0

    # Gate 1: pre-generation coverage check -- never call the LLM at all if
    # retrieval confidence is too low.
    if not hits or top_score < SIMILARITY_THRESHOLD:
        return AnswerResult(
            refused=True,
            reason="low_retrieval_confidence",
            answer=None,
            top_score=top_score,
            hits=hits,
        )

    raw_output = generate_answer(question, hits)

    if raw_output.strip().startswith("REFUSE:"):
        return AnswerResult(
            refused=True,
            reason="model_declined",
            answer=None,
            top_score=top_score,
            hits=hits,
            raw_llm_output=raw_output,
        )

    # Gate 2: post-hoc citation validation -- override to refusal if any
    # cited chunk_id doesn't resolve, or if there are zero citations.
    citations = _resolve_citations(raw_output, hits)
    if citations is None:
        return AnswerResult(
            refused=True,
            reason="unverifiable_citation",
            answer=None,
            top_score=top_score,
            hits=hits,
            raw_llm_output=raw_output,
        )

    return AnswerResult(
        refused=False,
        reason=None,
        answer=raw_output,
        citations=citations,
        top_score=top_score,
        hits=hits,
        raw_llm_output=raw_output,
    )
