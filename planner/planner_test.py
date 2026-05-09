import unittest
from perception.detector import Detection
from planner.planner import Waypoint, plan_path, is_path_clear


class PlannerTest(unittest.TestCase):

    def test_plan_path_to_clear_goal(self):
        detections = [Detection("car", 0.9, 5.0, 5.0)]
        goal = Waypoint(10.0, 10.0)
        path = plan_path(detections, goal)
        self.assertEqual(len(path), 2)
        self.assertEqual(path[-1], goal)

    def test_plan_path_blocked_goal(self):
        detections = [Detection("pedestrian", 0.95, 10.0, 10.0)]
        goal = Waypoint(10.0, 10.0)
        path = plan_path(detections, goal)
        self.assertEqual(path, [])

    def test_is_path_clear(self):
        waypoints = [Waypoint(0.0, 0.0), Waypoint(5.0, 5.0)]
        detections = [Detection("car", 0.9, 3.0, 3.0)]
        self.assertTrue(is_path_clear(waypoints, detections))

    def test_is_path_blocked(self):
        waypoints = [Waypoint(0.0, 0.0), Waypoint(5.0, 5.0)]
        detections = [Detection("car", 0.9, 5.0, 5.0)]
        self.assertFalse(is_path_clear(waypoints, detections))


if __name__ == "__main__":
    unittest.main()
