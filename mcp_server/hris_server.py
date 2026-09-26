"""Week 9 -- a standalone MCP server exposing the one complete, safety-
gated capability of this HR-policy app: app.refusal.answer_question(),
the two-gate (pre-generation similarity threshold + post-hoc citation
resolution) RAG pipeline built in Weeks 3-6.

This server contains zero agent reasoning -- no ReAct loop, no
Thought/Action parsing, nothing resembling app/agent.py's logic. Its one
tool internally calls an LLM (via app.generation.generate_answer(), as
part of answer_question()) to do its job well, the same way a
"calculator" tool might use floating point math -- that is not the same
thing as "the agent runs on the server." Whatever calls this server
decides on its own, elsewhere, what to do with the result.

IMPORTANT (Qdrant single-process lock): app.vectorstore.get_client()
opens an embedded, file-locked Qdrant database at data/qdrant_data. Only
ONE process may hold that path open at a time. This server should be the
only process touching Qdrant while it runs -- do not also run
app/agent.py's own search_policy/get_chunk tools (which open the same
path) concurrently with this server. See week9_results.md for the full
tradeoff writeup; the production-correct fix is Qdrant server mode
(QdrantClient(url=...) against a standalone Qdrant service), which is
out of scope here since no docker is installed in this environment.

Usage:
    python mcp_server/hris_server.py            # stdio (agent's own use)
    python mcp_server/hris_server.py --http --port 8765   # HTTP (external clients)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastmcp import FastMCP

from app.refusal import answer_question

mcp = FastMCP("hris-server")


@mcp.tool
def ask_hr_policy(question: str, region: str | None = None) -> dict:
    """Ask an HR policy question and get a grounded, citation-checked
    answer, or an honest refusal if the policy corpus doesn't cover it.

    Args:
        question: the HR policy question to ask.
        region: optionally restrict to one region ("APAC", "EMEA", "AMER").
    """
    result = answer_question(question, region=region)
    return {
        "answer": result.answer,
        "refused": result.refused,
        "reason": result.reason,
        "citations": [
            {"chunk_id": c.chunk_id, "policy_id": c.policy_id, "section": c.section}
            for c in result.citations
        ],
    }


@mcp.tool
def list_supported_regions() -> list[str]:
    """Lists the HR regions this policy corpus has coverage for.

    Deliberately simple and Qdrant-free (reads nothing from the vector
    store) -- proves the agent's generic MCP dispatch works for a second,
    genuinely different tool without touching app/agent.py at all.
    """
    return ["APAC", "EMEA", "AMER"]


if __name__ == "__main__":
    if "--http" in sys.argv:
        port = 8765
        if "--port" in sys.argv:
            port = int(sys.argv[sys.argv.index("--port") + 1])
        mcp.run(transport="http", port=port)
    else:
        mcp.run()
