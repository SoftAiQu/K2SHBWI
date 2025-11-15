"""Adaptive quality streaming stub

Very small helper that chooses a quality level based on bandwidth.
"""
from typing import Literal


class AdaptiveQualityManager:
    def __init__(self, qualities=(20, 40, 60, 80, 100)):
        self.qualities = qualities

    def choose_quality(self, bandwidth_kbps: float) -> int:
        """Return an integer quality (0-100) based on bandwidth.

        Simple heuristic: more bandwidth -> higher quality.
        """
        if bandwidth_kbps < 200:
            return self.qualities[0]
        if bandwidth_kbps < 500:
            return self.qualities[1]
        if bandwidth_kbps < 1000:
            return self.qualities[2]
        if bandwidth_kbps < 5000:
            return self.qualities[3]
        return self.qualities[4]
