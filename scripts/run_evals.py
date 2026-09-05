"""Week 6 -- the one-command eval entry point.

Runs every test case in data/eval/test_cases.json through the live
pipeline, applies rule-based checks (free, run first), runs the
faithfulness judge on non-refused answers, and aggregates pass rates
BY PROBLEM TYPE. Run with --gate-mode top1 (before) and --gate-mode top3
(after) to get the before/after comparison.

Usage:
    python scripts/run_evals.py --gate-mode top1
    python scripts/run_evals.py --gate-mode top3
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import BASE_DIR
from app.eval_checks import run_rule_checks
from app.judge import judge_faithfulness
from app.refusal import answer_question

TEST_CASES_PATH = BASE_DIR / "data" / "eval" / "test_cases.json"
RESULTS_DIR = BASE_DIR / "data" / "eval"


def _all_cases(test_cases: dict) -> list[dict]:
    cases = []
    for group in test_cases.values():
        cases.extend(group)
    return cases


def run_one_case(case: dict, gate_mode: str, run_judge: bool) -> dict:
    result = answer_question(
        case["question"],
        strategy=case.get("strategy", "structure_aware"),
        region=case.get("region"),
        gate_mode=gate_mode,
    )

    rule_results = run_rule_checks(result, case)
    rule_pass = all(r.passed for r in rule_results)

    judge_result = None
    if run_judge and not result.refused and result.citations:
        cited_id = result.citations[0].chunk_id
        cited_text = next((h.text for h in result.hits if h.chunk_id == cited_id), "")
        jr = judge_faithfulness(case["question"], cited_text, result.answer)
        judge_result = {"verdict": jr.verdict, "reason": jr.reason}

    overall_pass = rule_pass and (judge_result is None or judge_result["verdict"] == "PASS")

    return {
        "id": case["id"],
        "problem_type": case["problem_type"],
        "question": case["question"],
        "refused": result.refused,
        "reason": result.reason,
        "top_score": result.top_score,
        "rule_checks": [{"name": r.name, "passed": r.passed, "reason": r.reason} for r in rule_results],
        "rule_pass": rule_pass,
        "judge": judge_result,
        "overall_pass": overall_pass,
    }


def aggregate_by_problem_type(case_results: list[dict]) -> dict:
    by_type: dict[str, list[bool]] = {}
    for cr in case_results:
        by_type.setdefault(cr["problem_type"], []).append(cr["overall_pass"])
    return {
        pt: {"pass": sum(v), "total": len(v), "rate": sum(v) / len(v)}
        for pt, v in by_type.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Week 6 eval suite.")
    parser.add_argument("--gate-mode", choices=["top1", "top3"], default="top1")
    parser.add_argument("--no-judge", action="store_true", help="Skip the LLM judge (rule checks only, faster).")
    args = parser.parse_args()

    test_cases = json.loads(TEST_CASES_PATH.read_text(encoding="utf-8"))
    cases = _all_cases(test_cases)

    print(f"Running {len(cases)} test cases with gate_mode={args.gate_mode}...")
    results = []
    for i, case in enumerate(cases, 1):
        cr = run_one_case(case, args.gate_mode, run_judge=not args.no_judge)
        results.append(cr)
        status = "PASS" if cr["overall_pass"] else "FAIL"
        print(f"  [{i}/{len(cases)}] {cr['id']} ({cr['problem_type']}) -> {status}")

    by_type = aggregate_by_problem_type(results)

    print()
    print("=== Results by problem type ===")
    for pt, agg in sorted(by_type.items()):
        print(f"  {pt}: {agg['pass']}/{agg['total']} ({agg['rate'] * 100:.0f}%)")

    out_path = RESULTS_DIR / f"eval_results_{args.gate_mode}.json"
    out_path.write_text(
        json.dumps({"gate_mode": args.gate_mode, "cases": results, "by_problem_type": by_type}, indent=2),
        encoding="utf-8",
    )
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
