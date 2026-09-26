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

from app.agent_memory import (
    ShortTermMemory,
    distill_observation,
    load_long_term_memory,
    lookup,
    remember,
    save_long_term_memory,
)
from app.agent_tools import TOOL_DESCRIPTIONS, get_chunk, search_policy
from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL
from app.web_search import web_search

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

ESCALATION RULE (follow this strictly): if you have already called search_policy \
TWICE for this question and neither call returned a result that actually answers \
it (e.g. every result scores low, or the returned text is clearly about a \
different topic), STOP retrying search_policy with reworded queries. On your very \
next turn you MUST either call web_search (if the question might have a real \
answer on the open web) or call finish with an honest refusal (if it has no real \
answer at all, from either source). Do not call search_policy a third time with \
the same or a similar query.
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
# A second observed drift: positional-style calls with no keyword names at
# all, e.g. 'Action: search_policy("query text", "APAC")'. Map positions to
# each tool's known argument order so these aren't silently lost either.
_POSITIONAL_ARG_RE = re.compile(r'"([^"]*)"')
TOOL_ARG_ORDER = {
    "search_policy": ["query", "region"],
    "get_chunk": ["chunk_id"],
    "finish": ["summary", "citations"],
}


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
    source: str = "unknown"  # "internal_policy" | "external_web" | "refused" | "long_term_memory"
    recalled_from_memory: bool = False


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

    # Try the inline-call fallback FIRST when the Action line itself embeds
    # arguments (e.g. "Action: search_policy(...)"), even if a separate,
    # empty "Action Input: {}" also appears -- the model sometimes emits
    # BOTH on the same turn, and an empty-but-valid {} would otherwise
    # short-circuit the strict parse below before the real args are ever
    # read from the inline call. This was a real, observed failure mode
    # (see race_results.md): it silently produced empty tool calls on
    # 4-5 of 6 steps per run until this ordering was fixed.
    inline_match = _INLINE_CALL_RE.search(raw)
    if inline_match:
        tool_name = inline_match.group(1).strip()
        call_body = inline_match.group(2)

        kwargs = dict(_KWARG_RE.findall(call_body))
        if kwargs:
            return thought, tool_name, kwargs, True

        positional = _POSITIONAL_ARG_RE.findall(call_body)
        arg_names = TOOL_ARG_ORDER.get(tool_name, [])
        if positional and arg_names:
            positional_kwargs = dict(zip(arg_names, positional))
            return thought, tool_name, positional_kwargs, True

    input_match = _INPUT_RE.search(raw)
    if input_match:
        try:
            parsed = json.loads(input_match.group(1))
            if parsed:
                return thought, action, parsed, False
        except json.JSONDecodeError:
            pass

    return thought, action, {}, bool(action_match)


def run_agent(scenario: dict) -> AgentRun:
    run = AgentRun(scenario_id=scenario["id"])
    start_time = time.monotonic()
    question = scenario["question"]

    # -- Long-term memory pre-check: has this exact question already been
    # answered in a previous run? If so, skip every tool call and recall
    # the stored answer directly -- this is what gives long-term memory
    # actual behavioral value, not just unused storage.
    long_term_store = load_long_term_memory()
    remembered = lookup(long_term_store, question)
    if remembered is not None:
        run.steps.append(
            Step(
                step_number=1,
                thought=f"I recall answering this exact question before (source: {remembered['source']}, "
                f"remembered at {remembered['remembered_at']}). Recalling from long-term memory instead of "
                "repeating the same tool calls.",
                action="recall_from_memory",
                action_input={},
                observation=f"Recalled: {remembered['answer']}",
                elapsed_seconds=time.monotonic() - start_time,
                input_tokens=0,
                output_tokens=0,
                used_fallback_parse=False,
            )
        )
        run.final_answer = remembered["answer"]
        run.citations = remembered.get("citations", [])
        run.stop_reason = "recalled_from_long_term_memory"
        run.reliability_ok = True
        run.source = remembered["source"]
        run.recalled_from_memory = True
        run.total_seconds = time.monotonic() - start_time
        return run

    short_term = ShortTermMemory()
    region_suffix = f" (region: {scenario['region']})" if scenario.get("region") else ""
    last_observation = "(none yet -- this is the first step)"

    for step_num in range(1, MAX_STEPS + 1):
        elapsed = time.monotonic() - start_time
        if elapsed >= MAX_SECONDS:
            run.stop_reason = f"time_budget_exceeded ({elapsed:.1f}s >= {MAX_SECONDS}s)"
            break
        if run.total_cost_usd >= MAX_ESTIMATED_COST_USD:
            run.stop_reason = f"cost_budget_exceeded (${run.total_cost_usd:.4f} >= ${MAX_ESTIMATED_COST_USD})"
            break

        # -- Short-term memory: build the prompt from the distilled fact
        # list + only the MOST RECENT observation, instead of replaying
        # the entire raw transcript that has accumulated so far. This is
        # the concrete "summarisation instead of full history" mechanism.
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {question}{region_suffix}\n\n{short_term.as_prompt_block()}\n\nLast observation: {last_observation}"},
        ]

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

            used_web = any(s.action == "web_search" for s in run.steps)
            run.source = "external_web" if used_web else "internal_policy"

            long_term_store = remember(long_term_store, question, run.final_answer, run.source, run.citations)
            save_long_term_memory(long_term_store)
            break

        if action == "search_policy":
            result = search_policy(action_input.get("query", ""), action_input.get("region"))
        elif action == "get_chunk":
            result = get_chunk(action_input.get("chunk_id", ""))
        elif action == "web_search":
            result = web_search(action_input.get("query", ""))
        else:
            result = type("R", (), {"output": f"(unknown tool {action!r} -- ignored)"})()

        observation = result.output
        run.steps.append(Step(step_num, thought, action, action_input, observation, time.monotonic() - start_time, in_tok, out_tok, used_fallback))

        short_term.add(distill_observation(action, action_input, observation))
        last_observation = observation
    else:
        run.stop_reason = f"max_steps_exceeded ({MAX_STEPS})"

    run.total_seconds = time.monotonic() - start_time
    return run
