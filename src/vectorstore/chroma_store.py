"""
ChromaDB vector store with logical collections via metadata
"""

from typing import List, Optional, Dict, Any
from pathlib import Path

import chromadb
from chromadb.config import Settings

from ..config import config
from ..processors.base import Chunk
from ..embedding import Embedder


class ChromaStore:
    """
    ChromaDB vector store with a single physical collection and
    logical collections implemented via metadata filtering.
    """

    def __init__(
        self,
        persist_directory: Optional[Path] = None,
        collection_name: Optional[str] = None,
        embedder: Optional[Embedder] = None
    ):
        """
        Initialize ChromaDB store.

        Args:
            persist_directory: Directory for persistence
            collection_name: Name of Chroma collection
            embedder: Embedder instance
        """
        self.persist_directory = Path(persist_directory or config.CHROMA_DIR)
        self.collection_name = collection_name or config.COLLECTION_NAME
        self.embedder = embedder or Embedder()

        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Persistent Chroma client
        self._client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )

        # Prefer the new collection name, but keep the legacy one readable.
        try:
            self._collection = self._client.get_collection(name=self.collection_name)
        except Exception:
            try:
                self._collection = self._client.get_collection(name="aegis-rag_chunks")
                self.collection_name = "aegis-rag_chunks"
            except Exception:
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
        
        # Sidecar file for persistent collections (even empty ones)
        self.collections_file = self.persist_directory / "collections.json"
        self._ensure_collections_file()

    def _ensure_collections_file(self):
        """Ensure collections file exists"""
        if not self.collections_file.exists():
            import json
            with open(self.collections_file, "w") as f:
                json.dump([], f)

    def _load_collections(self) -> List[str]:
        """Load persistent collections"""
        import json
        try:
            if self.collections_file.exists():
                with open(self.collections_file, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _save_collections(self, collections: List[str]):
        """Save persistent collections"""
        import json
        with open(self.collections_file, "w") as f:
            json.dump(sorted(list(set(collections))), f)

    # ------------------------------------------------------------------
    # INGESTION
    # ------------------------------------------------------------------

    def add_chunks(
        self,
        chunks: List[Chunk],
        collections: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add chunks to the vector store.

        Args:
            chunks: List of Chunk objects
            collections: Optional logical collections

        Returns:
            List of chunk IDs added
        """
        if not chunks:
            return []
            
        # Ensure collections exist in persistent storage
        if collections:
            current = self._load_collections()
            updated = False
            for c in collections:
                if c not in current:
                    current.append(c)
                    updated = True
            if updated:
                self._save_collections(current)

        ids: List[str] = []
        documents: List[str] = []
        embeddings: List[List[float]] = []
        metadatas: List[Dict[str, Any]] = []

        for chunk in chunks:
            if not chunk.content or not chunk.content.strip():
                continue

            if collections:
                for c in collections:
                    if c not in chunk.collections:
                        chunk.collections.append(c)

            embedding = self.embedder.embed(chunk.content)

            metadata: Dict[str, Any] = {
                "document_id": chunk.document_id,
                "doc_type": chunk.doc_type,
                "source_file": chunk.source_file,
                "created_at": chunk.created_at,
                "collections": ",".join(chunk.collections) if chunk.collections else ""
            }

            if chunk.page is not None:
                metadata["page"] = chunk.page
            if chunk.timestamp_start is not None:
                metadata["timestamp_start"] = chunk.timestamp_start
            if chunk.timestamp_end is not None:
                metadata["timestamp_end"] = chunk.timestamp_end
            if chunk.speaker:
                metadata["speaker"] = chunk.speaker

            for key, value in chunk.metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    metadata[key] = value

            ids.append(chunk.id)
            documents.append(chunk.content)
            embeddings.append(embedding)
            metadatas.append(metadata)

        if not ids:
            return []

        self._collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        return ids

    # ------------------------------------------------------------------
    # QUERY
    # ------------------------------------------------------------------

    def query(
        self,
        query_text: str,
        n_results: Optional[int] = None,
        doc_types: Optional[List[str]] = None,
        collections: Optional[List[str]] = None,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the vector store.

        Returns:
            List of dicts with content, metadata, similarity
        """
        if not query_text or not query_text.strip():
            return []

        n_results = n_results or config.TOP_K_RESULTS
        query_embedding = self.embedder.embed(query_text)

        where_filter = self._build_where_filter(doc_types, document_id)
        fetch_n = n_results * 3 if collections else n_results

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=fetch_n,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        formatted: List[Dict[str, Any]] = []

        if not results.get("ids") or not results["ids"][0]:
            return []

        for i, chunk_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i]

            if collections:
                chunk_cols = [
                    c.strip()
                    for c in metadata.get("collections", "").split(",")
                    if c.strip()
                ]
                if not any(c in chunk_cols for c in collections):
                    continue

            distance = results["distances"][0][i]
            similarity = max(0.0, 1.0 - distance)

            formatted.append({
                "id": chunk_id,
                "content": results["documents"][0][i],
                "metadata": metadata,
                "distance": distance,
                "similarity": similarity
            })

            if len(formatted) >= n_results:
                break

        return formatted

    # ------------------------------------------------------------------
    # FILTER HELPERS
    # ------------------------------------------------------------------

    def _build_where_filter(
        self,
        doc_types: Optional[List[str]],
        document_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        conditions = []

        if document_id:
            conditions.append({"document_id": {"$eq": document_id}})

        if doc_types:
            if len(doc_types) == 1:
                conditions.append({"doc_type": {"$eq": doc_types[0]}})
            else:
                conditions.append({"doc_type": {"$in": doc_types}})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]

        return {"$and": conditions}

    # ------------------------------------------------------------------
    # MANAGEMENT
    # ------------------------------------------------------------------

    def delete_document(self, document_id: str) -> int:
        results = self._collection.get(
            where={"document_id": {"$eq": document_id}},
            include=[]
        )

        ids = results.get("ids", [])
        if ids:
            self._collection.delete(ids=ids)
            return len(ids)
        return 0

    def get_all_documents(self) -> List[Dict[str, Any]]:
        results = self._collection.get(include=["metadatas"])

        documents: Dict[str, Dict[str, Any]] = {}

        for metadata in results.get("metadatas", []):
            doc_id = metadata.get("document_id")
            if doc_id and doc_id not in documents:
                documents[doc_id] = {
                    "document_id": doc_id,
                    "doc_type": metadata.get("doc_type"),
                    "source_file": metadata.get("source_file"),
                    "collections": (
                        metadata.get("collections", "").split(",")
                        if metadata.get("collections") else []
                    )
                }

        return list(documents.values())

    def get_all_collections(self) -> List[str]:
        """Get all collections (both used and empty)"""
        # Load from file
        persistent = self._load_collections()
        
        # Also scan current documents to be safe/sync
        results = self._collection.get(include=["metadatas"])
        used = set()
        for metadata in results.get("metadatas", []):
            for c in metadata.get("collections", "").split(","):
                if c.strip():
                    used.add(c.strip())
        
        # Merge
        all_colls = sorted(list(set(persistent) | used))
        
        # Update persistent if we found new ones in metadata
        if len(all_colls) > len(persistent):
            self._save_collections(all_colls)
            
        return all_colls

    def create_collection(self, name: str):
        """Create a new collection (persistent)"""
        current = self._load_collections()
        if name not in current:
            current.append(name)
            self._save_collections(current)

    def add_to_collection(self, document_id: str, collection: str):
        # Ensure collection exists in persistent storage
        self.create_collection(collection)
        
        results = self._collection.get(
            where={"document_id": {"$eq": document_id}},
            include=["metadatas"]
        )

        for chunk_id, metadata in zip(results.get("ids", []), results.get("metadatas", [])):
            current = [
                c.strip() for c in metadata.get("collections", "").split(",") if c.strip()
            ]
            if collection not in current:
                current.append(collection)
                self._collection.update(
                    ids=[chunk_id],
                    metadatas=[{"collections": ",".join(current)}]
                )

    def delete_collection(self, collection_name: str) -> int:
        """
        Delete collection from persistent storage.
        - If a document belongs ONLY to this collection, delete the document.
        - If a document belongs to multiple collections, remove this collection tag.
        """
        # Remove from persistent storage
        current = self._load_collections()
        if collection_name in current:
            current.remove(collection_name)
            self._save_collections(current)
            
        # Get all chunks to scan for the collection tag
        results = self._collection.get(include=["metadatas"])

        ids_to_delete = []
        ids_to_update = []
        metadatas_to_update = []
        affected = 0

        for chunk_id, metadata in zip(results.get("ids", []), results.get("metadatas", [])):
            current_tags = [
                c.strip() for c in metadata.get("collections", "").split(",") if c.strip()
            ]
            
            if collection_name in current_tags:
                current_tags.remove(collection_name)
                affected += 1
                
                if not current_tags:
                    # No collections left -> Delete document/chunk
                    ids_to_delete.append(chunk_id)
                else:
                    # Other collections exist -> Update metadata
                    ids_to_update.append(chunk_id)
                    # Create a new metadata dict to avoid modifying the original one in place unexpectedly
                    # (though parsing it from results creates a copy usually)
                    new_metadata = metadata.copy()
                    new_metadata["collections"] = ",".join(current_tags)
                    metadatas_to_update.append(new_metadata)

        # Execute batch operations
        if ids_to_delete:
            self._collection.delete(ids=ids_to_delete)
            
        if ids_to_update:
            self._collection.update(
                ids=ids_to_update,
                metadatas=metadatas_to_update
            )

        return affected

    def get_stats(self) -> Dict[str, Any]:
        documents = self.get_all_documents()
        collections = self.get_all_collections()

        type_counts: Dict[str, int] = {}
        for doc in documents:
            t = doc.get("doc_type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "total_chunks": self._collection.count(),
            "total_documents": len(documents),
            "total_collections": len(collections),
            "documents_by_type": type_counts,
            "collections": collections
        }
