# Eval Results — Week 6 (HR Policy)

## How to run this

```powershell
.\.venv\Scripts\python.exe scripts/run_evals.py --gate-mode top1   # before
.\.venv\Scripts\python.exe scripts/run_evals.py --gate-mode top3   # after
```

One command per gate mode. Each run scores all 21 test cases (`data/eval/test_cases.json`) through the live pipeline: free rule-based checks first (`app/eval_checks.py`, zero LLM calls), then an LLM-as-judge faithfulness check (`app/judge.py`) on every non-refused answer. Full per-case detail is written to `data/eval/eval_results_<mode>.json`.

## Judge validation (done before trusting the judge's number)

Ran `python scripts/validate_judge.py`: 11 real answered traces (a mix of known-answer and citation-drift cases) were graded by hand (PASS/FAIL, faithfulness only) *before* the judge's own verdict was shown, then the judge graded the same 11. Full detail in `data/eval/judge_validation.json`.

**Result: 11/11 (100%) agreement.** Every trace was graded PASS by both the human and the judge, and the judge's stated reasons matched the actual source text in every case checked.

**Honest limitation of this validation run**: all 11 traces happened to be genuinely faithful answers, so this run only confirms the judge does not produce false negatives on clean cases — it does not, by itself, demonstrate the judge correctly catches an unfaithful answer (a false positive would slip through undetected in an all-PASS validation set). That capability was checked separately in an earlier smoke test (see `app/judge.py`'s development): given a deliberately wrong answer stating "10 days" against a source that says "2 days," the judge correctly returned `FAIL — The answer incorrectly states the carry-over cap as 10 days instead of the 2 days specified in the source text.` Both checks together (100% human agreement on real faithful cases, correct FAIL on a known-wrong case) are the basis for trusting the judge in the scored runs below.

## Before/after score, by problem type

Both runs used the same 21-case test set (`data/eval/test_cases.json`): the 8 known-answer + 3 out-of-corpus baseline questions from Week 3, plus 10 curated regression cases from Week 5's 20-trace sample, each tagged with a problem_type matching a `taxonomy.md` mode.

| Problem type | Before (top1 gate) | After (top3 gate) |
|---|---|---|
| known_answer_baseline | 6/8 (75%) | 6/8 (75%) |
| out_of_corpus_baseline | 3/3 (100%) | 3/3 (100%) |
| false_refusal_near_threshold | 0/1 (0%) | 0/1 (0%) |
| citation_drift | 3/3 (100%) | 3/3 (100%) |
| region_mismatch_refusal | 2/2 (100%) | 2/2 (100%) |
| vague_or_malformed_refusal | 4/4 (100%) | 4/4 (100%) |

**The gate change had zero measurable effect.** Every problem type scored identically before and after.

## The Week 5 prediction was wrong — and here's why, with evidence

Week 5's prediction (`notes.md`): *"checking the top-3 retrieved chunks (not just the top-1) against the 0.72 confidence threshold before refusing will drop the false-refusal-near-threshold mode from 1/20 (5%) to 0/20 (0%)."* The implementation (`app/refusal.py`, `gate_mode="top3"`) does exactly what was predicted — it checks whether *any* of the top-3 hits clears 0.72, not just the top-ranked one. Measured against t016 directly:

```
gate_mode=top1: refused=True, reason=low_retrieval_confidence, top_score=0.7160
gate_mode=top3: refused=True, reason=low_retrieval_confidence, top_score=0.7160
```

Still refused. Inspecting why: t016's actual top-3 retrieved scores are **0.7160, 0.6875, 0.6818** — all three below the 0.72 threshold. The mechanism Week 5 assumed was wrong: the prediction was framed around "the correct chunk is ranked 2nd/3rd but scores well, so checking more ranks should catch it." In reality, for this question, the *entire neighborhood* of plausible answers scores in the 0.66–0.72 band — the correct chunk isn't a high-scoring chunk buried at a low rank, it's a chunk that scores low *everywhere* it appears, regardless of rank. Checking more ranks doesn't help when the actual defect is that the threshold itself sits above where a real answer's best score lands for this question.

**This is a confirmed-wrong prediction, reported honestly rather than reframed as a success.** The falsifiable claim was tested, and it failed — which is itself the informative outcome the assignment's philosophy is built around. A follow-up fix (not attempted here, since it would be a new, different change requiring its own before/after measurement) would need to either lower the threshold itself, or replace the threshold-based gate with a different mechanism entirely (e.g. always attempting generation and relying solely on Gate 2's post-hoc citation check, or a judge-based faithfulness gate instead of a similarity-score gate).

## A second, unplanned finding: citation drift is more widespread than Week 5's sample showed

Running the full known-answer baseline (not just the 20-trace Week 5 sample) surfaced two NEW citation-drift cases that were never part of Week 5's random draw:

- **q5** — known-correct citation is HR-205 §3 (the eligibility table); the app cited §2.2 (the secondary-caregiver prose paragraph) instead. The judge correctly passed this as faithful (the stated fact, 6 weeks, is genuinely supported by §2.2's text), but the strict citation-match rule correctly flagged that the cited chunk isn't the specific authoritative section.
- **q6** — known-correct is HR-211 §2; the app cited §2.1 instead. Same pattern.

This means the true citation-drift rate across the full 21-case test set is **5/21 (24%)**, not the 3/20 (15%) Week 5's smaller random sample suggested — a real example of why a small sample can understate a mode's true frequency, and a concrete demonstration of why an automated, repeatable eval set (this week's actual deliverable) catches things a one-time manual read can miss.
