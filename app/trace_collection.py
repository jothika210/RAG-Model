"""Week 5 -- trace collection for error analysis.

Builds a diverse pool of real questions, runs each one through the actual
live pipeline (app/refusal.py::answer_question(), unchanged), and packages
a complete "trace" per the assignment's definition: a full record of one
request -- the question, what the app fetched, and what it answered --
complete enough to replay later.

This module only COLLECTS traces. Reading them, writing honest notes, and
grouping/ranking is the human's job (see data/traces/trace_worksheet.md
and data/traces/analysis_template.md) -- that is the actual graded skill
this week and is deliberately not automated here.
"""

from dataclasses import asdict, dataclass, field

from app.refusal import answer_question


@dataclass
class Trace:
    trace_id: str
    question: str
    category: str  # internal tag for pool diversity bookkeeping -- NOT shown on the worksheet
    region: str | None
    strategy: str
    retrieval_mode: str
    ranked_hits: list[dict] = field(default_factory=list)
    refused: bool = False
    reason: str | None = None
    raw_llm_output: str | None = None
    answer: str | None = None
    citations: list[dict] = field(default_factory=list)
    top_score: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def build_query_pool() -> list[dict]:
    """Returns ~45 diverse query specs: {question, category, region, strategy,
    retrieval_mode}. Categories exist for our own bookkeeping (to confirm the
    pool is genuinely diverse before sampling) -- they are never shown to the
    person reading the worksheet, so judgment on each trace stays honest
    rather than pattern-matched to a label.
    """
    pool: list[dict] = []

    def add(question, category, region=None, strategy="structure_aware", retrieval_mode="semantic"):
        pool.append(
            {
                "question": question,
                "category": category,
                "region": region,
                "strategy": strategy,
                "retrieval_mode": retrieval_mode,
            }
        )

    # -- known_answer: the 8 Week 3 questions, run under a mix of strategy/mode
    known = [
        ("What is the carry-over cap for a probationary employee under HR-207 section 4.2?", "APAC"),
        ("Under HR-207, what is the carry-over cap for a full-time confirmed employee in India?", "APAC"),
        ("How many days of company-paid sick leave is an EMEA employee entitled to per calendar year under HR-203?", "EMEA"),
        ("Under HR-203, what certification is required for a sick absence of 4 to 7 days?", "EMEA"),
        ("How many weeks of paid parental leave is a full-time secondary caregiver entitled to under HR-205?", "AMER"),
        ("Under HR-211, what is the carry-over cap for a full-time confirmed employee in Brazil, and why can't it be reduced?", "AMER"),
        ("Under HR-209, if a remote employee's scheduled annual leave day coincides with a public holiday in their home country, what happens to that leave day?", "EMEA"),
        ("Under HR-201, what is the special carry-over exception for full-time confirmed employees based in Singapore, and how many days can they carry over?", "APAC"),
    ]
    for i, (q, region) in enumerate(known):
        strategy = "naive" if i % 3 == 0 else "structure_aware"
        mode = "hybrid" if i % 2 == 0 else "semantic"
        add(q, "known_answer", region=region, strategy=strategy, retrieval_mode=mode)

    # -- out_of_corpus: the 3 Week 3 OOC questions, plus a couple more genuinely uncovered topics
    ooc = [
        "What is the company's sabbatical leave policy after 5 years of continuous service?",
        "Can an employee take annual leave during their notice period after resignation?",
        "What is the bereavement leave entitlement for APAC employees?",
        "What is the policy on unlimited PTO for senior management?",
        "Does the company offer a four-day work week option?",
    ]
    for q in ooc:
        add(q, "out_of_corpus", strategy="structure_aware", retrieval_mode="hybrid")

    # -- rephrase: same underlying facts, different wording/register
    rephrases = [
        ("If I'm on probation and get confirmed halfway through the year, how many carry-over days do I keep under HR-207?", "APAC"),
        ("I'm based in India and I'm full-time and confirmed -- what's my leave carry-over limit per HR-207?", "APAC"),
        ("How much sick pay from the company do EMEA staff get each year, per HR-203?", "EMEA"),
        ("What paperwork do I need for a sick day that's 5 days long under HR-203?", "EMEA"),
        ("As the non-primary parent, how much paid leave do I get for parental leave under HR-205?", "AMER"),
        ("Brazil full-timers confirmed in their role -- what's their carry-over allowance under HR-211, and is there a legal reason it's fixed?", "AMER"),
        ("If my scheduled leave lands on a public holiday back home while I'm working remotely, do I lose that day under HR-209?", "EMEA"),
        ("Singapore employees who are confirmed full-time -- how many carry-over days do they specifically get under HR-201?", "APAC"),
    ]
    for q, region in rephrases:
        add(q, "rephrase", region=region, strategy="structure_aware", retrieval_mode="hybrid")

    # -- ambiguous / multi-part: questions that bundle two asks or are underspecified
    ambiguous = [
        "What's the leave policy?",
        "How much leave do I get and when does it reset?",
        "What happens to my leave if I move from probation to confirmed AND relocate from Singapore to Japan mid-year?",
        "Tell me everything about HR-207.",
        "What's the difference between HR-201 and HR-207 on carry-over?",
        "Can you compare sick leave and parental leave entitlements for EMEA vs AMER?",
        "What is 'continuous service' and how does it affect all my leave entitlements?",
    ]
    for q in ambiguous:
        add(q, "ambiguous", strategy="structure_aware", retrieval_mode="hybrid")

    # -- typo / informal phrasing
    typos = [
        "wats the carryover cap 4 probationary employee hr207 4.2",
        "sick leave days emea plz under hr203",
        "secondary caregiver parental leave weeks HR205???",
        "carryover cap brasil hr 211 full time",
        "hows the holiday overlap thing work for remote ppl hr209",
        "singapore carryover days pls hr201",
    ]
    for q in typos:
        add(q, "typo_informal", strategy="structure_aware", retrieval_mode="semantic")

    # -- region_mismatch: asking about a policy under a region filter that doesn't apply to it
    mismatches = [
        ("What is the carry-over cap for a full-time confirmed employee in India under HR-207?", "AMER"),
        ("How many weeks of parental leave does a secondary caregiver get under HR-205?", "EMEA"),
        ("What is the sick leave entitlement under HR-203?", "APAC"),
    ]
    for q, wrong_region in mismatches:
        add(q, "region_mismatch", region=wrong_region, strategy="structure_aware", retrieval_mode="semantic")

    # -- malformed / vague
    malformed = [
        "leave",
        "?",
        "hr policy question please help",
        "what about the thing with the days",
        "policy",
        "help me understand my benefits",
    ]
    for q in malformed:
        add(q, "malformed", strategy="structure_aware", retrieval_mode="semantic")

    return pool


def collect_trace(index: int, spec: dict) -> Trace:
    """Runs one query spec through the real, unmodified live pipeline and
    packages a complete trace."""
    result = answer_question(
        spec["question"],
        strategy=spec["strategy"],
        region=spec.get("region"),
        retrieval_mode=spec["retrieval_mode"],
    )

    ranked_hits = [
        {
            "chunk_id": h.chunk_id,
            "policy_id": h.policy_id,
            "section": h.section,
            "region": h.region,
            "score": round(h.score, 4),
        }
        for h in result.hits
    ]

    return Trace(
        trace_id=f"t{index:03d}",
        question=spec["question"],
        category=spec["category"],
        region=spec.get("region"),
        strategy=spec["strategy"],
        retrieval_mode=spec["retrieval_mode"],
        ranked_hits=ranked_hits,
        refused=result.refused,
        reason=result.reason,
        raw_llm_output=result.raw_llm_output,
        answer=result.answer,
        citations=[c.model_dump() for c in result.citations],
        top_score=result.top_score,
    )
