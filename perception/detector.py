"""Perception module: detects objects in the environment."""

from dataclasses import dataclass
from typing import List


@dataclass
class Detection:
    label: str
    confidence: float
    x: float
    y: float


def detect_objects(frame_data: dict) -> List[Detection]:
    """Run object detection on a single frame."""
    objects = frame_data.get("objects", [])
    return [
        Detection(
            label=obj["label"],
            confidence=obj.get("confidence", 1.0),
            x=obj.get("x", 0.0),
            y=obj.get("y", 0.0),
        )
        for obj in objects
    ]


def filter_by_confidence(detections: List[Detection], threshold: float) -> List[Detection]:
    return [d for d in detections if d.confidence >= threshold]
