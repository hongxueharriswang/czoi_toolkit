
from abc import ABC, abstractmethod
from typing import List, Tuple, Any
import numpy as np

class VectorStore(ABC):
    """Abstract base for vector similarity search."""
    @abstractmethod
    def upsert(self, entity_id: str, vector: np.ndarray):
        """Insert or update vector for entity."""
        pass

    @abstractmethod
    def similarity_search(self, query: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        """Return top-k similar entity IDs with scores."""
        pass

    @abstractmethod
    def get(self, entity_id: str) -> np.ndarray:
        """Retrieve vector for entity."""
        pass

class InMemoryVectorStore(VectorStore):
    """Simple in-memory store for testing."""
    def __init__(self):
        self.vectors = {}

    def upsert(self, entity_id: str, vector: np.ndarray):
        self.vectors[entity_id] = vector

    def similarity_search(self, query: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        import heapq
        scores = []
        for eid, vec in self.vectors.items():
            # cosine similarity
            sim = np.dot(query, vec) / (np.linalg.norm(query) * np.linalg.norm(vec))
            scores.append((sim, eid))
        top = heapq.nlargest(k, scores)
        return [(eid, sim) for sim, eid in top]

    def get(self, entity_id: str) -> np.ndarray:
        return self.vectors.get(entity_id)
