
from typing import Any, List, Tuple, Optional
import numpy as np
from .vector_store import VectorStore
from ..neural.base import NeuralComponent

class EmbeddingService:
    def __init__(self, vector_store: VectorStore, embedder: Optional[NeuralComponent] = None):
        self.vector_store = vector_store
        self.embedder = embedder

    def embed_entity(self, entity: Any) -> np.ndarray:
        """Generate embedding for a single entity."""
        if self.embedder:
            return self.embedder.predict(entity)
        else:
            # Fallback: use entity's string representation
            return self._fallback_embed(str(entity))

    def _fallback_embed(self, text: str) -> np.ndarray:
        """Simple deterministic hash-based embedding (for testing)."""
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        # Convert hash to 256-dim vector of floats in [-1,1]
        vec = np.frombuffer(hash_obj.digest(), dtype=np.uint8) / 127.5 - 1.0
        return vec.astype(np.float32)

    def update_embedding(self, entity_id: str, entity: Any):
        vec = self.embed_entity(entity)
        self.vector_store.upsert(entity_id, vec)

    def find_similar(self, entity_id: str, k: int = 10) -> List[Tuple[str, float]]:
        vec = self.vector_store.get(entity_id)
        if vec is None:
            return []
        return self.vector_store.similarity_search(vec, k)
