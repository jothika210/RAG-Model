# HR Policy RAG — Week 3 Task Set C

A mini "ask my documents" app over 6 synthetic HR policy addenda, built to satisfy
[W3-Task-Set-C.md](W3-Task-Set-C.md): two chunking strategies measured against the
same 8 known-answer questions, a metadata filter demo, grounded citation generation,
and forced refusal on out-of-corpus questions.

See [results.md](results.md) for the graded deliverable.

## Setup

```
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv\Scripts\activate on cmd/PowerShell
pip install -r requirements.txt
cp .env.example .env            # then fill in OPENROUTER_API_KEY
```

## Run

```
python scripts/ingest.py --recreate     # build both Qdrant collections
python scripts/run_evaluation.py        # writes results.md + data/eval_raw_dump.json
uvicorn app.main:app --reload           # UI at http://127.0.0.1:8000
```

`/` — ask a question, get a cited answer or a refusal.
`/eval.html` — trigger or view the full evaluation run.

## Tests

```
pytest tests/
```

## Design notes

- Embeddings are local (`sentence-transformers`, `BAAI/bge-small-en-v1.5`) so the
  exact same model is used for both chunking-strategy collections — only the
  chunker varies between the two indexes being compared.
- Generation only (citation answers + refusal) goes through OpenRouter.
- Qdrant runs in embedded/local mode (`data/qdrant_data/`), one process, two
  collections: `hr_addenda_naive` and `hr_addenda_structured`.
- Refusal is enforced by two independent code-level gates in `app/refusal.py`,
  not a soft prompt instruction — see `results.md` §6 for the calibration data
  that motivated this.
