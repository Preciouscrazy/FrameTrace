"""End-to-end process, file safety and report regression tests."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FrameTraceCliTests(unittest.TestCase):
    def run_cli(self, *arguments):
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + environment.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-m", "frametrace", *(str(a) for a in arguments)],
            cwd=ROOT, capture_output=True, text=True, env=environment,
            timeout=20, check=False,
        )

    def test_fixture_output_matches_golden_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "report.json"
            result = self.run_cli("--input", ROOT / "examples" / "frames.csv",
                                  "--output", output, "--stutter-ms", "33.3")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8")),
                json.loads((ROOT / "evidence" / "sample-frame-report.json").read_text(encoding="utf-8")),
            )
            self.assertFalse(list(Path(tmp).glob("*.tmp")))

    def test_input_output_alias_rejected_without_data_loss(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv = Path(tmp) / "source.csv"
            csv.write_text("timestamp_ms,frame_time_ms\n0,16.7\n", encoding="utf-8")
            before = csv.read_bytes()
            result = self.run_cli("--input", csv, "--output", csv)
            self.assertEqual(result.returncode, 2)
            self.assertIn("same file", result.stderr)
            self.assertEqual(csv.read_bytes(), before)

    def test_existing_hardlink_to_input_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv = Path(tmp) / "source.csv"
            alias = Path(tmp) / "alias.csv"
            csv.write_text("timestamp_ms,frame_time_ms\n0,16.7\n", encoding="utf-8")
            try:
                os.link(csv, alias)
            except OSError as exc:
                self.skipTest(f"hard links unavailable: {exc}")
            before = csv.read_bytes()
            result = self.run_cli("--input", csv, "--output", alias)
            self.assertEqual(result.returncode, 2)
            self.assertIn("same file", result.stderr)
            self.assertEqual(csv.read_bytes(), before)

    def test_existing_output_is_replaced_without_temporary_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "report.json"
            dest.write_text("old report", encoding="utf-8")
            result = self.run_cli("--input", ROOT / "examples" / "frames.csv", "--output", dest)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(dest.read_text(encoding="utf-8"))["frame_count"], 12)
            self.assertFalse(list(Path(tmp).glob("*.tmp")))

    def test_bad_input_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv = Path(tmp) / "bad.csv"
            dest = Path(tmp) / "report.json"
            csv.write_text("timestamp_ms,frame_time_ms\n0,not-a-frame\n", encoding="utf-8")
            dest.write_text("existing report", encoding="utf-8")
            result = self.run_cli("--input", csv, "--output", dest)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(dest.read_text(encoding="utf-8"), "existing report")

    def test_invalid_threshold_rejected_without_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "report.json"
            result = self.run_cli("--input", ROOT / "examples" / "frames.csv",
                                  "--output", dest, "--stutter-ms", "nan")
            self.assertEqual(result.returncode, 2)
            self.assertFalse(dest.exists())

    def test_missing_input_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli("--input", Path(tmp) / "missing.csv",
                                  "--output", Path(tmp) / "report.json")
            self.assertEqual(result.returncode, 2)
            self.assertIn("Error:", result.stderr)

    def test_help_exits_successfully(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--stutter-ms", result.stdout)

    def test_missing_required_input_returns_usage_error(self):
        result = self.run_cli("--stutter-ms", "33.3")
        self.assertEqual(result.returncode, 2)
        self.assertIn("required", result.stderr)


if __name__ == "__main__":
    unittest.main()
