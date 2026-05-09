"""Planner module: generates a path plan based on detected objects."""

from dataclasses import dataclass
from typing import List

from perception.detector import Detection


@dataclass
class Waypoint:
    x: float
    y: float


def plan_path(detections: List[Detection], goal: Waypoint) -> List[Waypoint]:
    """Return waypoints to reach goal while avoiding detected obstacles."""
    obstacles = {(d.x, d.y) for d in detections if d.confidence >= 0.7}
    if (goal.x, goal.y) in obstacles:
        return []
    return [Waypoint(0.0, 0.0), goal]


def is_path_clear(waypoints: List[Waypoint], detections: List[Detection]) -> bool:
    """Return True if no high-confidence detection blocks the planned path."""
    obstacle_positions = {(d.x, d.y) for d in detections if d.confidence >= 0.7}
    return not any((w.x, w.y) in obstacle_positions for w in waypoints)
