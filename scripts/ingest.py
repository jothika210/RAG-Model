import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunking.naive import NaiveChunker
from app.chunking.structure_aware import StructureAwareChunker
from app.config import COLLECTIONS
from app.indexing import build_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest the 6 HR addenda into both chunking-strategy collections.")
    parser.add_argument("--recreate", action="store_true", help="Drop and rebuild collections from scratch.")
    args = parser.parse_args()

    naive_count = build_index(NaiveChunker(), COLLECTIONS["naive"], recreate=args.recreate)
    print(f"naive: indexed {naive_count} chunks into '{COLLECTIONS['naive']}'")

    structured_count = build_index(StructureAwareChunker(), COLLECTIONS["structure_aware"], recreate=args.recreate)
    print(f"structure_aware: indexed {structured_count} chunks into '{COLLECTIONS['structure_aware']}'")


if __name__ == "__main__":
    main()
