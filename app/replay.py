"""Week 5 Task Set C, requirement #1 -- prove traces are replayable.

Reconstructs the exact call for one trace using ONLY the fields already
stored on that trace, re-runs it through the live pipeline, and compares
the replayed output against the original. This is the evidence that a
trace record is self-sufficient -- someone reading the trace file alone,
with no other context, could reproduce what the app actually did.
"""

from dataclasses import dataclass

from app.refusal import answer_question

# Fields a fully replay-grade trace should carry, per W5-Task-Set-C.md
# requirement #1: "prompt version, retrieved chunk_ids + scores, model +
# params, raw output". Checked against app/trace_collection.py::Trace.
FIELDS_PRESENT = [
    "question (the exact input)",
    "region / strategy / retrieval_mode (the params that select the retrieval path)",
    "ranked_hits: chunk_id + score for every retrieved chunk",
    "raw_llm_output (the model's unprocessed response, when generation ran)",
    "refused / reason (which gate fired, if any)",
    "answer + citations (the final resolved output)",
]

FIELDS_NOT_RECONSTRUCTABLE = [
    "No explicit prompt-template VERSION string is stored on the trace -- "
    "app/generation.py's SYSTEM_PROMPT is a single hardcoded constant with no "
    "version tag, so if the prompt text is edited in the future, old traces "
    "would have no way to record which prompt version actually produced them.",
    "No explicit model name / temperature is stored per-trace -- these are "
    "read from app/config.py (OPENROUTER_MODEL) and hardcoded in "
    "app/generation.py (temperature=0) at call time, not captured into the "
    "Trace record itself. A replay today uses whatever the CURRENT config "
    "says, which happens to be unchanged, but a trace alone cannot prove "
    "that if config changes later.",
    "Embedding model version is likewise a global config constant "
    "(EMBEDDING_MODEL), not recorded per-trace -- retrieval score "
    "reproducibility depends on the embedding model and the Qdrant index "
    "content being unchanged between when the trace was collected and when "
    "it's replayed; this is not bit-for-bit guaranteed if either changes.",
]


@dataclass
class ReplayComparison:
    trace_id: str
    original: dict
    replayed: dict
    ranked_hits_match: bool
    answer_match: bool
    refused_match: bool


def replay_trace(trace: dict) -> ReplayComparison:
    """Reconstructs and re-runs the exact call stored on `trace`, using only
    the trace's own fields (question, strategy, region, retrieval_mode) --
    proving the trace is self-sufficient to replay without any external
    context.
    """
    result = answer_question(
        trace["question"],
        strategy=trace["strategy"],
        region=trace.get("region"),
        retrieval_mode=trace["retrieval_mode"],
    )

    replayed = {
        "ranked_hits": [
            {
                "chunk_id": h.chunk_id,
                "policy_id": h.policy_id,
                "section": h.section,
                "region": h.region,
                "score": round(h.score, 4),
            }
            for h in result.hits
        ],
        "refused": result.refused,
        "reason": result.reason,
        "raw_llm_output": result.raw_llm_output,
        "answer": result.answer,
        "citations": [c.model_dump() for c in result.citations],
    }

    original_chunk_ids = [h["chunk_id"] for h in trace["ranked_hits"]]
    replayed_chunk_ids = [h["chunk_id"] for h in replayed["ranked_hits"]]

    return ReplayComparison(
        trace_id=trace["trace_id"],
        original={
            "ranked_hits": trace["ranked_hits"],
            "refused": trace["refused"],
            "reason": trace["reason"],
            "raw_llm_output": trace["raw_llm_output"],
            "answer": trace["answer"],
            "citations": trace["citations"],
        },
        replayed=replayed,
        ranked_hits_match=original_chunk_ids == replayed_chunk_ids,
        answer_match=trace["answer"] == replayed["answer"],
        refused_match=trace["refused"] == replayed["refused"],
    )
