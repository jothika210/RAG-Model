"""Week 7 extension -- short-term and long-term memory for the agent.

Short-term memory: a distilled, running scratchpad of facts learned
WITHIN one run. Instead of re-sending the entire growing raw transcript
to the LLM every turn (which is what the loop did before this
extension), only a short bulleted list of what's already been learned
is injected -- a concrete, inspectable stand-in for "summarisation."

Long-term memory: a flat JSON file that persists ACROSS separate
run_agent() calls, so a question already answered once doesn't need to
be re-searched from scratch -- a hand-buildable stand-in for the
"mem0 / vector memory" course topic, scaled for this project (no new
infrastructure, just a JSON file, human-readable and inspectable).
"""

import json
import re
import time
from pathlib import Path

from app.config import BASE_DIR

LONG_TERM_MEMORY_PATH = BASE_DIR / "data" / "agent" / "long_term_memory.json"


class ShortTermMemory:
    """A running list of short, distilled fact strings learned during one
    agent run. Injected into the prompt each turn INSTEAD OF the full raw
    conversation transcript, so the model reads a compact summary of
    progress rather than re-reading everything verbatim every step.
    """

    def __init__(self) -> None:
        self._facts: list[str] = []

    def add(self, fact: str) -> None:
        fact = fact.strip()
        if fact:
            self._facts.append(fact)

    def as_prompt_block(self) -> str:
        if not self._facts:
            return "What I've learned so far: (nothing yet -- this is the first step)"
        lines = ["What I've learned so far:"]
        lines.extend(f"{i}. {fact}" for i, fact in enumerate(self._facts, 1))
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._facts)


def distill_observation(action: str, action_input: dict, observation: str) -> str:
    """Turns one tool's raw observation into a distilled fact for
    ShortTermMemory -- a small, deterministic transformation of the
    tool's own structured result, not a second LLM call (keeps this free
    and fast, consistent with the "simple checks first" pattern already
    used elsewhere in this codebase, e.g. app/eval_checks.py).

    search_policy's observation holds MULTIPLE ranked results, and the
    one the agent actually needs is not always the top-ranked one (see
    race_results.md's citation-drift findings) -- keeping only the first
    line here was a real bug found during testing: the model would fetch
    a useful chunk via get_chunk, but a LATER search_policy call would
    overwrite that context, and the next turn's memory block no longer
    showed which earlier chunk_id was actually worth revisiting. All
    ranked lines are preserved (still capped, so this stays a short
    scratchpad entry, not the full raw transcript).
    """
    lines = observation.splitlines() if observation else ["(no result)"]
    if action == "search_policy":
        query = action_input.get("query", "")
        kept = "; ".join(line[:150] for line in lines[:5])
        return f"Searched for {query!r} -> results: {kept}"
    if action == "get_chunk":
        chunk_id = action_input.get("chunk_id", "")
        return f"Fetched chunk {chunk_id!r} -> {lines[0][:200]}"
    if action == "web_search":
        query = action_input.get("query", "")
        kept = "; ".join(line[:150] for line in lines[:3])
        return f"Web-searched {query!r} (external, not HR policy) -> {kept}"
    return f"{action}({action_input}) -> {lines[0][:150]}"


def _normalize_question(question: str) -> str:
    return re.sub(r"\s+", " ", question.strip().lower())


def load_long_term_memory() -> dict:
    if not LONG_TERM_MEMORY_PATH.exists():
        return {}
    try:
        return json.loads(LONG_TERM_MEMORY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_long_term_memory(store: dict) -> None:
    LONG_TERM_MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    LONG_TERM_MEMORY_PATH.write_text(json.dumps(store, indent=2), encoding="utf-8")


def lookup(store: dict, question: str) -> dict | None:
    return store.get(_normalize_question(question))


def remember(store: dict, question: str, answer: str, source: str, citations: list[str]) -> dict:
    """Adds one entry to the in-memory store and returns it (caller is
    responsible for calling save_long_term_memory() to persist it)."""
    key = _normalize_question(question)
    store[key] = {
        "question": question,
        "answer": answer,
        "source": source,  # "internal_policy" | "external_web" | "refused"
        "citations": citations,
        "remembered_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    return store
