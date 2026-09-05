"""Week 6 -- LLM-as-judge for faithfulness: does the answer's stated
claims actually appear in / match the cited chunk's text? This is the
"harder stuff a rule can't check" category from the assignment -- rules
can verify a citation RESOLVES to a real chunk (app/eval_checks.py), but
not whether the answer's prose is actually FAITHFUL to that chunk's
content.

This is a dedicated, separate OpenRouter call with its own system
prompt -- it does NOT reuse app/generation.py's answer-generation prompt,
since judging and answering are different tasks with different failure
modes if conflated.
"""

from dataclasses import dataclass

import httpx

from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL

JUDGE_SYSTEM_PROMPT = """You are a strict fact-checker. You are given a \
question, an answer someone gave, and the exact source text the answer \
claims to be based on. Your only job is to decide: is every factual claim \
in the answer actually supported by the source text?

Respond with EXACTLY one line in this format, nothing else:
VERDICT: PASS | one short sentence why
or
VERDICT: FAIL | one short sentence why

Rules:
- PASS only if every number, date, and claim in the answer is present in \
or directly implied by the source text.
- FAIL if the answer states anything the source text does not support, \
even if the answer sounds plausible or is phrased confidently.
- Do not use outside knowledge of HR policy. Judge only against the given \
source text.
"""


@dataclass
class JudgeResult:
    verdict: str  # "PASS" | "FAIL"
    reason: str
    raw_output: str


def judge_faithfulness(question: str, cited_chunk_text: str, answer: str) -> JudgeResult:
    user_prompt = (
        f"Question: {question}\n\n"
        f"Source text (what the answer claims to be based on):\n{cited_chunk_text}\n\n"
        f"Answer to judge:\n{answer}"
    )

    response = httpx.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
        },
        timeout=60,
    )
    response.raise_for_status()
    raw_output = response.json()["choices"][0]["message"]["content"].strip()

    verdict = "FAIL"
    reason = raw_output
    if raw_output.upper().startswith("VERDICT:"):
        body = raw_output.split(":", 1)[1].strip()
        parts = body.split("|", 1)
        verdict_word = parts[0].strip().upper()
        verdict = "PASS" if verdict_word == "PASS" else "FAIL"
        reason = parts[1].strip() if len(parts) > 1 else body

    return JudgeResult(verdict=verdict, reason=reason, raw_output=raw_output)
