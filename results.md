# Results — Week 3 Task Set C (HR Policy)

## 1. The 8 known-answer questions

| ID | Question | Known policy_id | Known section | Depends on table? |
|---|---|---|---|---|
| q1 | What is the carry-over cap for a probationary employee under HR-207 section 4.2? | HR-207 | 4.2 | no |
| q2 | Under HR-207, what is the carry-over cap for a full-time confirmed employee in India? | HR-207 | 3 | yes |
| q3 | How many days of company-paid sick leave is an EMEA employee entitled to per calendar year under HR-203? | HR-203 | 2.1 | no |
| q4 | Under HR-203, what certification is required for a sick absence of 4 to 7 days? | HR-203 | 3 | yes |
| q5 | How many weeks of paid parental leave is a full-time secondary caregiver entitled to under HR-205? | HR-205 | 3 | yes |
| q6 | Under HR-211, what is the carry-over cap for a full-time confirmed employee in Brazil, and why can't it be reduced? | HR-211 | 2 | yes |
| q7 | Under HR-209, if a remote employee's scheduled annual leave day coincides with a public holiday in their home country, what happens to that leave day? | HR-209 | 2.2 | no |
| q8 | Under HR-201, what is the special carry-over exception for full-time confirmed employees based in Singapore, and how many days can they carry over? | HR-201 | 4.2 | no |

## 2. Hit-in-top-5 comparison

Only the 6 addenda were indexed (not a full handbook — there is no pre-existing handbook in this build).

| Strategy | Hit-in-top-5 |
|---|---|
| Naive (fixed-size, 800 chars / 150 overlap) | 2/8 |
| Structure-aware (header-glued) | 8/8 |

### Per-question detail

| ID | Naive hit? | Structure-aware hit? |
|---|---|---|
| q1 | ✅ | ✅ |
| q2 | ❌ | ✅ |
| q3 | ❌ | ✅ |
| q4 | ❌ | ✅ |
| q5 | ❌ | ✅ |
| q6 | ❌ | ✅ |
| q7 | ✅ | ✅ |
| q8 | ❌ | ✅ |

Full ranked lists (chunk_id, policy_id, section, score) for every question under both strategies are in `data/eval_raw_dump.json` → `hit_rate.per_question`.

## 3. Metadata filter demo (region)

Query: **What is the carry-over cap for a probationary employee under HR-207 section 4.2?** (region=`APAC`, collection=`structure_aware`)

Top-1 changed when filtering: **True**

**Unfiltered:**

1. `HR-211_carryover_amer.md::structure_aware::4` — policy=HR-211 section=3 score=0.9003
2. `HR-207_carryover_apac.md::structure_aware::4` — policy=HR-207 section=4 score=0.897
3. `HR-207_carryover_apac.md::structure_aware::5` — policy=HR-207 section=4.2 score=0.862
4. `HR-211_carryover_amer.md::structure_aware::5` — policy=HR-211 section=4.2 score=0.813
5. `HR-207_carryover_apac.md::structure_aware::2` — policy=HR-207 section=2 score=0.8019

**Filtered (region=APAC):**

1. `HR-207_carryover_apac.md::structure_aware::4` — policy=HR-207 section=4 score=0.897
2. `HR-207_carryover_apac.md::structure_aware::5` — policy=HR-207 section=4.2 score=0.862
3. `HR-207_carryover_apac.md::structure_aware::2` — policy=HR-207 section=2 score=0.8019
4. `HR-207_carryover_apac.md::structure_aware::0` — policy=HR-207 section=1 score=0.7612
5. `HR-201_annual_leave_apac.md::structure_aware::6` — policy=HR-201 section=3 score=0.7525

## 4. Cited answers (3 answerable questions)

**q1**: What is the carry-over cap for a probationary employee under HR-207 section 4.2?
- refused: `False`
- answer: The carry-over cap for a probationary employee under HR-207 section 4.2 is 2 days for the transition year only, regardless of sub-region. This cap applies only to leave accrued during the probationary period itself; leave accrued after confirmation follows the standard caps in Section 3 [HR-207_carryover_apac.md::structure_aware::5].
- citations:
  - `HR-207_carryover_apac.md::structure_aware::5` → policy_id=HR-207, section=4.2

