from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str
    region: str | None = None
    strategy: str = "structure_aware"
    retrieval_mode: str = "semantic"  # "semantic" (Week 3 default) | "hybrid" (Week 4, BM25+RRF)


class Citation(BaseModel):
    chunk_id: str
    policy_id: str
    section: str | None


class AskResponse(BaseModel):
    refused: bool
    reason: str | None = None
    answer: str | None = None
    citations: list[Citation] = []
    top_score: float | None = None
