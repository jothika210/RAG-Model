"""Print retrieval rank and score for a single question, straight to the
terminal -- for live demos (e.g. showing a mentor exactly what the app
fetched and why).

Usage:
    python scripts/check_rank.py "your question here"
    python scripts/check_rank.py "your question here" --collection naive
    python scripts/check_rank.py "your question here" --region APAC
    python scripts/check_rank.py "your question here" --k 5
    python scripts/check_rank.py "your question here" --compare
        (prints semantic-only AND hybrid side by side, with sem/bm25 rank
        badges -- use this one to show how hybrid search changed a ranking)
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import COLLECTIONS
from app.hybrid_retrieval import hybrid_search
from app.retrieval import search

COL_WIDTHS = (4, 8, 50, 8, 9)


def _print_row(rank, score, chunk_id, policy_id, section, extra=""):
    print(
        f"{rank:<{COL_WIDTHS[0]}}"
        f"{score:<{COL_WIDTHS[1]}.4f}"
        f"{chunk_id:<{COL_WIDTHS[2]}}"
        f"{policy_id:<{COL_WIDTHS[3]}}"
        f"{('sec.' + str(section)) if section else '-':<{COL_WIDTHS[4]}}"
        f"{extra}"
    )


def _print_header(title):
    print()
    print(f"== {title} ==")
    print(f"{'#':<{COL_WIDTHS[0]}}{'score':<{COL_WIDTHS[1]}}{'chunk_id':<{COL_WIDTHS[2]}}{'policy':<{COL_WIDTHS[3]}}{'section':<{COL_WIDTHS[4]}}{'notes'}")
    print("-" * 100)


def main() -> None:
    parser = argparse.ArgumentParser(description="Show retrieval rank/scores for one question.")
    parser.add_argument("question", help="The question to search for (quote it).")
    parser.add_argument("--collection", default="structure_aware", choices=list(COLLECTIONS), help="Chunking strategy to search (default: structure_aware).")
    parser.add_argument("--region", default=None, help="Optional region filter (APAC, EMEA, AMER).")
    parser.add_argument("--k", type=int, default=5, help="Number of ranked results to show (default: 5).")
    parser.add_argument("--mode", default="semantic", choices=["semantic", "hybrid"], help="Retrieval mode (default: semantic). Ignored if --compare is set.")
    parser.add_argument("--compare", action="store_true", help="Show semantic AND hybrid side by side instead of just one mode.")
    args = parser.parse_args()

    print(f"Question: {args.question}")
    print(f"Collection: {args.collection}" + (f" | Region: {args.region}" if args.region else ""))

    if args.compare:
        _print_header(f"SEMANTIC (top {args.k})")
        for i, h in enumerate(search(args.question, COLLECTIONS[args.collection], top_k=args.k, region=args.region), 1):
            _print_row(i, h.score, h.chunk_id, h.policy_id, h.section)

        _print_header(f"HYBRID / BM25+RRF (top {args.k})")
        for i, h in enumerate(hybrid_search(args.question, args.collection, top_k=args.k, region=args.region), 1):
            notes = f"sem_rank={h.semantic_rank} bm25_rank={h.bm25_rank} fused={h.fused_score:.5f}"
            _print_row(i, h.score, h.chunk_id, h.policy_id, h.section, extra=notes)
    else:
        if args.mode == "hybrid":
            hits = hybrid_search(args.question, args.collection, top_k=args.k, region=args.region)
        else:
            hits = search(args.question, COLLECTIONS[args.collection], top_k=args.k, region=args.region)

        _print_header(f"{args.mode.upper()} (top {args.k})")
        for i, h in enumerate(hits, 1):
            extra = ""
            if args.mode == "hybrid":
                extra = f"sem_rank={h.semantic_rank} bm25_rank={h.bm25_rank} fused={h.fused_score:.5f}"
            _print_row(i, h.score, h.chunk_id, h.policy_id, h.section, extra=extra)

    print()


if __name__ == "__main__":
    main()
