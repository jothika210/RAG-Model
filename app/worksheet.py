"""Renders the Week 5 trace-reading worksheet and the blank analysis
template. Pure formatting logic -- no judgment, grouping, or ranking
happens here; that is the human reviewer's job.
"""


def _fmt_hits(ranked_hits: list[dict]) -> str:
    if not ranked_hits:
        return "_(no chunks retrieved)_"
    lines = []
    for i, h in enumerate(ranked_hits, 1):
        lines.append(
            f"{i}. `{h['chunk_id']}` — policy={h['policy_id']} section={h['section']} "
            f"region={h['region']} score={h['score']}"
        )
    return "\n".join(lines)


def _fmt_citations(citations: list[dict]) -> str:
    if not citations:
        return "_(none)_"
    return ", ".join(f"`{c['chunk_id']}`" for c in citations)


def render_trace_block(trace: dict) -> str:
    lines = [f"### {trace['trace_id']}", "", f"**Question asked:** {trace['question']}", ""]

    meta = []
    if trace.get("region"):
        meta.append(f"region filter: `{trace['region']}`")
    meta.append(f"strategy: `{trace['strategy']}`")
    meta.append(f"retrieval_mode: `{trace['retrieval_mode']}`")
    lines.append(f"_{' · '.join(meta)}_")
    lines.append("")

    lines.append("**Fetched:**")
    lines.append("")
    lines.append(_fmt_hits(trace["ranked_hits"]))
    lines.append("")

    if trace["refused"]:
        lines.append(f"**Result:** REFUSED (reason: `{trace['reason']}`" + (f", top_score={trace['top_score']:.4f})" if trace.get("top_score") is not None else ")"))
        if trace.get("raw_llm_output"):
            lines.append("")
            lines.append(f"**Model output:** {trace['raw_llm_output']}")
    else:
        lines.append("**Answer:**")
        lines.append("")
        lines.append(trace["answer"] or "_(empty)_")
        lines.append("")
        lines.append(f"**Citations:** {_fmt_citations(trace['citations'])}")

    lines.append("")
    lines.append("**Note:** _(write one honest sentence about what, if anything, went wrong in this trace -- before reading ahead or grouping)_")
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def render_worksheet(traces: list[dict], seed: int) -> str:
    lines = [
        "# Trace Worksheet — Week 5 Error Analysis (HR Policy)",
        "",
        f"{len(traces)} traces, randomly sampled with seed `{seed}` from a pool of diverse real queries "
        "run through the live pipeline. Read every trace in order below and write one honest note per "
        "trace about what, if anything, went wrong — **before** grouping or ranking anything. Full raw "
        "data (including which trace_ids were drawn) is in `data/traces/traces_raw.json` and "
        "`data/traces/sampled_trace_ids.json`.",
        "",
        "---",
        "",
    ]
    for trace in traces:
        lines.append(render_trace_block(trace))
    return "\n".join(lines)


def render_analysis_template() -> str:
    return """# Error Analysis — Named Problems, Ranked (Week 5)

Fill this in only after every trace in `trace_worksheet.md` has an honest note.

## 1. Open coding notes

Your per-trace notes live in `trace_worksheet.md`. Do not summarize them here yet — read all of them first.

## 2. Named problem groups

Group your notes into a handful of named problem types. Give each a name a stranger
could understand without more context.

| Group name | Description | Trace IDs in this group |
|---|---|---|
| | | |
| | | |
| | | |

## 3. Ranking (frequency × severity)

Severity: 1 = minor/cosmetic, 2 = wrong but harmless, 3 = actively misleading or harmful.

| Rank | Group | Frequency (count) | Severity (1-3) | Frequency × Severity |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

## 4. Chosen fix target

**Which group are you fixing next, and why?**

(one paragraph)

**Prediction — what do you expect to happen after the fix?**

(one paragraph, written before making the fix)
"""
