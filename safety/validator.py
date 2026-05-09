"""Safety module: validates a planned path before execution."""

from typing import List

from perception.detector import Detection
from planner.planner import Waypoint, is_path_clear

MIN_CONFIDENCE_THRESHOLD = 0.6
MAX_WAYPOINTS = 50


def validate_path(waypoints: List[Waypoint], detections: List[Detection]) -> bool:
    """Return True only if the path is safe to execute."""
    if not waypoints:
        return False
    if len(waypoints) > MAX_WAYPOINTS:
        return False
    if not is_path_clear(waypoints, detections):
        return False
    high_risk = [d for d in detections if d.label == "pedestrian" and d.confidence >= MIN_CONFIDENCE_THRESHOLD]
    if high_risk:
        return False
    return True


def validation_report(waypoints: List[Waypoint], detections: List[Detection]) -> dict:
    """Return a structured report explaining why a path passed or failed."""
    reasons = []
    if not waypoints:
        reasons.append("empty path")
    if len(waypoints) > MAX_WAYPOINTS:
        reasons.append(f"path exceeds {MAX_WAYPOINTS} waypoints")
    if waypoints and not is_path_clear(waypoints, detections):
        reasons.append("obstacle in path")
    pedestrians = [d for d in detections if d.label == "pedestrian" and d.confidence >= MIN_CONFIDENCE_THRESHOLD]
    if pedestrians:
        reasons.append(f"{len(pedestrians)} pedestrian(s) detected")
    return {
        "safe": len(reasons) == 0,
        "reasons": reasons,
    }
