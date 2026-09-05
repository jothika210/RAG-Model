from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RawDoc:
    text: str
    source_file: str
    policy_id: str
    region: str
    effective_date: str


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source_file: str
    policy_id: str
    region: str
    effective_date: str
    section: str | None
    strategy: str


class Chunker(ABC):
    name: str

    @abstractmethod
    def chunk(self, doc: RawDoc) -> list[Chunk]: ...
