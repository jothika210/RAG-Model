import pytest

from app.hybrid_retrieval import _rrf_fuse, bm25_search, hybrid_search
from app.chunking.naive import NaiveChunker
from app.loader import load_addenda


def test_rrf_fusion_math():
    # semantic ranks x=1, y=2, z=3; bm25 ranks y=1, x=2, w=3
    semantic_ranked = ["x", "y", "z"]
    bm25_ranked = ["y", "x", "w"]
    k = 60

    scores = _rrf_fuse(semantic_ranked, bm25_ranked, k=k)

    expected_x = 1 / (k + 1) + 1 / (k + 2)  # rank 1 in semantic, rank 2 in bm25
    expected_y = 1 / (k + 2) + 1 / (k + 1)  # rank 2 in semantic, rank 1 in bm25
    expected_z = 1 / (k + 3)  # only in semantic, rank 3
    expected_w = 1 / (k + 3)  # only in bm25, rank 3

    assert scores["x"] == pytest.approx(expected_x)
    assert scores["y"] == pytest.approx(expected_y)
    assert scores["z"] == pytest.approx(expected_z)
    assert scores["w"] == pytest.approx(expected_w)

    # x and y appear in both lists and should outrank z/w which appear in only one
    assert scores["x"] > scores["z"]
    assert scores["y"] > scores["w"]


def test_bm25_recovers_naive_miss_q2():
    # Real corpus example: "India" appears exactly once in the whole corpus,
    # in the HR-207 table row containing "Full-time confirmed | India | 10
    # days". Pure semantic search missed this chunk entirely in top-5 under
    # naive chunking (confirmed in data/eval_raw_dump.json: q2 is a naive
    # miss). Note the chunk's `section` metadata is itself mislabeled "4.2"
    # by naive chunking's best-effort regex hint (the same metadata-tagging
    # bug documented in results.md), so this test checks for the actual
    # answer TEXT landing at rank 1, not the (known-unreliable) section
    # field -- which is exactly the point: BM25 finds the right content by
    # exact keyword match even though naive chunking's own metadata for
    # that same chunk is wrong.
    query = "Under HR-207, what is the carry-over cap for a full-time confirmed employee in India?"
    hits = bm25_search(query, "naive", top_k=5)

    assert hits, "expected at least one BM25 hit"
    assert "India | 10 days" in hits[0].text, (
        "expected BM25's rank-1 hit to be the chunk containing the India carry-over row"
    )


def test_hybrid_search_returns_ranks():
    hits = hybrid_search("What is the carry-over cap for a probationary employee under HR-207 section 4.2?", "structure_aware", top_k=5)
    assert hits, "expected hybrid_search to return at least one hit"
    top = hits[0]
    assert top.fused_score is not None
    assert top.semantic_rank is not None or top.bm25_rank is not None
