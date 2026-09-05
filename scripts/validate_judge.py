"""Week 6 -- validate the LLM-as-judge against real human grading before
trusting its number, per the assignment's explicit requirement: "Checking
the AI judge agrees with your own grading before you trust it."

Presents a small set of real answered traces one at a time -- question,
the cited chunk's actual text, and the answer -- and asks the user to
grade each PASS/FAIL by hand, WITHOUT showing the judge's own verdict
first. Only after all human grades are collected does it run the judge
on the same set and report the agreement rate plus any disagreements.

Usage:
    python scripts/validate_judge.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import BASE_DIR
from app.judge import judge_faithfulness

TRACES_RAW_PATH = BASE_DIR / "data" / "traces" / "traces_raw.json"
VALIDATION_OUT_PATH = BASE_DIR / "data" / "eval" / "judge_validation.json"

# A mix of known-answer traces (should mostly PASS) and citation-drift
# traces (the interesting edge cases for a faithfulness judge, since the
# cited chunk is real but not the top-ranked one -- worth checking a
# human agrees the cited chunk still supports the claim).
VALIDATION_TRACE_IDS = [
    "t000", "t001", "t005", "t006", "t007",  # known-answer, expect PASS
    "t002", "t015", "t017",  # citation-drift cases
    "t014", "t019", "t030",  # rephrased known-answer, expect PASS
]


def main() -> None:
    all_traces = {t["trace_id"]: t for t in json.loads(TRACES_RAW_PATH.read_text(encoding="utf-8"))}

    from app.retrieval import search
    from app.config import COLLECTIONS

    human_grades: dict[str, str] = {}
    judge_grades: dict[str, dict] = {}
    chunk_texts: dict[str, str] = {}

    print(f"Grading {len(VALIDATION_TRACE_IDS)} traces. For each, read the question, the cited")
    print("source text, and the answer, then type P (pass, faithful) or F (fail, not faithful).\n")

    for tid in VALIDATION_TRACE_IDS:
        trace = all_traces[tid]
        if trace["refused"] or not trace["citations"]:
            print(f"skipping {tid}: refused or no citation, nothing to judge")
            continue

        cited_id = trace["citations"][0]["chunk_id"]
        # re-fetch full chunk text live (traces_raw.json only stores chunk_id/policy_id/section/score, not text)
        hits = search(trace["question"], COLLECTIONS[trace["strategy"]], top_k=10, region=trace.get("region"))
        chunk_text = next((h.text for h in hits if h.chunk_id == cited_id), "(chunk text not found in top-10 re-fetch)")
        chunk_texts[tid] = chunk_text

        print(f"=== {tid} ===")
        print(f"Question: {trace['question']}")
        print(f"Cited source text:\n{chunk_text}")
        print(f"Answer: {trace['answer']}")
        grade = input("Your grade (P=pass/F=fail): ").strip().upper()
        while grade not in ("P", "F"):
            grade = input("Please type P or F: ").strip().upper()
        human_grades[tid] = "PASS" if grade == "P" else "FAIL"
        print()

    print("Running the judge on the same set...\n")
    for tid in human_grades:
        trace = all_traces[tid]
        result = judge_faithfulness(trace["question"], chunk_texts[tid], trace["answer"])
        judge_grades[tid] = {"verdict": result.verdict, "reason": result.reason}

    agreements = sum(1 for tid in human_grades if human_grades[tid] == judge_grades[tid]["verdict"])
    total = len(human_grades)

    print(f"=== AGREEMENT: {agreements}/{total} ({agreements / total * 100:.0f}%) ===\n")
    disagreements = []
    for tid in human_grades:
        h, j = human_grades[tid], judge_grades[tid]["verdict"]
        status = "AGREE" if h == j else "DISAGREE"
        if h != j:
            disagreements.append(tid)
        print(f"{tid}: human={h} judge={j} [{status}] -- judge reason: {judge_grades[tid]['reason']}")

    VALIDATION_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_OUT_PATH.write_text(
        json.dumps(
            {
                "trace_ids": list(human_grades.keys()),
                "human_grades": human_grades,
                "judge_grades": judge_grades,
                "agreements": agreements,
                "total": total,
                "agreement_rate": agreements / total if total else None,
                "disagreements": disagreements,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nWrote {VALIDATION_OUT_PATH}")


if __name__ == "__main__":
    main()
