import httpx

from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL
from app.retrieval import SearchHit

SYSTEM_PROMPT = """You are an HR policy assistant. You answer ONLY using the numbered \
context chunks provided below. Every factual claim in your answer MUST end with a \
citation tag containing ONLY the chunk_id, wrapped in square brackets -- nothing else \
inside the brackets, no "chunk_id=" prefix, no extra words.

Correct example: The carry-over cap is 2 days [HR-207_carryover_apac.md::structure_aware::5].
Incorrect (do not do this): [chunk_id=HR-207_carryover_apac.md::structure_aware::5]
Incorrect (do not do this): [see HR-207_carryover_apac.md::structure_aware::5]

Rules:
- Do not use any knowledge beyond the provided chunks.
- If the chunks do not fully answer the question, respond with exactly this text and \
nothing else: REFUSE: insufficient grounding.
- Never invent a policy, number, or chunk_id that is not present below.
"""


def _build_context(hits: list[SearchHit]) -> str:
    parts = []
    for h in hits:
        parts.append(f"[{h.chunk_id}] (policy_id={h.policy_id}, section={h.section})\n{h.text}")
    return "\n\n---\n\n".join(parts)


def generate_answer(question: str, hits: list[SearchHit]) -> str:
    context = _build_context(hits)
    user_prompt = f"Context chunks:\n\n{context}\n\nQuestion: {question}"

    response = httpx.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]
