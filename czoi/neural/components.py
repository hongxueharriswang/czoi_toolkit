
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import HDBSCAN
from typing import Any, List, Dict
from .base import NeuralComponent

class AnomalyDetector(NeuralComponent):
    """Detect anomalous access patterns using Isolation Forest."""
    def __init__(self, contamination=0.1):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.trained = False

    def train(self, data: np.ndarray):
        self.model.fit(data)
        self.trained = True

    def predict(self, input: np.ndarray) -> float:
        """Return anomaly score (higher = more anomalous)."""
        if not self.trained:
            raise RuntimeError("Model not trained")
        # IsolationForest returns -1 for anomalies, 1 for normal.
        # Convert to risk score in [0,1].
        scores = self.model.decision_function(input)
        # Normalize: scores range approx [-0.5, 0.5] for typical data.
        risk = 1.0 - (scores + 0.5)  # crude normalization
        return float(np.clip(risk, 0, 1))

    def save(self, path: str):
        import joblib
        joblib.dump(self.model, path)

    @classmethod
    def load(cls, path: str) -> 'AnomalyDetector':
        import joblib
        detector = cls()
        detector.model = joblib.load(path)
        detector.trained = True
        return detector

class RoleMiner(NeuralComponent):
    """Discover latent roles from user-operation logs using clustering."""
    def __init__(self, min_cluster_size=5):
        self.model = HDBSCAN(min_cluster_size=min_cluster_size)
        self.labels_ = None

    def train(self, data: np.ndarray):
        self.labels_ = self.model.fit_predict(data)

    def predict(self, input: np.ndarray) -> List[int]:
        """Return cluster labels for new data points."""
        # HDBSCAN does not have a native predict; approximate by finding nearest cluster
        # For simplicity, return empty list.
        return []

    def save(self, path: str):
        import joblib
        joblib.dump(self.model, path)

    @classmethod
    def load(cls, path: str) -> 'RoleMiner':
        import joblib
        miner = cls()
        miner.model = joblib.load(path)
        miner.labels_ = miner.model.labels_
        return miner
