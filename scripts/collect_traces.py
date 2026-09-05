import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import BASE_DIR
from app.trace_collection import build_query_pool, collect_trace

TRACES_DIR = BASE_DIR / "data" / "traces"
TRACES_RAW_PATH = TRACES_DIR / "traces_raw.json"


def main() -> None:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    pool = build_query_pool()
    print(f"Collecting {len(pool)} traces from the live pipeline (this calls the LLM once per trace)...")

    traces = []
    for i, spec in enumerate(pool):
        trace = collect_trace(i, spec)
        traces.append(trace.to_dict())
        status = "REFUSED" if trace.refused else "answered"
        print(f"  [{i + 1}/{len(pool)}] {trace.trace_id} ({spec['category']}) -> {status}")

    TRACES_RAW_PATH.write_text(json.dumps(traces, indent=2), encoding="utf-8")
    print(f"Wrote {len(traces)} traces to {TRACES_RAW_PATH}")


if __name__ == "__main__":
    main()
