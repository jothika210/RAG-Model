# Weeks 4–7 — What Was Done (Mentor Walkthrough)

One HR-policy RAG app, extended over four weeks. Each week builds directly on
the one before it — same codebase, same corpus (6 synthetic HR addenda), no
restarts. This doc is the one place that ties the whole arc together.

```
Week 3 (baseline)   Build the RAG pipeline: retrieval + citation + refusal
Week 4              Add ONE retrieval improvement, measure it honestly
Week 5              Read 20 real traces BY HAND, name the failure patterns
Week 6              Automate Week 5's checks, test Week 5's own prediction
Week 7              Build an agent, prove a simpler approach usually wins
```

---

## Week 4 — Hybrid Search

**The ask:** make one targeted improvement to retrieval and prove it helped
with a before/after number — not a feeling.

**What was done:**
- Semantic (meaning-based) search alone has a blind spot: it can miss an
  exact keyword or code if the wording around it isn't a strong semantic
  match. Added a second search method — **BM25 keyword search** — and
  combined it with the existing semantic search using **Reciprocal Rank
  Fusion (RRF)**: each method produces its own ranked list, and a chunk's
  final score is `1/(rank + 60)` summed across every list it appears in.
- Measured **hit-rate@3** (is the correct chunk in the top 3 results?)
  before and after, broken down **per individual question**, not just one
  blended number.

**Files touched:**
- `app/hybrid_retrieval.py` — new; `bm25_search()`, `hybrid_search()`
- `app/refusal.py` — `answer_question()` gets an optional `retrieval_mode`
  parameter; the old default path is untouched
- `scripts/run_evaluation.py` — runs it, writes `results.md`
- `scripts/check_rank.py` — inspect one question's ranking live, `--compare`
  flag shows semantic vs hybrid side by side

**The honest result:** the aggregate score stayed 7/8 both before and after
— but the per-question breakdown showed hybrid search **fixed one question
and broke a different one**. That's the real point being demonstrated: an
aggregate number can hide a trade you'd otherwise miss.

---

## Week 5 — Error Analysis

**The ask:** find problems nobody knew to look for. Explicitly **not**
automatable — a human has to read real output and notice things.

**What was done, in order:**
1. Generated 43 deliberately varied real questions — known-answer,
   out-of-corpus, typo'd, vague, and some with the region filter set
   incorrectly on purpose.
2. Ran all 43 through the live app for real, saved every full "trace"
   (question, what was retrieved, the answer, the citations).
3. Randomly sampled 20 of the 43 (seed recorded, so it's provably not
   cherry-picked).
4. **A human read all 20 and wrote one honest sentence per trace, before
   grouping anything.**
5. Grouped the 20 sentences into named "failure modes," ranked by
   frequency × severity.

**Files touched:**
- `app/trace_collection.py` — builds the 43-question pool
- `scripts/collect_traces.py` — runs all 43, saves `data/traces/traces_raw.json`
- `scripts/sample_traces.py` — draws 20 at random, writes the worksheet
- `notes.md` — the 20 human-written sentences (the actual deliverable)
- `taxonomy.md` — 5 named failure modes with count/%/severity/example
- `app/replay.py`, `scripts/replay_check.py` — proves a saved trace is
  self-contained: re-runs it from its own saved fields and checks the
  output matches exactly

**The honest result:** found a real bug (trace `t016`) — an answerable
question got refused. Why: the refusal check only looked at the **top-ranked**
chunk's confidence score, and that one happened to score just under the
cutoff even though the correct chunk was retrieved at rank 2. Named this
mode and wrote a specific, falsifiable, numeric prediction for how to fix
it — dated and committed to git before any fix was attempted.

---

## Week 6 — Evals

**The ask:** turn Week 5's one-time manual read into an automatic,
repeatable test — and actually test Week 5's prediction, not just assume it
worked.

**What was done — two layers of checking:**
1. **Rule-based checks** (free, instant, zero AI calls): did it answer when
   it should have? Refuse when it should have? Does every citation point to
   something real?
2. **LLM-as-judge** for the one thing a rule can't check: does the answer's
   wording actually match what the cited source text says? — but only
   after validating the judge against real human grading first, so its
   verdicts can be trusted.

**Files touched:**
- `data/eval/test_cases.json` — 21 cases: Week 3's 8+3 baseline questions +
  10 of Week 5's traces converted into "this is what should happen"
  assertions
- `app/eval_checks.py` — 5 rule-based checks, confirmed zero LLM/network
  imports
