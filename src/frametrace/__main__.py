"""Command-line entry point for the offline FrameTrace report."""

import argparse
import json
import os
from pathlib import Path
import tempfile

from .core import analyze, load_frames


def _same_file(source, destination):
    """Check path aliases and existing hard links before replacing an output."""
    if source.resolve() == destination.resolve():
        return True
    return source.exists() and destination.exists() and source.samefile(destination)


def _write_report(destination, report):
    """Stage a completed JSON report in the destination directory before replacing."""
    content = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n",
            dir=destination.parent, prefix=f".{destination.name}.",
            suffix=".tmp", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Analyze local frame-time CSV data")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="frame-report.json")
    parser.add_argument("--stutter-ms", type=float, default=33.3)
    args = parser.parse_args()

    source = Path(args.input)
    destination = Path(args.output)
    try:
        if _same_file(source, destination):
            raise ValueError("input and output refer to the same file")
        report = analyze(load_frames(source), stutter_ms=args.stutter_ms)
        _write_report(destination, report)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(f"Saved {destination}")


if __name__ == "__main__":
    main()
