"""Frame-time summary and consecutive-threshold event detection."""
import csv
import math
from statistics import mean, median

FIELDS = {"timestamp_ms", "frame_time_ms"}

def load_frames(path):
    frames = []
    previous = None
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not FIELDS.issubset(reader.fieldnames):
            raise ValueError("missing required CSV columns")
        for line, row in enumerate(reader, 2):
            try:
                timestamp = float(row["timestamp_ms"])
                duration = float(row["frame_time_ms"])
                if not math.isfinite(timestamp) or not math.isfinite(duration) or duration <= 0:
                    raise ValueError("non-finite timestamp or nonpositive frame time")
                if previous is not None and timestamp <= previous:
                    raise ValueError("timestamps must be strictly increasing")
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(f"{path}:{line}: {exc}") from exc
            frames.append({"timestamp_ms": timestamp, "frame_time_ms": duration})
            previous = timestamp
    if not frames:
        raise ValueError("no frame samples")
    return frames

def percentile(values, fraction):
    """Nearest-rank percentile (fraction in [0,1])."""
    if not values or not 0 <= fraction <= 1:
        raise ValueError("invalid percentile input")
    ordered = sorted(values)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]

def analyze(frames, stutter_ms=33.3):
    if not math.isfinite(stutter_ms) or stutter_ms <= 0:
        raise ValueError("stutter threshold must be finite and positive")
    if not frames:
        raise ValueError("no frames")
    times = [f["frame_time_ms"] for f in frames]
    if any(not math.isfinite(t) or t <= 0 for t in times):
        raise ValueError("frame times must be finite and positive")
    if any(frames[i]["timestamp_ms"] <= frames[i-1]["timestamp_ms"] for i in range(1, len(frames))):
        raise ValueError("timestamps must increase")
    slow_count = max(1, math.ceil(len(times) * 0.01))
    slowest = sorted(times, reverse=True)[:slow_count]
    events = []
    current = None
    for frame in frames:
        if frame["frame_time_ms"] >= stutter_ms:
            if current is None:
                current = {"start_ms": frame["timestamp_ms"], "end_ms": frame["timestamp_ms"],
                           "frame_count": 0, "peak_frame_ms": 0.0}
            current["end_ms"] = frame["timestamp_ms"]
            current["frame_count"] += 1
            current["peak_frame_ms"] = max(current["peak_frame_ms"], frame["frame_time_ms"])
        elif current is not None:
            events.append(current)
            current = None
    if current is not None:
        events.append(current)
    return {
        "frame_count": len(times),
        "mean_fps": 1000.0 / mean(times),
        "median_frame_ms": median(times),
        "p95_frame_ms": percentile(times, 0.95),
        "p99_frame_ms": percentile(times, 0.99),
        "one_percent_low_fps_approx": 1000.0 / mean(slowest),
        "stutter_threshold_ms": stutter_ms,
        "stutter_frame_count": sum(event["frame_count"] for event in events),
        "stutter_events": events,
        "limitations": "Frame times alone cannot identify CPU/GPU/network root cause.",
    }
