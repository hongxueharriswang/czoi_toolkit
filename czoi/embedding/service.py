# czoi/embedding/service.py
import weakref
from typing import Dict, Tuple, Optional
from uuid import UUID
import numpy as np
from czoi.zones.base import Zone

class EmbeddingService:
    """
    Semantic embedding service for all CZOA entities.
    """
    def __init__(self, dimension: int = 128):
        self.dimension = dimension
        self._embeddings: Dict[Tuple[str, UUID], np.ndarray] = {}
        self._zone_cache = weakref.WeakKeyDictionary()

    def set_embedding(self, entity_type: str, entity_id: UUID, vector: np.ndarray) -> None:
        if len(vector) != self.dimension:
            raise ValueError(f"Vector dimension must be {self.dimension}")
        self._embeddings[(entity_type, entity_id)] = vector.copy()

    def get_embedding(self, entity_type: str, entity_id: UUID) -> Optional[np.ndarray]:
        key = (entity_type, entity_id)
        if key in self._embeddings:
            return self._embeddings[key]
        # Generate random default embedding
        vec = np.random.randn(self.dimension) * 0.1
        self._embeddings[key] = vec
        return vec

    def compute_zone_embedding(self, zone: 'Zone') -> np.ndarray:
        if zone in self._zone_cache:
            return self._zone_cache[zone]

        if not zone.is_composite:
            vec = self.get_embedding('zone', zone.id)
        else:
            child_embeddings = [self.compute_zone_embedding(child) for child in zone.children]
            if child_embeddings:
                combined = np.mean(child_embeddings, axis=0)
            else:
                combined = np.zeros(self.dimension)
            # Include property embeddings
            prop_vecs = []
            for prop in zone.properties.values():
                pv = self.get_embedding('property', prop.id)
                prop_vecs.append(pv)
            if prop_vecs:
                prop_combined = np.mean(prop_vecs, axis=0)
                combined = 0.7 * combined + 0.3 * prop_combined
            vec = combined

        self._zone_cache[zone] = vec
        return vec

    def similarity(self, entity1: Tuple[str, UUID], entity2: Tuple[str, UUID]) -> float:
        v1 = self.get_embedding(entity1[0], entity1[1])
        v2 = self.get_embedding(entity2[0], entity2[1])
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))