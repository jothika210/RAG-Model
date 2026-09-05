import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import BASE_DIR
from app.worksheet import render_analysis_template, render_worksheet

TRACES_DIR = BASE_DIR / "data" / "traces"
TRACES_RAW_PATH = TRACES_DIR / "traces_raw.json"
SAMPLED_IDS_PATH = TRACES_DIR / "sampled_trace_ids.json"
WORKSHEET_PATH = TRACES_DIR / "trace_worksheet.md"
ANALYSIS_TEMPLATE_PATH = TRACES_DIR / "analysis_template.md"


def main() -> None:
    parser = argparse.ArgumentParser(description="Randomly sample traces and render the reading worksheet.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed, recorded for reproducibility.")
    parser.add_argument("--n", type=int, default=20, help="Number of traces to sample.")
    args = parser.parse_args()

    if not TRACES_RAW_PATH.exists():
        raise SystemExit(f"{TRACES_RAW_PATH} not found -- run scripts/collect_traces.py first.")

    all_traces = json.loads(TRACES_RAW_PATH.read_text(encoding="utf-8"))
    if args.n > len(all_traces):
        raise SystemExit(f"--n={args.n} exceeds pool size {len(all_traces)}")

    rng = random.Random(args.seed)
    sampled = rng.sample(all_traces, args.n)
    # keep the pool's original ordering among the sampled traces, rather than
    # the sample-call's internal order, so the worksheet reads in a stable,
    # non-suspicious sequence (not sorted by anything that could hint at
    # difficulty or category)
    sampled_ids = {t["trace_id"] for t in sampled}
    sampled_in_pool_order = [t for t in all_traces if t["trace_id"] in sampled_ids]

    SAMPLED_IDS_PATH.write_text(
        json.dumps({"seed": args.seed, "n": args.n, "trace_ids": sorted(sampled_ids)}, indent=2),
        encoding="utf-8",
    )

    worksheet_md = render_worksheet(sampled_in_pool_order, seed=args.seed)
    WORKSHEET_PATH.write_text(worksheet_md, encoding="utf-8")

    if not ANALYSIS_TEMPLATE_PATH.exists():
        ANALYSIS_TEMPLATE_PATH.write_text(render_analysis_template(), encoding="utf-8")

    print(f"Sampled {args.n} of {len(all_traces)} traces (seed={args.seed}).")
    print(f"Wrote {WORKSHEET_PATH}")
    print(f"Wrote {SAMPLED_IDS_PATH}")
    print(f"Analysis template at {ANALYSIS_TEMPLATE_PATH}")


if __name__ == "__main__":
    main()
