"""Week 7 extension -- a free external web search tool for the agent,
strictly as a FALLBACK when the internal HR policy corpus doesn't cover a
question. Uses `ddgs` (DuckDuckGo search, no API key, no cost).

This must never be confused with an internal policy citation -- every
result is explicitly prefixed "[EXTERNAL WEB]" in the observation string
so both the agent's own reasoning and a human reading the step log can
tell at a glance that this did NOT come from the controlled HR corpus.
"""

from ddgs import DDGS

from app.agent_tools import ToolCallResult


def web_search(query: str, max_results: int = 5) -> ToolCallResult:
    try:
        results = DDGS().text(query, max_results=max_results)
    except Exception as e:
        return ToolCallResult(tool_name="web_search", output=f"[EXTERNAL WEB] search failed: {e}")

    if not results:
        return ToolCallResult(tool_name="web_search", output="[EXTERNAL WEB] (no results)")

    lines = []
    for r in results:
        title = r.get("title", "")
        href = r.get("href", "")
        body = (r.get("body", "") or "").strip().replace("\n", " ")[:200]
        lines.append(f"[EXTERNAL WEB] {title} ({href}): {body}")
    return ToolCallResult(tool_name="web_search", output="\n".join(lines))
