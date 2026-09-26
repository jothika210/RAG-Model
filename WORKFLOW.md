# Workflow Guide — Weeks 4 through 7

This is the one place that explains **what each week actually does, why it exists,
how it connects to the week before it, and the exact command to run it yourself.**

All four weeks build on the same base: a RAG app that answers HR-policy questions
from 6 synthetic addenda, with a citation per claim or a refusal when it doesn't
know. That base (Week 3) lives in `app/refusal.py::answer_question()` — every
week below calls that same function, or something built directly on top of it.

```
Week 3  Build the RAG pipeline (retrieval + citation + refusal)
Week 4  Fix ONE retrieval problem, measure before/after with a number
Week 5  Read 20 real traces by hand, name the failure patterns, rank them
Week 6  Turn Week 5's findings into an automatic, repeatable test suite
Week 7  Build an agent for a multi-step task, race it against a fixed sequence
```

Read the sections in order — each one assumes you understand the one before it.

---

## Before you run anything

```powershell
cd D:\RAGmodule
.venv\Scripts\Activate.ps1
```

If `python` inside that shell ever resolves to the wrong interpreter (a known
quirk on this machine), call the venv's Python directly instead:

```powershell
.\.venv\Scripts\python.exe <script>
```

Only **one process** can hold the Qdrant database at a time (`data/qdrant_data/`).
If a script errors with `"already accessed by another instance"`, close any
running `uvicorn` server first.

---

## Week 4 — Hybrid Search: one change, measured honestly

### What problem this solves

The base app searches by **meaning** (semantic similarity — "vector search").
That alone has a blind spot: it can miss an exact keyword or code (like a policy
number) if the wording around it doesn't feel semantically similar enough. Week 4
adds a second search method — **BM25 keyword search** — and combines the two
with a technique called **Reciprocal Rank Fusion (RRF)**: each method produces
its own ranked list, and a chunk's final score is the sum of `1/(rank + 60)`
across whichever lists it appears in. A chunk that ranks well in *either* method
gets rewarded.

### How it's wired in

```
app/hybrid_retrieval.py
    bm25_search()       -- a plain keyword index (rank_bm25), rebuilt in memory
    hybrid_search()      -- calls the existing semantic search() AND bm25_search(),
                            fuses both ranked lists via RRF, returns one list

app/refusal.py::answer_question(..., retrieval_mode="hybrid")
    -- an optional parameter; "semantic" (default) is untouched Week-3 behavior
```

### The actual finding (not hypothetical)

Week 4 measured **hit-rate@3** (does the correct chunk appear in the top 3
results?) before and after adding hybrid search, split out **by individual
question**, not just one blended number:

| | Before (semantic only) | After (hybrid) |
|---|---|---|
| structure_aware collection | 7/8 | 7/8 |

The aggregate looks unchanged — but underneath, hybrid search **fixed one
question and broke a different one**: it correctly promoted a table row that
semantic search had ranked too low, but it also over-rewarded an exact keyword
match that happened to belong to the *wrong* policy document. That's the real,
important lesson: an aggregate score can hide a trade that a per-question
breakdown reveals.

### Run it yourself

```powershell
.\.venv\Scripts\python.exe scripts/run_evaluation.py
```

Writes `results.md` (the full Week 3+4 write-up, including the hybrid-search
before/after table) and `data/eval_raw_dump.json` (every raw score).

To inspect one specific question's ranking live:

```powershell
.\.venv\Scripts\python.exe scripts/check_rank.py "your question here" --compare
```

`--compare` prints semantic-only and hybrid side by side, so you can see exactly
which chunk moved and why.

---

## Week 5 — Error Analysis: read real traces, find patterns by hand

### What problem this solves

Week 4 fixed *one* known problem. Week 5 asks a harder question: **what
problems don't you know about yet?** The only way to find those is to read a
genuinely random sample of real questions-and-answers and notice, case by
case, what actually happened — before trying to categorize or fix anything.

### The flow

```
1. app/trace_collection.py::build_query_pool()
      -- 43 deliberately varied real questions: known-answer, out-of-corpus,
         rephrased, typo'd, vague, and region-mismatched on purpose

2. scripts/collect_traces.py
      -- runs all 43 through the live app for real, saves every full
         "trace" (question, what was retrieved, the answer, citations)
      -> data/traces/traces_raw.json

3. scripts/sample_traces.py --seed 42 --n 20
      -- draws 20 of the 43 at random (seed recorded, so it's reproducible
         and provably not cherry-picked)
      -> data/traces/trace_worksheet.md   (the 20 traces, blank note field each)

4. A HUMAN reads all 20 and writes one honest sentence per trace,
   BEFORE grouping anything -- this step cannot be automated, by design.
   -> notes.md

5. The 20 sentences get grouped into named "modes" and ranked by
   frequency x severity.
   -> taxonomy.md
```

