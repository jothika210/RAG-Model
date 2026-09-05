"""Week 7 -- the tools shared by both the hand-built agent (app/agent.py)
and the fixed workflow (app/fixed_workflow.py). Both call these same
functions directly; only the agent additionally needs their text
descriptions (for the LLM to pick the right one), since the fixed
workflow calls them by hard-coded control flow, never by LLM choice.
"""

from dataclasses import dataclass

from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.config import COLLECTIONS
from app.hybrid_retrieval import hybrid_search
from app.vectorstore import get_client

DEFAULT_COLLECTION_KEY = "structure_aware"


@dataclass
class ToolCallResult:
    tool_name: str
    output: str  # human/LLM-readable string -- this is what becomes the "Observation" in the agent loop


def search_policy(query: str, region: str | None = None) -> ToolCallResult:
    """Searches the HR policy corpus (hybrid: BM25 + semantic, RRF-fused)
    and returns the top-5 ranked chunks as a readable observation string.
    """
    hits = hybrid_search(query, DEFAULT_COLLECTION_KEY, top_k=5, region=region)
    lines = []
    for h in hits:
        snippet = h.text.strip().replace("\n", " ")[:180]
        lines.append(f"[{h.chunk_id}] policy={h.policy_id} section={h.section} score={h.score:.3f}: {snippet}")
    output = "\n".join(lines) if lines else "(no results)"
    return ToolCallResult(tool_name="search_policy", output=output)


def get_chunk(chunk_id: str) -> ToolCallResult:
    """Fetches one specific chunk's full text by its exact chunk_id, for
    chasing a cross-reference noticed in a previous search result (e.g.
    'as defined in HR-201 Section 1.2')."""
    client = get_client()
    collection_name = COLLECTIONS[DEFAULT_COLLECTION_KEY]
    points, _ = client.scroll(
        collection_name,
        scroll_filter=Filter(must=[FieldCondition(key="chunk_id", match=MatchValue(value=chunk_id))]),
        limit=1,
        with_payload=True,
    )
    if not points:
        return ToolCallResult(tool_name="get_chunk", output=f"(no chunk found with id {chunk_id!r})")
    payload = points[0].payload or {}
    output = f"[{chunk_id}] policy={payload.get('policy_id')} section={payload.get('section')}: {payload.get('text', '')}"
    return ToolCallResult(tool_name="get_chunk", output=output)


TOOL_DESCRIPTIONS = """You have access to these tools:

1. search_policy(query: string, region: string or null)
   Searches the HR policy corpus for chunks relevant to `query`. Optionally
   restrict to one region ("APAC", "EMEA", or "AMER"). Returns up to 5
   ranked chunks, each with its chunk_id, policy_id, section, and a text
   snippet. Use this to find the source for a specific fact.

2. get_chunk(chunk_id: string)
   Fetches the FULL text of one exact chunk you already know the id of.
   Use this when a chunk you retrieved via search_policy mentions a
   definition or rule "as defined in <policy> Section <x>" and you need
   that definition's exact wording before you can answer confidently.

3. finish(summary: string, citations: list of chunk_id strings)
   Ends the task. `summary` is your final answer to the user's question,
   citing every claim. `citations` lists every chunk_id you actually used
   to support the summary. Call this only when you have enough information
   to answer completely, or when you have determined the question cannot
   be fully answered from the corpus.

Respond with EXACTLY this format on every turn, nothing else:
Thought: <your reasoning about what to do next>
Action: <tool_name>
Action Input: <a single JSON object with the tool's arguments>
"""