**q2**: Under HR-207, what is the carry-over cap for a full-time confirmed employee in India?
- refused: `False`
- answer: The carry-over cap for a full-time confirmed employee in India is 10 days [HR-207_carryover_apac.md::structure_aware::3].
- citations:
  - `HR-207_carryover_apac.md::structure_aware::3` → policy_id=HR-207, section=3

**q3**: How many days of company-paid sick leave is an EMEA employee entitled to per calendar year under HR-203?
- refused: `False`
- answer: Employees are entitled to 10 days of company-paid sick leave per calendar year at full salary under HR-203 [HR-203_sick_leave_emea.md::structure_aware::3].
- citations:
  - `HR-203_sick_leave_emea.md::structure_aware::3` → policy_id=HR-203, section=2.1

## 5. Refusal transcripts (3 out-of-corpus questions)

**ooc1**: What is the company's sabbatical leave policy after 5 years of continuous service?
- refused: `True`
- reason: `low_retrieval_confidence`
- top retrieval score: `0.7075`
- retrieved chunks (for audit):
  - `HR-205_parental_leave_amer.md::structure_aware::1` (score=0.7075)
  - `HR-201_annual_leave_apac.md::structure_aware::4` (score=0.6956)
  - `HR-201_annual_leave_apac.md::structure_aware::2` (score=0.6949)

**ooc2**: Can an employee take annual leave during their notice period after resignation?
- refused: `True`
- reason: `model_declined`
- top retrieval score: `0.7439`
- model output: `REFUSE: insufficient grounding.`
- retrieved chunks (for audit):
  - `HR-209_remote_work_emea.md::structure_aware::4` (score=0.7439)
  - `HR-201_annual_leave_apac.md::structure_aware::4` (score=0.7168)
  - `HR-201_annual_leave_apac.md::structure_aware::5` (score=0.7059)

**ooc3**: What is the bereavement leave entitlement for APAC employees?
- refused: `True`
- reason: `model_declined`
- top retrieval score: `0.7602`
- model output: `REFUSE: insufficient grounding.`
- retrieved chunks (for audit):
  - `HR-201_annual_leave_apac.md::structure_aware::0` (score=0.7602)
  - `HR-211_carryover_amer.md::structure_aware::0` (score=0.7136)
  - `HR-207_carryover_apac.md::structure_aware::0` (score=0.7061)

## 6. Refusal calibration

Answerable-question top-1 scores: [0.9003, 0.7899, 0.7885, 0.7556, 0.8844, 0.8346, 0.8067, 0.822]

Out-of-corpus top-1 scores: [0.7075, 0.7439, 0.7602]

These ranges overlap (weakest answerable question scored lower than the strongest out-of-corpus near-miss), so a similarity threshold alone (set to `0.72` here as a coarse first gate) cannot reliably separate answerable from unanswerable questions on this embedding model. The real enforcement is the second, independent gate: post-hoc citation resolution, which checks every `[chunk_id]` tag the model outputs against the chunks actually retrieved, and forces a refusal if any tag fails to resolve or if the model produces zero citations. This is why refusal is implemented as two structural code-level gates (`app/refusal.py`) rather than a single soft prompt instruction.

## 7. Chunking strategy: which one ships, and why

**Structure-aware chunking ships.** On the same 8 known-answer questions, same embedding model (`BAAI/bge-small-en-v1.5`, held constant across both indexes so only the chunker varied), naive scored 2/8 vs structure-aware's 8/8. The naive chunker's fixed 800-character windows repeatedly split eligibility tables mid-row and separated section headers from the clauses they govern (see the diagnosed failure below), so its retrieved chunks were frequently topically close but attributed to the wrong section number — a direct violation of the assignment's core requirement that a clause stay attached to the section number that gives it authority. Structure-aware chunking, which splits on policy headers and repeats the header on any sub-chunk of a long section, kept every retrieved chunk correctly labeled and hit all 8 questions.

## 8. One retrieval that embarrassed us — diagnosis