### The actual finding

Reading the 20 traces surfaced a real bug: **t016** asked a perfectly
answerable question, but the app refused it. Why: the correct chunk *was*
retrieved (rank 2 of 5), but the refusal gate only checked whether the
**top-ranked (rank 1)** chunk's similarity score cleared a threshold — and rank
1's score fell just short. The taxonomy (`taxonomy.md`) named this
**"false refusal near the confidence threshold"** and made a **falsifiable
prediction**: "checking the top 3 ranks instead of just rank 1 will fix this,
dropping the failure rate from 1/20 (5%) to 0/20 (0%)."

### Run it yourself

```powershell
.\.venv\Scripts\python.exe scripts/collect_traces.py     # only if you want to regenerate the 43-question pool
.\.venv\Scripts\python.exe scripts/sample_traces.py --seed 42 --n 20
```

To prove a trace is genuinely self-contained (replayable from its own saved
fields, no hidden state), pick one at random and replay it:

```powershell
.\.venv\Scripts\python.exe scripts/replay_check.py --seed 7
```

This re-runs the exact same call and diffs the original result against the
fresh one — they should match exactly.

**Read `notes.md` and `taxonomy.md` directly** — that's the actual deliverable,
not something a script regenerates for you.

---

## Week 6 — Evals: turn Week 5's finding into an automatic test, then check the prediction

### What problem this solves

Week 5 was a one-time manual read. If the app changes later, nobody will know
whether those same 20 traces still behave the same way — unless someone reads
them all again by hand. Week 6 builds a **repeatable test suite** that checks
the app automatically, plus tests **Week 5's own prediction** for real.

### The flow

```
data/eval/test_cases.json
    -- 21 test cases: the original 8 known-answer + 3 out-of-corpus
       questions from Week 3, PLUS 10 of Week 5's traces converted into
       "this is what SHOULD happen" assertions

app/eval_checks.py   (rule-based, free, zero LLM calls -- run these first)
    -- check_answered_when_expected   : did an answerable question get answered?
    -- check_refused_when_expected    : did an out-of-corpus question get refused?
    -- check_citation_present         : does every answer cite something?
    -- check_citation_resolves        : does every citation point at a real chunk?
    -- check_citation_matches_known_answer : is the cited chunk the RIGHT one?

app/judge.py   (an LLM call -- for the one thing a rule can't check)
    -- judge_faithfulness(): does the answer's wording actually match what
       the cited source text says? A rule can check a citation EXISTS;
       only a judge can check if the answer is actually TRUE to that citation.

scripts/validate_judge.py
    -- BEFORE trusting the judge's verdicts, a human grades ~10 real
       answers by hand (blind to the judge's own answer), then the judge
       grades the same 10 -- agreement rate is reported honestly.
       Result: 11/11 (100%) agreement.

scripts/run_evals.py --gate-mode top1   (the "before" run)
scripts/run_evals.py --gate-mode top3   (the "after" run -- Week 5's fix, implemented)
    -- scores all 21 cases, broken down BY PROBLEM TYPE (not one blended number)
```

### The actual finding — Week 5's prediction was WRONG, and that's reported honestly

The fix predicted in Week 5 (check top-3 ranks, not just rank 1) was
**implemented exactly as described** in `app/refusal.py` (`gate_mode="top3"`)
— and then measured. Result:

| Problem type | Before | After |
|---|---|---|
| false_refusal_near_threshold | 0/1 | 0/1 |

**No change.** Digging into why: t016's top-3 candidate scores were
**0.716, 0.688, 0.682** — every single one below the 0.72 threshold. The
original prediction assumed the correct chunk was a *good* match sitting at
rank 2 or 3; in reality, for this specific question, the *entire* neighborhood
of candidates scored low. Checking more ranks doesn't help when the real
problem is that none of them clear the bar.

This is exactly the point of writing a falsifiable prediction: it can be
**tested and shown wrong**, which teaches you something a vague guess never
would. (A real fix would need a different mechanism — e.g. lowering the
threshold, or relying only on the citation-check gate — not attempted here,
since that would be a second, separate change needing its own before/after.)

**Bonus finding**: running the *full* 21-case set (not just Week 5's smaller
sample) turned up 2 more cases of the same "citation drift" pattern Week 5 had
found — meaning the real rate was 24%, not the 15% the smaller sample suggested.

