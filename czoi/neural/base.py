
from abc import ABC, abstractmethod
from typing import Any, List
import numpy as np

class NeuralComponent(ABC):
    """Base class for all neural components."""
    @abstractmethod
    def train(self, data: Any):
        """Train the model."""
        pass

    @abstractmethod
    def predict(self, input: Any) -> Any:
        """Make prediction."""
        pass

    @abstractmethod
    def save(self, path: str):
        """Save model to disk."""
        pass

    @classmethod
    @abstractmethod
    def load(cls, path: str) -> 'NeuralComponent':
        """Load model from disk."""
        pass
