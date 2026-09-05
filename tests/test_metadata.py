import pytest

from app.chunking.naive import NaiveChunker
from app.chunking.structure_aware import StructureAwareChunker
from app.loader import load_addenda

CHUNKERS = [NaiveChunker(), StructureAwareChunker()]


@pytest.mark.parametrize("chunker", CHUNKERS, ids=lambda c: c.name)
def test_every_chunk_has_required_metadata(chunker):
    docs = load_addenda()
    assert len(docs) == 6, "expected exactly 6 addenda documents"

    for doc in docs:
        chunks = chunker.chunk(doc)
        assert chunks, f"{doc.source_file} produced zero chunks under {chunker.name}"
        for c in chunks:
            assert c.source_file, "chunk missing source_file"
            assert c.policy_id, "chunk missing policy_id"
            assert c.region, "chunk missing region"
            assert c.effective_date, "chunk missing effective_date"
