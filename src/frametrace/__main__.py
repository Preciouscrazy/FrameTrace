import argparse
import json
from .core import analyze, load_frames

def main():
    parser = argparse.ArgumentParser(description="Analyze local frame-time CSV data")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="frame-report.json")
    parser.add_argument("--stutter-ms", type=float, default=33.3)
    args = parser.parse_args()
    try:
        report = analyze(load_frames(args.input), stutter_ms=args.stutter_ms)
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(f"Saved {args.output}")

if __name__ == "__main__":
    main()