### Run it yourself

```powershell
.\.venv\Scripts\python.exe scripts/run_evals.py --gate-mode top1
.\.venv\Scripts\python.exe scripts/run_evals.py --gate-mode top3
```

Each is genuinely **one command** per rubric requirement. Read `eval_results.md`
for the full before/after table and the honest write-up of why the prediction
failed.

To redo the human-judge validation yourself (interactive — it asks you to type
P/F for each of ~11 traces):

```powershell
.\.venv\Scripts\python.exe scripts/validate_judge.py
```

---

## Week 7 — Agent Loops: build one, then prove a fixed sequence beats it

### What problem this solves

So far, every "step" the app takes is fixed in advance (search once, generate
once). Some real questions need a **variable number of steps depending on what
you find along the way** — e.g. a question that spans 3 leave categories needs
3 searches, and if one of those chunks says "as defined in Section X", you need
a 4th lookup you couldn't have predicted beforehand. Week 7 builds a genuine
**agent loop** for that case — and, just as importantly, tests whether it's
actually worth using compared to a simpler fixed sequence.

### What an "agent" means here, concretely

```
app/agent.py  (hand-built, ~150 lines, no framework)

  loop (up to 6 steps, up to 45 seconds, up to $0.05 estimated):
      1. ask the LLM: "given what you know so far, what's your next move?"
      2. the LLM replies with a Thought + one tool call
      3. actually run that tool, get a real result (an "Observation")
      4. feed the Observation back in, go to step 1
      5. stop when the LLM calls finish(), or a limit is hit

  tools available (app/agent_tools.py):
      search_policy(query, region)  -- the same hybrid search from Week 4
      get_chunk(chunk_id)           -- fetch one exact chunk by id (for
                                        chasing a cross-reference)
      finish(summary, citations)    -- the agent's own "I'm done" signal
```

Every single step — the model's reasoning, which tool it picked, and what that
tool actually returned — is logged. That's what makes it debuggable instead of
"magic."

### The fixed-sequence competitor

`app/fixed_workflow.py` does the *same task*, but with no LLM deciding what to
do next: it keyword-matches the question into categories (sick leave / carry-
over / parental leave), runs exactly one search per category, and never chases
a cross-reference — a plain, predictable sequence.

### The race — 5 real scenarios, both approaches, 3 metrics

```powershell
.\.venv\Scripts\python.exe scripts/race_agent.py
```

| Metric | Agent | Fixed workflow |
|---|---|---|
| Speed (avg) | 8.3s | 2.6s — **~3.2x faster** |
| Cost (avg) | $0.00062 | $0.00017 — **~3.6x cheaper** |
| Completed without crashing | 5/5 | 5/5 |

**The fixed sequence won on 2 of 3 metrics, decisively.** The agent's one real
advantage — following a cross-reference the fixed sequence structurally can't
reach — only mattered on 2 of the 5 scenarios, and even there the fixed
sequence didn't hallucinate: it either got lucky, or it explicitly said "this
detail isn't in what I found" rather than guessing.

We also **proved the safety limits actually work**, not just exist in code: we
deliberately forced the step limit down to 1 and confirmed the loop stopped
cleanly (`stop_reason="max_steps_exceeded"`, no answer fabricated) instead of
continuing forever.

**The recommendation** (see `race_results.md`): ship the fixed sequence as the
default, and only fall back to the agent when the fixed sequence's own answer
admits a gap — a cheap, honest signal for exactly when the more expensive path
is actually needed.

### Run it yourself

```powershell
.\.venv\Scripts\python.exe scripts/race_agent.py
```

Writes `race_results.md` (the comparison table + full step-by-step log for one
run) and `data/agent/race_raw.json` (every raw number).

---

## The one-page map of what to read vs. what to run

| Week | Read this for the explanation | Run this to reproduce it |
|---|---|---|
| 4 | `results.md` (hybrid search section) | `scripts/run_evaluation.py`, `scripts/check_rank.py` |
| 5 | `notes.md`, `taxonomy.md` | `scripts/sample_traces.py`, `scripts/replay_check.py` |
| 6 | `eval_results.md` | `scripts/run_evals.py --gate-mode top1/top3` |
| 7 | `race_results.md` | `scripts/race_agent.py` |

Every one of these numbers is real — generated by actually running the code
against the live app, not written by hand. If you re-run any script, the
generated `.md` file will be overwritten with a fresh (and, if anything about
the app changed, possibly different) result.
