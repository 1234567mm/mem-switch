from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from config import QDRANT_DIR


COLLECTIONS = {
    "conversations": VectorParams(size=768, distance=Distance.COSINE),
    "memories": VectorParams(size=768, distance=Distance.COSINE),
    "knowledge": VectorParams(size=768, distance=Distance.COSINE),
    "profiles": VectorParams(size=768, distance=Distance.COSINE),
}


class VectorStore:
    def __init__(self):
        self.client = QdrantClient(path=str(QDRANT_DIR))
        self._init_collections()

    def _init_collections(self):
        try:
            existing = [c.name for c in self.client.get_collections().collections]
        except Exception:
            existing = []
        for name, params in COLLECTIONS.items():
            if name not in existing:
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=params,
                )

    def get_collection_info(self, name: str) -> dict:
        try:
            info = self.client.get_collection(collection_name=name)
            return {
                "name": name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": str(info.status),
            }
        except Exception as e:
            return {"name": name, "error": str(e)}
