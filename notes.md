# Week 5 Notes — Error Analysis (HR Policy, Track C)

## Seeded random sample

Seed: `42` · n: `20` (drawn from a pool of 43 diverse real queries run through the live pipeline)

Trace IDs selected: `t000, t001, t002, t005, t006, t007, t008, t014, t015, t016, t017, t019, t027, t030, t031, t034, t035, t039, t040, t041`

(Matches `data/traces/sampled_trace_ids.json` verbatim. Full trace detail for all 20 — question, fetched chunks with scores, final answer or refusal — is in `data/traces/trace_worksheet.md`.)

## Open-coding sentences (one per trace, observation only — no diagnosis, no category, no fix)

1. **t000** — The answer stated "2 days" and cited `HR-207...naive::2`, tagged section 4.2; the top-fetched chunk also carried section 4.2 and the same identifier.
2. **t001** — The answer stated "10 days" for India and cited `HR-207...structure_aware::3`, tagged section 3, which was the top-ranked fetch.
3. **t002** — The top-ranked fetch was an HR-209 chunk (section 1); the answer instead cited the second-ranked HR-203 chunk (section 2.1) and stated "10 days."
4. **t005** — The answer stated "30 days," gave a statutory (férias) reason for why the figure can't be reduced, and cited `HR-211...structure_aware::3`, the top-ranked fetch.
5. **t006** — The answer described the leave day being credited back to balance and cited `HR-209...naive::1`, tagged section 2.2, the top-ranked fetch.
6. **t007** — The answer stated "7 days" for Singapore and cited `HR-201...structure_aware::10` (section 4.2, the top-ranked fetch); a different fetched chunk, `HR-207...structure_aware::3` (section 3), was not cited even though it also concerns Singapore carry-over.
7. **t008** — The question asked about a sabbatical policy; the top-ranked fetch scored 0.6740, below the 0.72 threshold, and the app refused with reason `low_retrieval_confidence`; none of the five fetched chunks were sabbatical-related by title.
8. **t014** — The question was phrased in first person ("I'm based in India..."); the answer stated "10 days" and cited `HR-207...structure_aware::3` (section 3), the top-ranked fetch.
9. **t015** — The question used the phrase "sick pay"; the answer stated "10 days" and cited `HR-203...structure_aware::3` (section 2.1), which was the second-ranked fetch (rank 1 was section 2.3, uncited).
10. **t016** — The top-ranked fetch (`HR-203...structure_aware::3`, section 2.1) scored 0.7160, below the 0.72 threshold; the app refused with reason `low_retrieval_confidence`; the second-ranked fetch, `HR-203...structure_aware::6` (section 3), was a certification table containing a 4-7 day bracket that overlaps the 5-day absence asked about, and was never surfaced in any answer.
11. **t017** — The question used the phrase "non-primary parent"; the answer stated "6 weeks" and cited `HR-205...structure_aware::4` (section 2.2), the third-ranked fetch (ranks 1-2 were an unrelated HR-211 chunk and an HR-205 section 2.1 chunk).
12. **t019** — The question was phrased as a rewording of the public-holiday scenario; the answer described the day being credited back and cited `HR-209...structure_aware::4` (section 2.2), the top-ranked fetch.
13. **t027** — The question asked about "continuous service" and its effect on "all my leave entitlements"; the answer combined text from three separately-cited chunks (`HR-201...::2` section 1.2, `HR-205...::1` section 1.1, `HR-201...::7` section 3.1), covering the definition and one eligibility rule; no chunk relating to sick leave or carry-over's own continuous-service conditions was cited.
14. **t030** — The question was "secondary caregiver parental leave weeks HR205???"; the answer stated "6 weeks" and cited `HR-205...structure_aware::4` (section 2.2), the top-ranked fetch.
15. **t031** — The question was "carryover cap brasil hr 211 full time"; the answer stated "30 days" and cited `HR-211...structure_aware::3` (section 2.1), the top-ranked fetch.
16. **t034** — The question asked about India under HR-207, but the region filter applied was AMER; all five fetched chunks were HR-211 (AMER); the raw model output was the literal string "REFUSE: insufficient grounding," recorded as reason `model_declined`.
17. **t035** — The question asked about HR-205 (a parental-leave policy tagged AMER), but the region filter applied was EMEA; all five fetched chunks were HR-203/HR-209 (EMEA); the top-ranked fetch scored 0.6659, below the 0.72 threshold, and the app refused with reason `low_retrieval_confidence`.
18. **t039** — The question was "hr policy question please help"; the top-ranked fetch (an HR-205 chunk, section 3) scored 0.7021, below the 0.72 threshold, and the app refused with reason `low_retrieval_confidence`.
19. **t040** — The question was "what about the thing with the days"; the top-ranked fetch scored 0.6498, below the 0.72 threshold, and the app refused with reason `low_retrieval_confidence`.
20. **t041** — The question was the single word "policy"; the top-ranked fetch scored 0.6551, below the 0.72 threshold, and the app refused with reason `low_retrieval_confidence`.

## Replay evidence

**Trace chosen at random, seeded:** seed `7` applied to `random.Random(7).choice(sampled_trace_ids)` → **`t017`** (command: `python scripts/replay_check.py --seed 7`).

