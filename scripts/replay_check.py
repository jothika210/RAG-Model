"""Week 5 Task Set C, requirement #1: pick one trace_id at random (seeded),
replay it from the trace alone, and print original vs replayed side by
side.

Usage:
    python scripts/replay_check.py --seed 7
    python scripts/replay_check.py --trace-id t016   (replay a specific one)
"""

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import BASE_DIR
from app.replay import FIELDS_NOT_RECONSTRUCTABLE, FIELDS_PRESENT, replay_trace

TRACES_RAW_PATH = BASE_DIR / "data" / "traces" / "traces_raw.json"
SAMPLED_IDS_PATH = BASE_DIR / "data" / "traces" / "sampled_trace_ids.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay one trace from the sampled 20, chosen at random or by id.")
    parser.add_argument("--seed", type=int, default=7, help="Seed for picking the trace_id at random (default: 7).")
    parser.add_argument("--trace-id", default=None, help="Replay this exact trace_id instead of picking randomly.")
    args = parser.parse_args()

    all_traces = {t["trace_id"]: t for t in json.loads(TRACES_RAW_PATH.read_text(encoding="utf-8"))}
    sampled = json.loads(SAMPLED_IDS_PATH.read_text(encoding="utf-8"))

    if args.trace_id:
        chosen_id = args.trace_id
        print(f"Replaying explicitly requested trace_id={chosen_id!r}")
    else:
        rng = random.Random(args.seed)
        chosen_id = rng.choice(sampled["trace_ids"])
        print(f"Randomly picked trace_id={chosen_id!r} from the 20 sampled ids, using seed={args.seed}")

    trace = all_traces[chosen_id]
    comparison = replay_trace(trace)

    print()
    print(f"=== ORIGINAL ({comparison.trace_id}) ===")
    print(json.dumps(comparison.original, indent=2))

    print()
    print(f"=== REPLAYED ({comparison.trace_id}) ===")
    print(json.dumps(comparison.replayed, indent=2))

    print()
    print("=== COMPARISON ===")
    print(f"ranked_hits chunk_id order match: {comparison.ranked_hits_match}")
    print(f"answer text match: {comparison.answer_match}")
    print(f"refused flag match: {comparison.refused_match}")

    print()
    print("=== Fields present on this trace (per requirement #1) ===")
    for f in FIELDS_PRESENT:
        print(f"  - {f}")

    print()
    print("=== Fields NOT reconstructable from the trace alone ===")
    for f in FIELDS_NOT_RECONSTRUCTABLE:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