- `app/judge.py` — the faithfulness judge, one dedicated OpenRouter call
- `scripts/validate_judge.py` — interactive: a human grades ~11 real
  answers blind, then the judge grades the same 11, agreement is reported
  (result: **11/11, 100% agreement**)
- `scripts/run_evals.py` — the one-command runner, `--gate-mode top1`
  (before) or `--gate-mode top3` (after)
- `eval_results.md` — the write-up, scored by problem type

**The honest result:** Week 5's predicted fix (check the top 3 ranks, not
just rank 1) was implemented exactly as described in `app/refusal.py` — and
**it did not work**. Scores were identical before and after. Digging into
why: the correct chunk's score wasn't just low at rank 1, it was low at
*every* rank for that question — checking more ranks can't help when nothing
clears the confidence bar. This is reported as a **failed, informative
prediction**, not hidden or reframed as a success. A genuine bonus finding
also surfaced: running the full 21-case set (not just Week 5's smaller
sample) found 2 more instances of the same failure pattern Week 5 had named,
showing the real rate was higher than the small sample suggested.

---

## Week 7 — Agent Loops

**The ask:** build a real multi-step agent by hand (no framework), then race
it against a plain fixed sequence on speed, cost, and reliability — and be
honest about which one actually wins.

**Why this task needed an agent, in principle:** a question spanning several
leave categories, where one category's answer sometimes references a
definition living elsewhere ("as defined in Section X"). The number of
lookups needed isn't fixed in advance — it depends on what the first search
turns up.

**What was done:**
- Built `app/agent.py` — a ~150-line hand-built loop: think → pick a tool →
  run it → look at the result → repeat, with 3 safety limits (max steps, max
  time, max estimated cost) and every single step logged.
- Built `app/fixed_workflow.py` — the same task as a plain hard-coded
  sequence: no LLM decides what to do next, and it never chases a
  cross-reference (a known, accepted limitation).
- Built `scripts/race_agent.py` — runs both across 5 real multi-category
  scenarios and writes `race_results.md`.

**Files touched:**
- `app/agent_tools.py` — the 3 shared tools: `search_policy`, `get_chunk`
  (fetch one exact chunk by id), `finish`
- `app/agent.py` — the loop itself
- `app/fixed_workflow.py` — the fixed-sequence competitor
- `data/agent/scenarios.json` — 5 real test scenarios
- `scripts/race_agent.py` — runs the race, writes the report

**The honest result:** the fixed sequence won clearly on **speed (~3x
faster)** and **cost (~4x cheaper)**. On reliability it initially looked
tied — but re-running the race multiple times as a deliberate stress test
surfaced a real problem: the agent's underlying LLM does **not** always
follow the exact tool-call format it's told to use. Across repeated runs,
this occasionally burned all of the agent's step budget on malformed calls,
while the fixed sequence never has this failure mode at all, since it never
depends on an LLM emitting a specific, parseable string. Several distinct
format-drift patterns were found and patched into the parser as they
appeared (`app/agent.py::_parse_action`), and the finding itself — that a
hand-built agent's reliability is genuinely fragile — is reported directly
rather than smoothed over.

**The recommendation:** ship the fixed sequence as the default. Only
escalate to the agent when the fixed sequence's own answer admits a gap
(e.g. "not explicitly stated in the search results") — a cheap, honest
signal for exactly the cases where the extra capability is worth the extra
cost and risk.

---

## The one sentence that connects all four weeks

Week 4 fixes one thing and measures it honestly → Week 5 finds new problems
by reading real output, no automation allowed → Week 6 turns that reading
process into a repeatable test and checks whether Week 5's fix actually
worked (it didn't, and that's reported truthfully) → Week 7 builds something
more powerful and proves, with real numbers, that the simpler thing usually
deserves to ship anyway.

---

## How to reproduce every result yourself

```powershell
cd D:\RAGmodule
.venv\Scripts\Activate.ps1

# Week 4
.\.venv\Scripts\python.exe scripts/run_evaluation.py
.\.venv\Scripts\python.exe scripts/check_rank.py "your question" --compare

# Week 5
.\.venv\Scripts\python.exe scripts/sample_traces.py --seed 42 --n 20
.\.venv\Scripts\python.exe scripts/replay_check.py --seed 7

# Week 6
.\.venv\Scripts\python.exe scripts/run_evals.py --gate-mode top1
.\.venv\Scripts\python.exe scripts/run_evals.py --gate-mode top3
.\.venv\Scripts\python.exe scripts/validate_judge.py

# Week 7
.\.venv\Scripts\python.exe scripts/race_agent.py

# Regression check (should show 8 passed)
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

Only one process can hold the Qdrant database at a time — close any running
`uvicorn` server before running these.