**Original (t017):**
```json
{
  "ranked_hits": [
    {"chunk_id": "HR-211_carryover_amer.md::structure_aware::6", "policy_id": "HR-211", "section": "4",   "region": "AMER", "score": 0.7673},
    {"chunk_id": "HR-205_parental_leave_amer.md::structure_aware::3", "policy_id": "HR-205", "section": "2.1", "region": "AMER", "score": 0.7415},
    {"chunk_id": "HR-205_parental_leave_amer.md::structure_aware::4", "policy_id": "HR-205", "section": "2.2", "region": "AMER", "score": 0.7384},
    {"chunk_id": "HR-205_parental_leave_amer.md::structure_aware::8", "policy_id": "HR-205", "section": "3.3", "region": "AMER", "score": 0.7121},
    {"chunk_id": "HR-205_parental_leave_amer.md::structure_aware::6", "policy_id": "HR-205", "section": "3.1", "region": "AMER", "score": 0.685}
  ],
  "refused": false,
  "reason": null,
  "answer": "As the non-primary parent, you are entitled to 6 weeks of paid parental leave at full salary under HR-205 [HR-205_parental_leave_amer.md::structure_aware::4].",
  "citations": [{"chunk_id": "HR-205_parental_leave_amer.md::structure_aware::4", "policy_id": "HR-205", "section": "2.2"}]
}
```

**Replayed (t017) — reconstructed from the trace's own `question`, `strategy`, `region`, `retrieval_mode` fields alone, re-run through `answer_question()`:**
```json
{
  "ranked_hits": [
    {"chunk_id": "HR-211_carryover_amer.md::structure_aware::6", "policy_id": "HR-211", "section": "4",   "region": "AMER", "score": 0.7673},
    {"chunk_id": "HR-205_parental_leave_amer.md::structure_aware::3", "policy_id": "HR-205", "section": "2.1", "region": "AMER", "score": 0.7415},
    {"chunk_id": "HR-205_parental_leave_amer.md::structure_aware::4", "policy_id": "HR-205", "section": "2.2", "region": "AMER", "score": 0.7384},
    {"chunk_id": "HR-205_parental_leave_amer.md::structure_aware::8", "policy_id": "HR-205", "section": "3.3", "region": "AMER", "score": 0.7121},
    {"chunk_id": "HR-205_parental_leave_amer.md::structure_aware::6", "policy_id": "HR-205", "section": "3.1", "region": "AMER", "score": 0.685}
  ],
  "refused": false,
  "reason": null,
  "answer": "As the non-primary parent, you are entitled to 6 weeks of paid parental leave at full salary under HR-205 [HR-205_parental_leave_amer.md::structure_aware::4].",
  "citations": [{"chunk_id": "HR-205_parental_leave_amer.md::structure_aware::4", "policy_id": "HR-205", "section": "2.2"}]
}
```

**Comparison:** ranked_hits chunk_id order match: **True** · answer text match: **True** · refused flag match: **True** — an exact match.

**Fields present on the trace that made this replay possible:** the exact question text; strategy/region/retrieval_mode (the parameters that select the retrieval path); the full ranked list of retrieved chunk_ids with scores; the raw, unprocessed model output; the refused flag and reason (which gate fired, if any); the final answer and resolved citations.

**Fields NOT reconstructable from the trace alone (what we could not fully verify from the trace record itself):**
- No explicit prompt-template *version* string is stored per trace — the system prompt in `app/generation.py` is a single hardcoded constant with no version tag, so a future prompt edit would leave old traces with no record of which prompt version actually produced them.
- No explicit model name or temperature is stored per trace — both are read from global config (`OPENROUTER_MODEL`, and `temperature=0` hardcoded in `app/generation.py`) at call time rather than captured onto the `Trace` record itself. This replay used whatever the current config says; a trace alone cannot prove that config was unchanged since collection.
- The embedding model version is likewise a global config constant, not recorded per trace. Retrieval score reproducibility depends on the embedding model and the Qdrant index content being unchanged between collection and replay — not bit-for-bit guaranteed if either changes, though in this instance the match was exact.

## Redaction confirmation

No employee names or employee IDs are written to the trace file, in either direction — confirmed by direct inspection of `data/traces/traces_raw.json` and every source document in `data/addenda/`. The corpus is entirely synthetic HR policy text describing categories of employees ("full-time confirmed," "probationary") rather than named individuals, and the trace-collection pool never asks about or references a specific person. There is no redaction *step* because there is nothing to redact — the corpus was designed without personal identifiers from the start.

## Dated, falsifiable prediction

**Date:** 2026-09-05

**Target mode:** False refusal near the confidence threshold (see `taxonomy.md`).

**Prediction:** Checking the top-3 retrieved chunks (not just the top-1) against the 0.72 confidence threshold before refusing — i.e. refusing only if *none* of the top 3 clears the threshold, instead of gating on the top-1 score alone — will drop the false-refusal-near-threshold mode from **1/20 (5%)** to **0/20 (0%)** on this exact sample, without increasing the count of correctly-refused traces (currently **6/20 (30%)** combined across the out-of-corpus, region-mismatch, and vague-input modes), which should remain at **6/20 (30%)**.

**Git commit:** `<pasted after commit — see below>`

## Why a public benchmark would have missed these modes

A benchmark like MMLU or HumanEval scores answers against a fixed, general-knowledge or code-correctness key that has nothing to do with this specific document set, so it cannot detect a retrieval-confidence threshold that happens to sit too close to real answerable questions in *this* corpus. It also has no notion of a region filter excluding the correct source document, or of a chunker's section metadata disagreeing with the text it's attached to — both are properties of this particular ingestion and retrieval pipeline, not of the model's general knowledge or reasoning ability. A model can score well on every public benchmark while still silently refusing a real HR question because one similarity score landed at 0.716 instead of 0.72 — that failure is invisible to any evaluation that never runs this exact corpus through this exact retrieval stack.
