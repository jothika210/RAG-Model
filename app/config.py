import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

ADDENDA_DIR = BASE_DIR / "data" / "addenda"
QUESTIONS_PATH = BASE_DIR / "data" / "questions" / "known_answer_questions.json"
QDRANT_PATH = BASE_DIR / "data" / "qdrant_data"
RESULTS_PATH = BASE_DIR / "results.md"
RAW_DUMP_PATH = BASE_DIR / "data" / "eval_raw_dump.json"

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

COLLECTIONS = {
    "naive": "hr_addenda_naive",
    "structure_aware": "hr_addenda_structured",
}

TOP_K = 5

# Calibrated against real scores from the 8 answerable vs 3 out-of-corpus
# questions (see results.md "Refusal calibration" section). Cosine top-1
# score ranges overlap substantially between answerable (0.756-0.900) and
# out-of-corpus (0.708-0.760) questions on this embedding model, so this
# threshold only catches clear non-matches -- the real enforcement is the
# post-hoc citation-resolution gate in app/refusal.py, which is what the
# assignment's "forced, not suggested" refusal requirement actually needs.
SIMILARITY_THRESHOLD = 0.72

NAIVE_CHUNK_SIZE = 800
NAIVE_CHUNK_OVERLAP = 150

# Week 4 -- hybrid search (BM25 + semantic, RRF fusion)
RRF_K = 60  # standard RRF damping constant from the literature
HIT_RATE_K = 3  # the "@3" in hit-rate@3, the Week 4 metric cutoff -- kept
# distinct from TOP_K=5 above, which stays the Week 3 / live-app default
# retrieval depth. Week 3's already-shipped results.md numbers key off
# TOP_K, so it is never repurposed.
HYBRID_SEMANTIC_POOL = 20  # widen the semantic candidate pool before RRF
# fusion so there's enough overlap between the two ranked lists to reorder
# meaningfully -- fusing only the top-3 from each side would make RRF close
# to a no-op for anything not already in both top-3s.
