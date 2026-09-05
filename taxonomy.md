# Taxonomy — Week 5 Error Analysis (HR Policy, Track C)

20 traces, seed `42`. Full detail: `notes.md`, `data/traces/trace_worksheet.md`.

| Mode | Count | % of 20 | Severity | Example trace_id |
|---|---|---|---|---|
| False refusal near the confidence threshold | 1 | 5% | Annoyance — no wrong fact stated, employee just has to re-ask | t016 |
| Correct refusal — region filter excludes the real document | 2 | 10% | Annoyance — refusal is correct behavior, not a defect | t034 |
| Correct refusal — vague or malformed input | 4 | 20% | Annoyance — refusal is correct behavior, not a defect | t040 |
| Grounded answer, citation resolves to a supporting chunk | 13 | 65% | None — not a failure mode | t001 |

No mode observed in this sample rises to legal-exposure severity (stating a wrong or superseded policy fact as if true) — every answered trace's citation resolved to a chunk that actually contains the stated figure.