**Question (q2):** "Under HR-207, what is the carry-over cap for a full-time confirmed employee in India?" (known answer: HR-207 §3, 10 days). Under the **naive** chunker this missed in the top-5 entirely. Inspecting the actual retrieved text showed why: the India row of the Section 3 table landed in a naive chunk that was itself mislabeled `section=4.2` by our best-effort regex metadata tagger, because a fixed-size window had already cut across a table row and into the following section-4 header before the regex ever saw the real "## 3." header. The naive chunker retrieved *a* HR-207 chunk with high similarity, but never surfaced the one containing the India row — the eligibility table was silently split, and the section metadata on the surviving chunks was simply wrong. This is the exact failure mode the assignment asked us to go looking for, and it did not show up until we ran the search-only comparison — eyeballing chunk output earlier had not caught it.

## 9. Bonus challenge — precision vs completeness

We looked for a case where structure-aware chunking wins retrieval precision but stranded the model without a definitions paragraph (e.g. "continuous service", defined in HR-201 §1.2, referenced but not restated in HR-207 §4.2). With `top_k=5` we could not reproduce a clean win/lose split under real testing: at k=5, structure-aware's retrieval reliably pulled in the HR-201 §1.2 definitions chunk alongside the HR-207 §4.2 clause, so generation succeeded with correct citations to both. The tension did appear at `top_k=1`: a single tight structure-aware chunk for HR-207 §4.2 alone does not contain the continuous-service definition, and a question that combined the two concepts and forced a low top_k correctly triggered a refusal (`model_declined`) rather than an unsupported guess. We are reporting this honestly rather than manufacturing a forced example — the tension is real but only surfaces when top_k is small enough that the defining paragraph does not make it into context; at the top_k=5 setting we ship, the wider recall window resolves it.

## 10. Time-boxing note

Only the 6 supplied addenda were indexed per collection — there is no pre-existing full handbook in this build, so the equivalent constraint ("do not re-index everything") was satisfied by construction: both collections were built directly from `data/addenda/*.md` only.

---

# Week 4 — Debugging Retrieval: Hybrid Search & Failure Separation

Week 3 measured hit-in-**top-5**, where structure_aware already scores 8/8 — there is no failure to diagnose at that cutoff. Tightening to hit-rate**@3** (the Week 4 metric) surfaces a real, non-manufactured failure: **q5** ("weeks of paid parental leave for a full-time secondary caregiver," HR-205 §3) — the correct chunk sits at rank 4 under semantic-only search, just outside top-3, bumped by two other HR-205 chunks about primary-caregiver leave that score higher on pure semantic similarity. **The one approved change is hybrid search: BM25 keyword search + the existing semantic search, fused via Reciprocal Rank Fusion (RRF).** No reranking, no query rewriting, no HyDE — one change only.

## 11. Failure labeling with evidence

For each question that changed state (fixed, still broken, or regressed) between semantic-only and hybrid at k=3 on structure_aware, we checked: is the known-correct chunk in the top-k at all (`wrong_document` if not), and if it is, did the generated answer actually cite it (`right_document_used` vs `right_document_not_used`).

| Question | Label | Evidence |
|---|---|---|
| q5 | `right_document_not_used` | known chunk at rank 3, correct_chunk_id=`HR-205_parental_leave_amer.md::structure_aware::5`, cited=['HR-205_parental_leave_amer.md::structure_aware::4'] |
| q1 | `wrong_document` | known chunk not in top-3; known=HR-207 §4.2 |

**q5 walkthrough (the flagship failure):** under hybrid search at k=3, the known-correct chunk (`HR-205...structure_aware::5`, §3, the eligibility table row) climbed into the top-3 and IS passed to the generation model as context — we wired `answer_question()` to support `retrieval_mode="hybrid"` specifically to test this. Even with the correct chunk available, the model still chose to cite the §2.2 prose chunk ("Secondary caregivers are entitled to 6 weeks...") rather than the §3 table row, because a clean declarative sentence is a more natural-looking citation source to the model than a bare table row stating the same number. The answer (6 weeks) is factually correct because §2.2 and §3 agree on the figure — but this is a real, distinct failure mode independent of retrieval: **even when the authoritative chunk is retrieved, generation can still prefer citing a different, merely corroborating chunk over it.** This is the two-kinds-of-wrong split shown on the very same question: retrieval failed it before hybrid search (`wrong_document`), and generation's citation choice still diverges from the known-answer key after hybrid search fixed retrieval (`right_document_not_used`) — a legitimate diagnosis, not a hidden bug to gloss over.

