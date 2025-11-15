"""Predictive preloading (InteractionPredictor) stub

Simple sequence-based predictor using a fixed-size deque.
"""
from collections import deque
from typing import List, Any


class InteractionPredictor:
    def __init__(self, sequence_length: int = 5):
        self.sequence_length = sequence_length
        self._history = deque(maxlen=sequence_length)

    def record(self, item: Any) -> None:
        self._history.append(item)

    def predict_next(self) -> Any:
        """Naive predictor: returns the most recent item or None."""
        if not self._history:
            return None
        return self._history[-1]
