import json

from app.agent import AgentRun, Step
from app.config import BASE_DIR
from app.trajectory_eval import evaluate_run

RACE_RAW_PATH = BASE_DIR / "data" / "agent" / "race_raw.json"


def _run_from_raw(scenario_id: str) -> AgentRun:
    data = json.loads(RACE_RAW_PATH.read_text(encoding="utf-8"))
    raw = next(r for r in data["agent_runs"] if r["scenario_id"] == scenario_id)
    steps = [
        Step(
            step_number=s["step_number"],
            thought=s["thought"],
            action=s["action"],
            action_input=s["action_input"],
            observation=s["observation"],
            elapsed_seconds=s["elapsed_seconds"],
            input_tokens=s["input_tokens"],
            output_tokens=s["output_tokens"],
            used_fallback_parse=s["used_fallback_parse"],
        )
        for s in raw["steps"]
    ]
    return AgentRun(
        scenario_id=raw["scenario_id"],
        steps=steps,
        final_answer=raw["final_answer"],
        citations=raw["citations"],
        stop_reason=raw["stop_reason"],
        total_seconds=raw["total_seconds"],
        total_cost_usd=raw["total_cost_usd"],
        reliability_ok=raw["reliability_ok"],
    )


def test_real_s3_trace_flags_the_unverified_snippet_citation():
    run = _run_from_raw("s3")
    report = evaluate_run(run)

    by_id = {v.chunk_id: v for v in report.citations}
    assert by_id["HR-205_parental_leave_amer.md::structure_aware::4"].verified is True
    assert by_id["HR-205_parental_leave_amer.md::structure_aware::9"].verified is False
    assert report.unverified_count == 1
    assert report.all_verified is False


def test_all_citations_verified_when_every_citation_was_fetched():
    steps = [
        Step(1, "t", "get_chunk", {"chunk_id": "A"}, "obs", 0.0, 0, 0),
        Step(2, "t", "finish", {"summary": "s", "citations": ["A"]}, "(finished)", 0.0, 0, 0),
    ]
    run = AgentRun(scenario_id="synthetic", steps=steps, citations=["A"])

    report = evaluate_run(run)

    assert report.all_verified is True
    assert report.unverified_count == 0
    assert report.citations[0].verified is True


def test_fabricated_citation_never_fetched_is_flagged():
    steps = [
        Step(1, "t", "search_policy", {"query": "q"}, "[A] some snippet", 0.0, 0, 0),
        Step(2, "t", "finish", {"summary": "s", "citations": ["B"]}, "(finished)", 0.0, 0, 0),
    ]
    run = AgentRun(scenario_id="synthetic", steps=steps, citations=["B"])

    report = evaluate_run(run)

    assert report.all_verified is False
    assert report.unverified_count == 1
    assert report.citations[0].chunk_id == "B"
    assert report.citations[0].verified is False
