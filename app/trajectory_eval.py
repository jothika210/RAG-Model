"""Week 8 -- a small, standalone checker for the outcome-vs-trajectory gap:
did the agent's cited evidence actually come from a chunk it fetched in
full (via get_chunk), or only from a truncated search_policy snippet it
never verified? Mirrors the same "resolve every citation against real
evidence, flag what doesn't resolve" pattern already proven in
app/refusal.py::_resolve_citations() and the rule-based CheckResult style
in app/eval_checks.py -- applied here to an agent's multi-step trajectory
instead of a single-shot generation context.
"""

from dataclasses import dataclass

from app.agent import AgentRun


@dataclass
class CitationVerification:
    chunk_id: str
    verified: bool
    reason: str


@dataclass
class TrajectoryReport:
    scenario_id: str
    citations: list[CitationVerification]
    all_verified: bool
    unverified_count: int


def _fetched_chunk_ids(run: AgentRun) -> set[str]:
    return {
        step.action_input.get("chunk_id")
        for step in run.steps
        if step.action == "get_chunk" and step.action_input.get("chunk_id")
    }


def evaluate_run(run: AgentRun) -> TrajectoryReport:
    """A citation is "verified" only if some step in this same run called
    get_chunk on that exact chunk_id -- i.e. the agent actually read the
    chunk's full text, not just a truncated search_policy snippet.
    """
    fetched = _fetched_chunk_ids(run)
    verifications = []
    for chunk_id in run.citations:
        if chunk_id in fetched:
            step_number = next(
                step.step_number
                for step in run.steps
                if step.action == "get_chunk" and step.action_input.get("chunk_id") == chunk_id
            )
            verifications.append(
                CitationVerification(chunk_id, True, f"fetched via get_chunk at step {step_number}")
            )
        else:
            verifications.append(
                CitationVerification(chunk_id, False, "snippet-only: never fetched via get_chunk during this run")
            )
    unverified_count = sum(1 for v in verifications if not v.verified)
    return TrajectoryReport(
        scenario_id=run.scenario_id,
        citations=verifications,
        all_verified=unverified_count == 0,
        unverified_count=unverified_count,
    )
