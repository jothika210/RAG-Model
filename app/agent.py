"""Week 7 -- a hand-built agent loop, no framework. Classic ReAct-style
plan -> act -> observe -> repeat, using OpenRouter chat completions for
the "plan" step, with every step logged and three safe stop conditions
(step count, wall-clock time, estimated token cost).
"""

import json
import re
import time
from dataclasses import dataclass, field

import httpx

from app.agent_tools import TOOL_DESCRIPTIONS, get_chunk, search_policy
from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL

MAX_STEPS = 6
MAX_SECONDS = 45.0
MAX_ESTIMATED_COST_USD = 0.05

# Rough per-token USD pricing for openai/gpt-4o-mini on OpenRouter as of
# this build (input/output priced differently) -- used only to compute an
# ESTIMATE for the cost stop-condition and the race comparison, not billed
# directly from this constant.
PRICE_PER_1K_INPUT = 0.00015
PRICE_PER_1K_OUTPUT = 0.0006

SYSTEM_PROMPT = f"""You are an HR policy assistant that answers questions by using tools \
to search a corpus of 6 HR policy addenda, one step at a time.

{TOOL_DESCRIPTIONS}

Always ground your final answer only in what the tools returned. If a chunk mentions \
a definition "as defined in <policy> Section <x>", use get_chunk to fetch that exact \
chunk before finishing, so your answer is precise. Call finish as soon as you have \
enough information -- do not make unnecessary tool calls.
"""

_ACTION_RE = re.compile(r"Action:\s*(\w+)", re.IGNORECASE)
_INPUT_RE = re.compile(r"Action Input:\s*(\{.*\})", re.IGNORECASE | re.DOTALL)
# The model sometimes drifts from the prescribed "Action: name" +
# "Action Input: {json}" template into inline call syntax instead, e.g.
# 'Action: search_policy(query="...", region="...")' with no separate
# Action Input line at all. This is a genuine, observed reliability
# quirk (see race_results.md) -- tolerated here rather than silently
# dropped, so the agent doesn't waste steps on a formatting slip.
_INLINE_CALL_RE = re.compile(r"Action:\s*(\w+)\s*\((.*?)\)", re.IGNORECASE | re.DOTALL)
_KWARG_RE = re.compile(r'(\w+)\s*=\s*"([^"]*)"')


@dataclass
class Step:
    step_number: int
    thought: str
    action: str
    action_input: dict
    observation: str
    elapsed_seconds: float
    input_tokens: int
    output_tokens: int
    used_fallback_parse: bool = False


@dataclass
class AgentRun:
    scenario_id: str
    steps: list[Step] = field(default_factory=list)
    final_answer: str | None = None
    citations: list[str] = field(default_factory=list)
    stop_reason: str = "unknown"
    total_seconds: float = 0.0
    total_cost_usd: float = 0.0
    reliability_ok: bool = False


def _call_llm(messages: list[dict]) -> tuple[str, int, int]:
    response = httpx.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
        json={"model": OPENROUTER_MODEL, "messages": messages, "temperature": 0},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return content, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def _parse_action(raw: str) -> tuple[str, str, dict, bool]:
    """Returns (thought, action, action_input, used_fallback_parse). The
    fourth value flags when the model didn't follow the prescribed
    template and the inline-call fallback had to be used instead -- this
    is logged as a real reliability signal, not silently absorbed.
    """
    thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction:|\Z)", raw, re.DOTALL)
    thought = thought_match.group(1).strip() if thought_match else raw.strip()

    action_match = _ACTION_RE.search(raw)
    action = action_match.group(1).strip() if action_match else "finish"

    input_match = _INPUT_RE.search(raw)
    if input_match:
        try:
            return thought, action, json.loads(input_match.group(1)), False
        except json.JSONDecodeError:
            pass

    # fallback: tolerate inline call syntax, e.g. Action: tool(query="x", region="y")
    inline_match = _INLINE_CALL_RE.search(raw)
    if inline_match:
        kwargs = dict(_KWARG_RE.findall(inline_match.group(2)))
        if kwargs:
            return thought, inline_match.group(1).strip(), kwargs, True

    return thought, action, {}, bool(action_match)


def run_agent(scenario: dict) -> AgentRun:
    run = AgentRun(scenario_id=scenario["id"])
    start_time = time.monotonic()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": scenario["question"] + (f" (region: {scenario['region']})" if scenario.get("region") else "")},
    ]

    for step_num in range(1, MAX_STEPS + 1):
        elapsed = time.monotonic() - start_time
        if elapsed >= MAX_SECONDS:
            run.stop_reason = f"time_budget_exceeded ({elapsed:.1f}s >= {MAX_SECONDS}s)"
            break
        if run.total_cost_usd >= MAX_ESTIMATED_COST_USD:
            run.stop_reason = f"cost_budget_exceeded (${run.total_cost_usd:.4f} >= ${MAX_ESTIMATED_COST_USD})"
            break

        raw, in_tok, out_tok = _call_llm(messages)
        step_cost = (in_tok / 1000) * PRICE_PER_1K_INPUT + (out_tok / 1000) * PRICE_PER_1K_OUTPUT
        run.total_cost_usd += step_cost

        thought, action, action_input, used_fallback = _parse_action(raw)

        if action == "finish":
            run.final_answer = action_input.get("summary", raw)
            run.citations = action_input.get("citations", [])
            run.steps.append(Step(step_num, thought, action, action_input, "(finished)", time.monotonic() - start_time, in_tok, out_tok, used_fallback))
            run.stop_reason = "finished"
            run.reliability_ok = True
            break

        if action == "search_policy":
            result = search_policy(action_input.get("query", ""), action_input.get("region"))
        elif action == "get_chunk":
            result = get_chunk(action_input.get("chunk_id", ""))
        else:
            result = type("R", (), {"output": f"(unknown tool {action!r} -- ignored)"})()

        observation = result.output
        run.steps.append(Step(step_num, thought, action, action_input, observation, time.monotonic() - start_time, in_tok, out_tok, used_fallback))

        messages.append({"role": "assistant", "content": raw})
        messages.append({"role": "user", "content": f"Observation: {observation}"})
    else:
        run.stop_reason = f"max_steps_exceeded ({MAX_STEPS})"

    run.total_seconds = time.monotonic() - start_time
    return run
