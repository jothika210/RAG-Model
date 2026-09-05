from fastapi import APIRouter

from app.models import AskRequest, AskResponse, Citation
from app.refusal import answer_question

router = APIRouter()


@router.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    result = answer_question(
        req.question,
        strategy=req.strategy,
        region=req.region,
        retrieval_mode=req.retrieval_mode,
    )
    return AskResponse(
        refused=result.refused,
        reason=result.reason,
        answer=result.answer,
        citations=[Citation(chunk_id=c.chunk_id, policy_id=c.policy_id, section=c.section) for c in result.citations],
        top_score=result.top_score,
    )
