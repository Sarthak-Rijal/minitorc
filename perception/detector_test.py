import unittest
from perception.detector import Detection, detect_objects, filter_by_confidence


class DetectorTest(unittest.TestCase):

    def test_detect_objects_returns_detections(self):
        frame = {"objects": [{"label": "pedestrian", "confidence": 0.95, "x": 10.0, "y": 20.0}]}
        result = detect_objects(frame)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].label, "pedestrian")

    def test_detect_empty_frame(self):
        self.assertEqual(detect_objects({}), [])

    def test_filter_by_confidence(self):
        detections = [
            Detection("car", 0.9, 0.0, 0.0),
            Detection("sign", 0.4, 1.0, 1.0),
            Detection("pedestrian", 0.85, 2.0, 2.0),
        ]
        result = filter_by_confidence(detections, 0.8)
        self.assertEqual(len(result), 2)
        self.assertNotIn("sign", [d.label for d in result])


if __name__ == "__main__":
    unittest.main()
