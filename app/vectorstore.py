from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import QDRANT_PATH

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        QDRANT_PATH.mkdir(parents=True, exist_ok=True)
        _client = QdrantClient(path=str(QDRANT_PATH))
    return _client


def ensure_collection(collection_name: str, vector_size: int, recreate: bool = False) -> None:
    client = get_client()
    exists = client.collection_exists(collection_name)
    if exists and recreate:
        client.delete_collection(collection_name)
        exists = False
    if not exists:
        client.create_collection(
            collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def collection_count(collection_name: str) -> int:
    client = get_client()
    if not client.collection_exists(collection_name):
        return 0
    return client.count(collection_name).count


def upsert_points(collection_name: str, points: list[PointStruct]) -> None:
    get_client().upsert(collection_name=collection_name, points=points)