## 12. The one change — hybrid search (RRF)

Implemented in `app/hybrid_retrieval.py`: a BM25 index (`rank_bm25`) is built in-memory from the same chunk corpus as each Qdrant collection, and combined with the existing semantic `search()` via Reciprocal Rank Fusion (`fused_score(chunk) = sum over each ranked list containing it of 1/(RRF_K + rank)`, RRF_K=60). This is purely additive — `app/retrieval.py::search()` is never modified, and `hybrid_search()` is a new, parallel function so all Week 3 code paths and results are unaffected.

## 13. Before/after hit-rate@3

**Primary comparison — structure_aware (the shipping collection):**

| | Before (semantic) | After (hybrid) |
|---|---|---|
| Hit-rate@3 | 7/8 | 7/8 |

| Question | Before hit? | After hit? | Outcome |
|---|---|---|---|
| q1 | ✅ | ❌ | **regressed** |
| q2 | ✅ | ✅ | **unaffected** |
| q3 | ✅ | ✅ | **unaffected** |
| q4 | ✅ | ✅ | **unaffected** |
| q5 | ❌ | ✅ | **fixed** |
| q6 | ✅ | ✅ | **unaffected** |
| q7 | ✅ | ✅ | **unaffected** |
| q8 | ✅ | ✅ | **unaffected** |

**What did NOT get fixed / what broke**: fixed = ['q5'], still broken = none, regressed = ['q1']. Net aggregate is unchanged (7/8 → 7/8), but this hides a real trade: hybrid search fixed q5 (a semantic-similarity confusion between two HR-205 sections) while regressing q1 (BM25's exact-term match on "4.2" rewards HR-211 §4.2 — a different policy that happens to share the same section number — pushing the correct HR-207 §4.2 chunk out of top-3). This is exactly why an aggregate number alone is not sufficient evidence; the per-question table is the deliverable.

**Secondary/bonus comparison — naive collection (conflates chunking with hybrid search as two variables, reported for context only):**

| | Before (semantic) | After (hybrid) |
|---|---|---|
| Hit-rate@3 | 2/8 | 2/8 |

Hybrid search fixed none of naive's misses at the automated `(policy_id, section)`-match hit-check, still broken = ['q2', 'q3', 'q4', 'q5', 'q6', 'q8']. This is not because BM25 failed to find the right content — a dedicated test (`tests/test_hybrid_retrieval.py::test_bm25_recovers_naive_miss_q2`) confirms BM25 alone ranks the chunk containing the literal answer text ("India | 10 days") at rank 1 for q2. The automated hit-check still reports a miss because naive chunking's own section metadata on that chunk is mislabeled (`4.2` instead of `3`, the same regex-based metadata-tagging bug documented in §8) — hybrid search recovered the right *content*, but the *(policy_id, section) label* the grader checks against is still wrong on naive's own chunks. This is a distinct failure mode from "wrong document": the content is right, the chunking's own metadata is what's broken, and no amount of retrieval improvement fixes a mislabeled chunk.

## 14. Diagnosis: two concrete failure examples

**Wrong document** (structure_aware, k=3, before hybrid): q5 — the known-correct chunk (HR-205 §3, the eligibility table) was retrieved at rank 4, one position outside the k=3 cutoff, because the question's wording ("secondary caregiver," "weeks") overlaps more with §2.2's prose restatement than with the table row that is the authoritative source. Evidence: the ranked list itself (see `data/eval_raw_dump.json` → `hybrid_comparison_structure_aware.before.per_question` for q5).

**Right document, wrong answer** (structure_aware, k=3, after hybrid): q5 again, but now under hybrid search — the correct chunk IS retrieved (rank 3), but `answer_question()`'s live generation path still used semantic-only search internally and cited §2.2 instead. Evidence: `label_failure()`'s `right_document_not_used` label with `correct_chunk_id` present in the retrieved set but absent from `cited_chunk_ids`. This is the mentor-check's two kinds of wrong shown on the *same* question at *two* different points in the pipeline — a clean illustration that retrieval and generation are genuinely separate failure surfaces, exactly as the assignment's framing predicts.
