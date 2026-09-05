from app.chunking.base import RawDoc
from app.chunking.structure_aware import StructureAwareChunker

SAMPLE_DOC = """# HR-999 — Sample Policy

Region: TEST
Effective Date: 2026-01-01
Policy ID: HR-999

## 1. Purpose

Intro text explaining the policy exists.

### 4.2 Carry-Over Cap

A probationary employee who is confirmed to permanent status partway through
the leave year is subject to a carry-over cap of 2 days for that transition
year only, regardless of sub-region.

### 4.3 Next Section

Some other clause text here.
"""


def _doc() -> RawDoc:
    return RawDoc(
        text=SAMPLE_DOC,
        source_file="HR-999_sample.md",
        policy_id="HR-999",
        region="TEST",
        effective_date="2026-01-01",
    )


def test_header_never_separated_from_clause():
    chunker = StructureAwareChunker()
    chunks = chunker.chunk(_doc())

    target = [c for c in chunks if c.section == "4.2"]
    assert len(target) >= 1, "expected at least one chunk for section 4.2"

    for c in target:
        assert "4.2" in c.text.split("\n", 1)[0], "chunk must start with its own section header line"
    assert any("carry-over cap of 2 days" in c.text for c in target), (
        "the clause body must co-occur with the 4.2 header in the same chunk"
    )


def test_sections_get_distinct_section_numbers():
    chunker = StructureAwareChunker()
    chunks = chunker.chunk(_doc())
    sections = {c.section for c in chunks}
    assert {"1", "4.2", "4.3"}.issubset(sections)


def test_long_section_repeats_header_on_each_subchunk():
    long_body = "\n\n".join([f"Paragraph {i} " + ("x" * 200) for i in range(10)])
    doc_text = f"""# HR-998 — Long Section Policy

Region: TEST
Effective Date: 2026-01-01
Policy ID: HR-998

### 5.1 Long Clause

{long_body}
"""
    doc = RawDoc(
        text=doc_text,
        source_file="HR-998_long.md",
        policy_id="HR-998",
        region="TEST",
        effective_date="2026-01-01",
    )
    chunks = StructureAwareChunker().chunk(doc)
    section_chunks = [c for c in chunks if c.section == "5.1"]
    assert len(section_chunks) > 1, "expected the long section to be sub-split"
    for c in section_chunks:
        assert c.text.startswith("### 5.1 Long Clause"), (
            "every sub-chunk of a split section must repeat the header line"
        )
