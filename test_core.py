import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from frametrace.core import analyze, load_frames, percentile

class FrameTraceTests(unittest.TestCase):
    def setUp(self):
        self.frames = [
            {"timestamp_ms": i * 20.0, "frame_time_ms": v}
            for i, v in enumerate([16, 16, 40, 50, 16, 16])
        ]

    def test_stutter_grouping(self):
        report = analyze(self.frames, stutter_ms=33.3)
        self.assertEqual(len(report["stutter_events"]), 1)
        self.assertEqual(report["stutter_events"][0]["frame_count"], 2)

    def test_percentile(self):
        self.assertEqual(percentile([1, 2, 3, 4], 0.95), 4)

    def test_reject_threshold(self):
        with self.assertRaises(ValueError):
            analyze(self.frames, stutter_ms=0)

    def test_reject_timestamp_order(self):
        with self.assertRaises(ValueError):
            analyze(list(reversed(self.frames)))

    def test_sample_csv(self):
        sample = Path(__file__).resolve().parents[1] / "examples" / "frames.csv"
        self.assertGreater(len(load_frames(sample)), 0)

if __name__ == "__main__":
    unittest.main()
