import unittest
from perception.detector import Detection
from planner.planner import Waypoint
from safety.validator import validate_path, validation_report


class ValidatorTest(unittest.TestCase):

    def _make_path(self):
        return [Waypoint(0.0, 0.0), Waypoint(5.0, 5.0)]

    def test_valid_path(self):
        detections = [Detection("car", 0.9, 99.0, 99.0)]
        self.assertTrue(validate_path(self._make_path(), detections))

    def test_empty_path_is_invalid(self):
        self.assertFalse(validate_path([], []))

    def test_pedestrian_blocks_path(self):
        detections = [Detection("pedestrian", 0.8, 99.0, 99.0)]
        self.assertFalse(validate_path(self._make_path(), detections))

    def test_low_confidence_pedestrian_is_safe(self):
        detections = [Detection("pedestrian", 0.3, 99.0, 99.0)]
        self.assertTrue(validate_path(self._make_path(), detections))

    def test_obstacle_in_path(self):
        waypoints = [Waypoint(0.0, 0.0), Waypoint(5.0, 5.0)]
        detections = [Detection("car", 0.9, 5.0, 5.0)]
        self.assertFalse(validate_path(waypoints, detections))

    def test_report_lists_reasons(self):
        detections = [Detection("pedestrian", 0.9, 99.0, 99.0)]
        report = validation_report(self._make_path(), detections)
        self.assertFalse(report["safe"])
        self.assertIn("pedestrian(s) detected", report["reasons"][0])

    def test_report_clean_path(self):
        report = validation_report(self._make_path(), [])
        self.assertTrue(report["safe"])
        self.assertEqual(report["reasons"], [])


if __name__ == "__main__":
    unittest.main()
