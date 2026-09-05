import re

from app.chunking.base import RawDoc
from app.config import ADDENDA_DIR

_POLICY_ID = re.compile(r"^#\s+(HR-\d+)\s+—", re.MULTILINE)
_REGION = re.compile(r"^Region:\s*(.+)$", re.MULTILINE)
_EFFECTIVE_DATE = re.compile(r"^Effective Date:\s*(.+)$", re.MULTILINE)


def load_addenda() -> list[RawDoc]:
    docs: list[RawDoc] = []
    for path in sorted(ADDENDA_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")

        policy_match = _POLICY_ID.search(text)
        region_match = _REGION.search(text)
        date_match = _EFFECTIVE_DATE.search(text)

        if not (policy_match and region_match and date_match):
            raise ValueError(f"{path.name}: missing required header fields (policy_id/region/effective_date)")

        docs.append(
            RawDoc(
                text=text,
                source_file=path.name,
                policy_id=policy_match.group(1),
                region=region_match.group(1).strip(),
                effective_date=date_match.group(1).strip(),
            )
        )
    return docs
