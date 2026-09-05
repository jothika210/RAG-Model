import re

from app.chunking.base import Chunk, Chunker, RawDoc

# Matches markdown headers of the form "### 4.2 Title" or "## 1. Title",
# capturing the section number and the full header line. The trailing dot
# after top-level numbers (e.g. "1.") is optional to match subsection style
# (e.g. "4.2") as well.
_SECTION_HEADER = re.compile(r"^(#{2,3})\s+(\d+(?:\.\d+)*)\.?\s+(.+)$", re.MULTILINE)

MAX_SECTION_CHUNK_SIZE = 900


class StructureAwareChunker(Chunker):
    """Splits on policy section headers. A clause is never separated from
    its own section number: each chunk always begins with the header line
    for the section it belongs to. If a section's body is long enough to
    need sub-splitting, the header is repeated at the top of every
    sub-chunk rather than letting the split fall between header and body.
    """

    name = "structure_aware"

    def chunk(self, doc: RawDoc) -> list[Chunk]:
        matches = list(_SECTION_HEADER.finditer(doc.text))

        if not matches:
            # no section headers found at all -- fall back to one chunk
            return [
                Chunk(
                    chunk_id=f"{doc.source_file}::structure_aware::0",
                    text=doc.text.strip(),
                    source_file=doc.source_file,
                    policy_id=doc.policy_id,
                    region=doc.region,
                    effective_date=doc.effective_date,
                    section=None,
                    strategy=self.name,
                )
            ]

        sections: list[tuple[str, str]] = []  # (section_number, full_section_text_incl_header)
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(doc.text)
            section_number = match.group(2)
            section_text = doc.text[start:end].strip()
            sections.append((section_number, section_text))

        chunks: list[Chunk] = []
        idx = 0
        for section_number, section_text in sections:
            header_line = section_text.split("\n", 1)[0]
            body = section_text[len(header_line) :].strip()

            if len(section_text) <= MAX_SECTION_CHUNK_SIZE or not body:
                chunks.append(
                    Chunk(
                        chunk_id=f"{doc.source_file}::structure_aware::{idx}",
                        text=section_text,
                        source_file=doc.source_file,
                        policy_id=doc.policy_id,
                        region=doc.region,
                        effective_date=doc.effective_date,
                        section=section_number,
                        strategy=self.name,
                    )
                )
                idx += 1
                continue

            # sub-split the body but repeat the header on every sub-chunk so
            # the clause is never separated from its section number
            paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
            current = ""
            sub_bodies: list[str] = []
            for para in paragraphs:
                candidate = f"{current}\n\n{para}" if current else para
                if len(header_line) + len(candidate) + 2 <= MAX_SECTION_CHUNK_SIZE:
                    current = candidate
                else:
                    if current:
                        sub_bodies.append(current)
                    current = para
            if current:
                sub_bodies.append(current)

            for sub_body in sub_bodies:
                chunks.append(
                    Chunk(
                        chunk_id=f"{doc.source_file}::structure_aware::{idx}",
                        text=f"{header_line}\n\n{sub_body}",
                        source_file=doc.source_file,
                        policy_id=doc.policy_id,
                        region=doc.region,
                        effective_date=doc.effective_date,
                        section=section_number,
                        strategy=self.name,
                    )
                )
                idx += 1

        return chunks
