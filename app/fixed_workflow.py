"""Week 7 -- the fixed-sequence equivalent of app/agent.py's loop, for
the speed/cost/reliability comparison. No LLM calls decide control flow
here -- the category detection is a simple keyword match, and exactly
one search_policy() call runs per detected category, in a fixed order.
Cross-reference chasing is intentionally NOT attempted (a known,
accepted limitation of the fixed-sequence approach -- see race_results.md).

The only LLM call in this path is the final answer-writing step, kept
so the cost comparison reflects a genuinely usable fixed workflow
(one that still produces a well-written final answer), not a strawman.
"""

import time
from dataclasses import dataclass, field

import httpx

from app.agent_tools import search_policy
from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL

PRICE_PER_1K_INPUT = 0.00015
PRICE_PER_1K_OUTPUT = 0.0006

CATEGORY_QUERIES = {
    "carry_over": "carry-over cap",
    "sick_leave": "sick leave entitlement and certification",
    "parental_leave": "parental leave entitlement",
    "remote_work": "remote work public holiday leave deduction",
}

CATEGORY_KEYWORDS = {
    "carry_over": ["carry-over", "carryover", "carry over"],
    "sick_leave": ["sick"],
    "parental_leave": ["parental", "caregiver", "maternity", "paternity"],
    "remote_work": ["remote", "public holiday"],
}


@dataclass
class WorkflowStep:
    step_number: int
    action: str
    action_input: dict
    observation: str


@dataclass
class WorkflowRun:
    scenario_id: str
    steps: list[WorkflowStep] = field(default_factory=list)
    final_answer: str | None = None
    citations: list[str] = field(default_factory=list)
    stop_reason: str = "finished"
    total_seconds: float = 0.0
    total_cost_usd: float = 0.0
    reliability_ok: bool = False


def _detect_categories(question: str) -> list[str]:
    q = question.lower()
    detected = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            detected.append(category)
    return detected or ["carry_over"]  # fallback: at least search something


def _write_final_answer(question: str, observations: list[str]) -> tuple[str, int, int]:
    context = "\n\n---\n\n".join(observations)
    response = httpx.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Answer the question using only the provided search results. Cite each "
                    "claim with the chunk_id in square brackets. If a detail is missing from the "
                    "results, say so plainly rather than guessing.",
                },
                {"role": "user", "content": f"Search results:\n\n{context}\n\nQuestion: {question}"},
            ],
            "temperature": 0,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    usage = data.get("usage", {})
    return data["choices"][0]["message"]["content"], usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def run_fixed_workflow(scenario: dict) -> WorkflowRun:
    run = WorkflowRun(scenario_id=scenario["id"])
    start_time = time.monotonic()

    categories = _detect_categories(scenario["question"])
    observations = []
    for i, category in enumerate(categories, 1):
        query = CATEGORY_QUERIES.get(category, category)
        result = search_policy(query, scenario.get("region"))
        run.steps.append(WorkflowStep(i, "search_policy", {"query": query, "region": scenario.get("region")}, result.output))
        observations.append(result.output)

    try:
        answer, in_tok, out_tok = _write_final_answer(scenario["question"], observations)
        run.total_cost_usd = (in_tok / 1000) * PRICE_PER_1K_INPUT + (out_tok / 1000) * PRICE_PER_1K_OUTPUT
        run.final_answer = answer
        run.reliability_ok = True
        # naive citation extraction: any chunk_id-looking bracket in the answer
        import re

        run.citations = re.findall(r"\[([\w\-.]+::[\w\-.]+::\d+)\]", answer)
    except Exception as e:
        run.stop_reason = f"error: {e}"
        run.reliability_ok = False

    run.total_seconds = time.monotonic() - start_time
    return run
