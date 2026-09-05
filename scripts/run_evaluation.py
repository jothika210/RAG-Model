import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.report import run_full_evaluation


def main() -> None:
    print("Running full evaluation (search-only comparison, filter demo, generation, refusals)...")
    dump = run_full_evaluation()
    print(f"hit-rate totals: {dump['hit_rate']['totals']}")
    print(f"filter demo top1_changed: {dump['filter_demo']['top1_changed']}")
    print("Wrote results.md and data/eval_raw_dump.json")


if __name__ == "__main__":
    main()
