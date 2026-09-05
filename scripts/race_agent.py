"""Week 7 -- races the hand-built agent against the fixed workflow over
the same 5 scenarios, recording speed, cost, and reliability for each,
and writes race_results.md + data/agent/race_raw.json.

Usage:
    python scripts/race_agent.py
"""

import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent import run_agent
from app.config import BASE_DIR
from app.fixed_workflow import run_fixed_workflow

SCENARIOS_PATH = BASE_DIR / "data" / "agent" / "scenarios.json"
RACE_RAW_PATH = BASE_DIR / "data" / "agent" / "race_raw.json"
RACE_RESULTS_PATH = BASE_DIR / "race_results.md"


def main() -> None:
    scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))

    agent_runs = []
    workflow_runs = []

    for s in scenarios:
        print(f"Running agent on {s['id']}...")
        agent_run = run_agent(s)
        agent_runs.append(agent_run)
        print(f"  -> {agent_run.stop_reason}, {agent_run.total_seconds:.1f}s, ${agent_run.total_cost_usd:.5f}")

        print(f"Running fixed workflow on {s['id']}...")
        workflow_run = run_fixed_workflow(s)
        workflow_runs.append(workflow_run)
        print(f"  -> reliability_ok={workflow_run.reliability_ok}, {workflow_run.total_seconds:.1f}s, ${workflow_run.total_cost_usd:.5f}")

    raw = {
        "agent_runs": [
            {
                "scenario_id": r.scenario_id,
                "steps": [asdict(s) for s in r.steps],
                "final_answer": r.final_answer,
                "citations": r.citations,
                "stop_reason": r.stop_reason,
                "total_seconds": r.total_seconds,
                "total_cost_usd": r.total_cost_usd,
                "reliability_ok": r.reliability_ok,
            }
            for r in agent_runs
        ],
        "workflow_runs": [
            {
                "scenario_id": r.scenario_id,
                "steps": [asdict(s) for s in r.steps],
                "final_answer": r.final_answer,
                "citations": r.citations,
                "stop_reason": r.stop_reason,
                "total_seconds": r.total_seconds,
                "total_cost_usd": r.total_cost_usd,
                "reliability_ok": r.reliability_ok,
            }
            for r in workflow_runs
        ],
    }
    RACE_RAW_PATH.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    print(f"\nWrote {RACE_RAW_PATH}")

    md = _render_race_results(scenarios, agent_runs, workflow_runs)
    RACE_RESULTS_PATH.write_text(md, encoding="utf-8")
    print(f"Wrote {RACE_RESULTS_PATH}")


def _render_race_results(scenarios, agent_runs, workflow_runs) -> str:
    lines = ["# Agent vs Fixed Workflow — Race Results (Week 7, HR Policy)", ""]
    lines.append(
        "5 scenarios, each run through both a hand-built agent loop (`app/agent.py`, real OpenRouter "
        "calls deciding each step) and a fixed sequence (`app/fixed_workflow.py`, keyword-detected "
        "categories, one search per category, no adaptive step count)."
    )
    lines.append("")

    lines.append("## Comparison table")
    lines.append("")
    lines.append("| Scenario | Agent time | Agent cost | Agent outcome | Workflow time | Workflow cost | Workflow outcome |")
    lines.append("|---|---|---|---|---|---|---|")
    for s, ar, wr in zip(scenarios, agent_runs, workflow_runs):
        agent_outcome = ar.stop_reason
        workflow_outcome = "answered" if wr.reliability_ok else wr.stop_reason
        lines.append(
            f"| {s['id']} | {ar.total_seconds:.1f}s | ${ar.total_cost_usd:.5f} | {agent_outcome} | "
            f"{wr.total_seconds:.1f}s | ${wr.total_cost_usd:.5f} | {workflow_outcome} |"
        )
    lines.append("")

    avg_agent_time = sum(r.total_seconds for r in agent_runs) / len(agent_runs)
    avg_workflow_time = sum(r.total_seconds for r in workflow_runs) / len(workflow_runs)
    avg_agent_cost = sum(r.total_cost_usd for r in agent_runs) / len(agent_runs)
    avg_workflow_cost = sum(r.total_cost_usd for r in workflow_runs) / len(workflow_runs)
    agent_reliable = sum(1 for r in agent_runs if r.reliability_ok)
    workflow_reliable = sum(1 for r in workflow_runs if r.reliability_ok)
    agent_hit_budget = sum(1 for r in agent_runs if r.stop_reason != "finished")

    lines.append("## Aggregate")
    lines.append("")
    lines.append(f"- **Speed**: agent avg {avg_agent_time:.1f}s vs workflow avg {avg_workflow_time:.1f}s")
    lines.append(f"- **Cost**: agent avg ${avg_agent_cost:.5f} vs workflow avg ${avg_workflow_cost:.5f}")
    lines.append(f"- **Reliability (completed cleanly)**: agent {agent_reliable}/{len(agent_runs)} vs workflow {workflow_reliable}/{len(workflow_runs)}")
    lines.append(f"- **Agent hit a stop condition (not a clean finish) on**: {agent_hit_budget}/{len(agent_runs)} scenarios")
    lines.append("")

    lines.append("## Full step log for one representative agent run")
    lines.append("")
    rep_idx = 0
    rep_scenario, rep_run = scenarios[rep_idx], agent_runs[rep_idx]
    lines.append(f"**Scenario {rep_scenario['id']}**: {rep_scenario['question']}")
    lines.append("")
    for step in rep_run.steps:
        lines.append(f"- **Step {step.step_number}** (fallback_parse={step.used_fallback_parse})")
        lines.append(f"  - Thought: {step.thought}")
        lines.append(f"  - Action: `{step.action}` `{step.action_input}`")
        lines.append(f"  - Observation: {step.observation[:200]}")
    lines.append(f"- **Stop reason**: {rep_run.stop_reason}")
    lines.append(f"- **Final answer**: {rep_run.final_answer}")
    lines.append(f"- **Citations**: {rep_run.citations}")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
