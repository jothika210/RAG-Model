"""Week 6 -- rule-based eval checks. These are cheap, deterministic, and
run before any LLM-as-judge call, per the assignment's own guidance:
"Simple checks a rule can do ... do these first, they're free."

No httpx/OpenRouter imports on purpose -- these checks never make a
network call, which is exactly what makes them free and fast.
"""

from dataclasses import dataclass

from app.refusal import AnswerResult


@dataclass
class CheckResult:
    name: str
    passed: bool
    reason: str


def check_answered_when_expected(result: AnswerResult, case: dict) -> CheckResult | None:
    """Known-answerable questions must not refuse. Returns None (not
    applicable) if the case doesn't expect an answer."""
    if case.get("expected_refused") is not False:
        return None
    if result.refused:
        return CheckResult(
            "answered_when_expected",
            passed=False,
            reason=f"expected an answer but got refused (reason={result.reason}, top_score={result.top_score})",
        )
    return CheckResult("answered_when_expected", passed=True, reason="answered as expected")


def check_refused_when_expected(result: AnswerResult, case: dict) -> CheckResult | None:
    """Known out-of-corpus / vague / region-mismatched questions must
    refuse. Returns None if the case doesn't expect a refusal."""
    if case.get("expected_refused") is not True:
        return None
    if not result.refused:
        return CheckResult(
            "refused_when_expected",
            passed=False,
            reason=f"expected a refusal but got an answer: {result.answer!r}",
        )
    return CheckResult("refused_when_expected", passed=True, reason="refused as expected")


def check_citation_present(result: AnswerResult, case: dict) -> CheckResult | None:
    """Every non-refused answer must carry at least one citation."""
    if result.refused:
        return None
    if not result.citations:
        return CheckResult("citation_present", passed=False, reason="answered with zero citations")
    return CheckResult("citation_present", passed=True, reason=f"{len(result.citations)} citation(s) present")


def check_citation_resolves(result: AnswerResult, case: dict) -> CheckResult | None:
    """Every cited chunk_id must exist among the retrieved hits. This is
    already enforced inside app/refusal.py's Gate 2, but testing it here
    explicitly guards against a future regression in that gate itself --
    if Gate 2 is ever weakened, this check catches it independently."""
    if result.refused:
        return None
    retrieved_ids = {h.chunk_id for h in result.hits}
    unresolved = [c.chunk_id for c in result.citations if c.chunk_id not in retrieved_ids]
    if unresolved:
        return CheckResult(
            "citation_resolves",
            passed=False,
            reason=f"citation(s) not found among retrieved hits: {unresolved}",
        )
    return CheckResult("citation_resolves", passed=True, reason="all citations resolve to retrieved chunks")


def check_citation_matches_known_answer(result: AnswerResult, case: dict) -> CheckResult | None:
    """For cases with a known-correct (policy_id, section), at least one
    citation must match it. Regression-guards the 'citation drift' mode
    from silently getting worse (i.e. citing something that isn't even
    topically related, not just a lower-ranked chunk)."""
    expected_policy = case.get("expected_policy_id")
    expected_section = case.get("expected_section")
    if result.refused or expected_policy is None:
        return None
    match = any(c.policy_id == expected_policy and c.section == expected_section for c in result.citations)
    if not match:
        cited = [(c.policy_id, c.section) for c in result.citations]
        return CheckResult(
            "citation_matches_known_answer",
            passed=False,
            reason=f"expected a citation to {expected_policy} sec.{expected_section}, got {cited}",
        )
    return CheckResult("citation_matches_known_answer", passed=True, reason="citation matches known-correct source")


ALL_CHECKS = [
    check_answered_when_expected,
    check_refused_when_expected,
    check_citation_present,
    check_citation_resolves,
    check_citation_matches_known_answer,
]


def run_rule_checks(result: AnswerResult, case: dict) -> list[CheckResult]:
    """Runs every applicable rule check against one (result, case) pair,
    skipping checks that return None (not applicable to this case)."""
    checks = []
    for check_fn in ALL_CHECKS:
        outcome = check_fn(result, case)
        if outcome is not None:
            checks.append(outcome)
    return checks
