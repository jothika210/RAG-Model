# Error Analysis — Named Problems, Ranked (Week 5)

Fill this in only after every trace in `trace_worksheet.md` has an honest note.

## 1. Open coding notes

Per-trace notes live in `trace_worksheet.md` — all 20 traces read and annotated before any grouping happened, as required.

## 2. Named problem groups

| Group name | Description | Trace IDs in this group |
|---|---|---|
| Correctly grounded answer | Retrieval found the right chunk, the stated fact matches the source text, and the citation resolves to that chunk — including under rephrasing, typos, and multi-part questions. | t000, t001, t002, t005, t006, t007, t014, t015, t017, t019, t027, t030, t031 |
| False refusal near the confidence threshold | The correct chunk WAS retrieved (just not ranked first), but the top-1 similarity score narrowly missed the fixed 0.72 cutoff, so the app refused a question the corpus could actually answer. | t016 |
| Correct refusal — region filter excludes the real answer | The question's true region didn't match the region filter applied; the real answer was filtered out, and the app correctly refused instead of answering from the wrong region's documents. | t034, t035 |
| Correct refusal — vague or malformed input | The question gave no identifiable policy fact to look up (single words, fragments); refusing was the right call, though a clarifying follow-up question might serve the user better than a flat refusal. | t008, t039, t040, t041 |

## 3. Ranking (frequency × severity)

Severity: 1 = minor/cosmetic, 2 = wrong but harmless, 3 = actively misleading or harmful.

| Rank | Group | Frequency (count) | Severity (1-3) | Frequency × Severity |
|---|---|---|---|---|
| 1 | False refusal near the confidence threshold | 1 | 3 | 3 |
| 2 | Correct refusal — vague or malformed input | 4 | 1 | 4 |
| 3 | Correct refusal — region filter excludes the real answer | 2 | 1 | 2 |
| 4 | Correctly grounded answer | 13 | 0 (not a problem) | 0 |

Note on ranking logic: frequency alone would put "vague input" or "correctly grounded" ahead, but the false-refusal case is rated severity 3 because it silently denies a real, retrievable answer to the user with no indication anything was almost found — that's a worse outcome for a real employee than a fragment being (correctly) turned away, so it's ranked #1 despite occurring only once in this sample.

## 4. Chosen fix target

**Which group are you fixing next, and why?**

The false-refusal-near-threshold group (t016), even though it's a sample size of one here. It's the only group where the app actively withheld a real, retrievable answer — the other refusal groups are the system behaving correctly. A single similarity threshold (0.72) cannot reliably separate "answerable" from "unanswerable" on its own, since Week 3's own calibration data already showed the answerable and out-of-corpus score ranges overlap. Fixing this matters more than any of the higher-frequency groups because those are already working as intended.

**Prediction — what do you expect to happen after the fix?**

If the fix is to check top-3 (not just top-1) for a strong-enough match before refusing — since t016's answer chunk was at rank 2 — I expect a small number of previously-refused questions like t016 to now get answered correctly, with citations resolving to the newly-considered rank-2/3 chunks. I do NOT expect this to fix every refusal in the sample: t008, t034, t035, t039, t040, and t041 should all still correctly refuse, since none of those had a real answer sitting anywhere in their retrieved list — so the fix should move the false-refusal count down without reducing the correct-refusal count.
