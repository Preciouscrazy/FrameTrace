"""Unit and edge-case regression tests for the FrameTrace analysis core."""

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from frametrace.core import analyze, load_frames, percentile


def samples(durations):
    return [
        {"timestamp_ms": i * 20.0, "frame_time_ms": value}
        for i, value in enumerate(durations)
    ]


class FrameTraceTests(unittest.TestCase):
    def setUp(self):
        self.frames = samples([16, 16, 40, 50, 16, 16])

    def csv(self, content):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "frames.csv"
            path.write_text(content, encoding="utf-8")
            return load_frames(path)

    def test_stutter_grouping(self):
        result = analyze(self.frames, stutter_ms=33.3)
        self.assertEqual(result["stutter_frame_count"], 2)
        self.assertEqual(len(result["stutter_events"]), 1)
        self.assertEqual(result["stutter_events"][0]["frame_count"], 2)
        self.assertEqual(result["stutter_events"][0]["peak_frame_ms"], 50.0)

    def test_stutter_ends_at_last_frame(self):
        result = analyze(samples([16, 33.3, 45]), 33.3)
        self.assertEqual(result["stutter_frame_count"], 2)
        self.assertEqual(result["stutter_events"][0]["end_ms"], 40.0)

    def test_exact_threshold_and_separated_events(self):
        result = analyze(samples([33.3, 16, 33.3]), 33.3)
        self.assertEqual(len(result["stutter_events"]), 2)
        self.assertEqual(result["stutter_frame_count"], 2)

    def test_no_stutter_frames(self):
        result = analyze(samples([10, 12, 11]), 33.3)
        self.assertEqual(result["stutter_events"], [])
        self.assertEqual(result["stutter_frame_count"], 0)

    def test_percentile(self):
        self.assertEqual(percentile([1, 2, 3, 4], 0.95), 4)
        self.assertEqual(percentile([4, 3, 2, 1], 0), 1)
        self.assertEqual(percentile([4, 3, 2, 1], 0.5), 2)
        self.assertEqual(percentile([4, 3, 2, 1], 1), 4)

    def test_reject_bad_percentile(self):
        for values, fraction in (
            ([], 0.5), ([1], -0.1), ([1], 1.1),
            ([1], math.nan), ([1], math.inf), ([1, math.nan], 0.5),
        ):
            with self.subTest(values=values, fraction=fraction):
                with self.assertRaises(ValueError):
                    percentile(values, fraction)

    def test_fps_is_inverse_mean_frame_time(self):
        report = analyze(samples([10, 30]))
        self.assertAlmostEqual(report["mean_fps"], 50.0)
        self.assertNotAlmostEqual(report["mean_fps"], (100 + 1000 / 30) / 2)

    def test_one_percent_low_sample_count(self):
        durations = [10.0] * 99 + [50.0, 100.0]
        result = analyze(samples(durations))
        self.assertAlmostEqual(result["one_percent_low_fps_approx"], 1000 / 75)
        self.assertEqual(result["p99_frame_ms"], 50.0)

    def test_reject_threshold(self):
        for threshold in (0, -1, math.nan, math.inf):
            with self.subTest(threshold=threshold):
                with self.assertRaises(ValueError):
                    analyze(self.frames, stutter_ms=threshold)

    def test_reject_empty_frames(self):
        with self.assertRaises(ValueError):
            analyze([])

    def test_reject_timestamp_order(self):
        with self.assertRaises(ValueError):
            analyze(list(reversed(self.frames)))

    def test_reject_nonfinite_and_negative_timestamps(self):
        for value in (-1.0, math.nan, math.inf, -math.inf):
            with self.subTest(timestamp=value):
                with self.assertRaises(ValueError):
                    analyze([{"timestamp_ms": value, "frame_time_ms": 16.0}])

    def test_reject_bad_frame_times(self):
        for value in (0, -2, math.nan, math.inf, -math.inf):
            with self.subTest(duration=value):
                with self.assertRaises(ValueError):
                    analyze([{"timestamp_ms": 0, "frame_time_ms": value}])

    def test_reject_tiny_durations_with_nonfinite_fps(self):
        with self.assertRaisesRegex(ValueError, "numeric range"):
            analyze(samples([5e-324]))

    def test_reject_bad_sample_keys(self):
        with self.assertRaises(ValueError):
            analyze([{"timestamp_ms": 0}])

    def test_sample_csv(self):
        sample = ROOT / "examples" / "frames.csv"
        self.assertEqual(len(load_frames(sample)), 12)

    def test_sample_json_matches_checked_in_report(self):
        result = analyze(load_frames(ROOT / "examples" / "frames.csv"), 33.3)
        expected = json.loads((ROOT / "evidence" / "sample-frame-report.json").read_text(encoding="utf-8"))
        self.assertEqual(result, expected)

    def test_csv_supports_utf8_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "frames.csv"
            path.write_text("timestamp_ms,frame_time_ms\n0,16.7\n", encoding="utf-8-sig")
            self.assertEqual(len(load_frames(path)), 1)

    def test_csv_rejects_wrong_duplicate_and_extra_headers(self):
        for header in (
            "frame_time_ms,timestamp_ms",
            "timestamp_ms",
            "timestamp_ms,frame_time_ms,extra",
            "timestamp_ms,frame_time_ms,frame_time_ms",
        ):
            with self.subTest(header=header):
                with self.assertRaisesRegex(ValueError, "header"):
                    self.csv(header + "\n0,16\n")

    def test_csv_rejects_extra_and_missing_cells(self):
        for row in ("0,16,unwanted", "0", "0,16,"):
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, "two columns"):
                    self.csv("timestamp_ms,frame_time_ms\n" + row + "\n")

    def test_csv_rejects_invalid_row_with_line_number(self):
        for row in ("-1,16", "nan,16", "0,inf", "0,0", "bad,16"):
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, r"frames.csv:2:"):
                    self.csv("timestamp_ms,frame_time_ms\n" + row + "\n")

    def test_csv_rejects_nonincreasing_timestamps(self):
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            self.csv("timestamp_ms,frame_time_ms\n0,16\n0,17\n")

    def test_csv_rejects_no_samples(self):
        with self.assertRaisesRegex(ValueError, "no frame samples"):
            self.csv("timestamp_ms,frame_time_ms\n")

    def test_csv_accepts_quoted_numbers_and_blank_lines(self):
        result = self.csv('timestamp_ms,frame_time_ms\n"0","16.5"\n\n"20","17"\n')
        self.assertEqual([r["frame_time_ms"] for r in result], [16.5, 17.0])

    def test_csv_rejects_invalid_quoted_field(self):
        with self.assertRaises(ValueError):
            self.csv('timestamp_ms,frame_time_ms\n"0,16\n')


if __name__ == "__main__":
    unittest.main()
