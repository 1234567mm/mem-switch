import chromadb
from chromadb.config import Settings
from config import QDRANT_DIR

COLLECTIONS = ["conversations", "memories", "knowledge", "profiles"]


class VectorStore:
    """VectorStore wrapper using Chroma PersistentClient.

    Provides a Qdrant-like API (upsert, search, delete, scroll) on top of Chroma.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if VectorStore._initialized:
            return
        self._ensure_storage_dir()
        self.client = chromadb.PersistentClient(
            path=str(QDRANT_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        self._init_collections()
        VectorStore._initialized = True

    def _ensure_storage_dir(self):
        import os
        os.makedirs(str(QDRANT_DIR), exist_ok=True)

    def _init_collections(self):
        for name in COLLECTIONS:
            self.client.get_or_create_collection(name)

    def upsert(self, collection_name: str, points: list):
        """Insert or update points in a collection.

        Args:
            collection_name: Name of the collection.
            points: List of points with format:
                [{"id": str, "vector": list, "payload": {"content": str, ...}}]
        """
        collection = self.client.get_collection(collection_name)
        ids = []
        documents = []
        metadatas = []

        for point in points:
            ids.append(point["id"])
            documents.append(point["payload"].get("content", ""))
            # metadata excludes 'content' key since it's stored as document
            metadata = {k: v for k, v in point["payload"].items() if k != "content"}
            metadatas.append(metadata)

        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    def search(
        self,
        collection_name: str,
        query_vector: list,
        limit: int = 10,
        query_filter: dict = None,
    ) -> list:
        """Search for similar vectors.

        Args:
            collection_name: Name of the collection.
            query_vector: The query embedding vector.
            limit: Maximum number of results.
            query_filter: Qdrant-style filter, e.g. {"must": [{"key": "type", "match": {"value": "preference"}}]}

        Returns:
            List of results with format: [{"id": str, "score": float, "payload": dict}, ...]
        """
        collection = self.client.get_collection(collection_name)

        # Convert Qdrant-style query_filter to Chroma where clause
        where = None
        if query_filter:
            must_conditions = query_filter.get("must", [])
            for condition in must_conditions:
                if condition.get("key") and condition.get("match"):
                    where = {condition["key"]: condition["match"]["value"]}
                    break

        results = collection.query(
            query_embeddings=[query_vector],
            n_results=limit,
            where=where,
        )

        # Convert Chroma results to Qdrant-like format
        processed = []
        if results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                distance = results["distances"][0][i] if results["distances"] else 0.0
                # Chroma uses L2 distance: smaller distance = more similar
                # Convert to similarity score (1 - normalized_distance)
                score = 1.0 / (1.0 + distance)
                processed.append({
                    "id": results["ids"][0][i],
                    "score": score,
                    "payload": {
                        "content": results["documents"][0][i],
                        **({} if not results["metadatas"][0][i] else results["metadatas"][0][i]),
                    },
                })

        return processed

    def delete(self, collection_name: str, points: list):
        """Delete points from a collection.

        Args:
            collection_name: Name of the collection.
            points: List of point IDs to delete.
        """
        collection = self.client.get_collection(collection_name)

        # Handle wildcard patterns like "doc_id_*"
        ids_to_delete = []
        for point_id in points:
            if "*" in point_id:
                # Query for matching IDs
                all_items = collection.get()
                prefix = point_id.replace("*", "")
                ids_to_delete.extend([id for id in all_items["ids"] if id.startswith(prefix)])
            else:
                ids_to_delete.append(point_id)

        if ids_to_delete:
            collection.delete(ids=ids_to_delete)

    def scroll(self, collection_name: str, limit: int = 100) -> tuple:
        """Retrieve points from a collection.

        Args:
            collection_name: Name of the collection.
            limit: Maximum number of results.

        Returns:
            Tuple of (list of results, next_page_offset or None)
        """
        collection = self.client.get_collection(collection_name)
        # Chroma uses peek() with limit parameter
        result = collection.peek(limit=limit)

        results = []
        for i in range(len(result["ids"])):
            results.append({
                "id": result["ids"][i],
                "payload": {
                    "content": result["documents"][i],
                    **({} if not result["metadatas"][i] else result["metadatas"][i]),
                },
            })

        return (results, None)

    def get_collection_info(self, name: str) -> dict:
        """Get information about a collection."""
        try:
            collection = self.client.get_collection(name)
            count = collection.count()
            return {
                "name": name,
                "vectors_count": count,
                "points_count": count,
                "status": "green",
            }
        except Exception as e:
            return {"name": name, "error": str(e)}
