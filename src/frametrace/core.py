"""Reproducible frame-time summaries and threshold-based stutter event detection."""

import csv
import math
from statistics import mean, median

FIELDS = ["timestamp_ms", "frame_time_ms"]


def load_frames(path):
    """Read a strict, two-column CSV; report physical line numbers on invalid rows."""
    frames = []
    previous = None
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, strict=True)
        try:
            if next(reader, None) != FIELDS:
                raise ValueError("expected CSV header: timestamp_ms,frame_time_ms")
            for row in reader:
                if not row:
                    continue
                line = reader.line_num
                try:
                    if len(row) != 2:
                        raise ValueError("expected exactly two columns")
                    timestamp = float(row[0])
                    duration = float(row[1])
                    if not math.isfinite(timestamp) or timestamp < 0:
                        raise ValueError("timestamp must be finite and non-negative")
                    if not math.isfinite(duration) or duration <= 0:
                        raise ValueError("frame time must be finite and positive")
                    if previous is not None and timestamp <= previous:
                        raise ValueError("timestamps must be strictly increasing")
                except (ValueError, TypeError, OverflowError) as exc:
                    raise ValueError(f"{path}:{line}: {exc}") from exc
                frames.append({"timestamp_ms": timestamp, "frame_time_ms": duration})
                previous = timestamp
        except csv.Error as exc:
            raise ValueError(f"{path}:{reader.line_num}: malformed CSV: {exc}") from exc
    if not frames:
        raise ValueError("no frame samples")
    return frames


def percentile(values, fraction):
    """Nearest-rank percentile with a fraction in [0, 1]."""
    if not values or not math.isfinite(fraction) or not 0 <= fraction <= 1:
        raise ValueError("invalid percentile input")
    if any(not math.isfinite(value) for value in values):
        raise ValueError("percentile values must be finite")
    ordered = sorted(values)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def analyze(frames, stutter_ms=33.3):
    if not math.isfinite(stutter_ms) or stutter_ms <= 0:
        raise ValueError("stutter threshold must be finite and positive")
    if not frames:
        raise ValueError("no frames")

    validated = []
    previous = None
    try:
        for frame in frames:
            timestamp = float(frame["timestamp_ms"])
            duration = float(frame["frame_time_ms"])
            if not math.isfinite(timestamp) or timestamp < 0:
                raise ValueError("timestamps must be finite and non-negative")
            if previous is not None and timestamp <= previous:
                raise ValueError("timestamps must increase")
            if not math.isfinite(duration) or duration <= 0:
                raise ValueError("frame times must be finite and positive")
            validated.append((timestamp, duration))
            previous = timestamp
    except (KeyError, TypeError, OverflowError) as exc:
        raise ValueError("invalid frame sample") from exc

    times = [duration for _, duration in validated]
    slow_count = max(1, math.ceil(len(times) * 0.01))
    slowest = sorted(times, reverse=True)[:slow_count]

    events = []
    current = None
    for timestamp, duration in validated:
        if duration >= stutter_ms:
            if current is None:
                current = {"start_ms": timestamp, "end_ms": timestamp,
                           "frame_count": 0, "peak_frame_ms": 0.0}
            current["end_ms"] = timestamp
            current["frame_count"] += 1
            current["peak_frame_ms"] = max(current["peak_frame_ms"], duration)
        elif current is not None:
            events.append(current)
            current = None
    if current is not None:
        events.append(current)

    try:
        mean_fps = 1000.0 / mean(times)
        one_percent_low = 1000.0 / mean(slowest)
        median_ms = median(times)
    except OverflowError as exc:
        raise ValueError("frame-time statistics are outside the supported numeric range") from exc
    if not all(map(math.isfinite, (mean_fps, one_percent_low, median_ms))):
        raise ValueError("frame-time statistics are outside the supported numeric range")

    return {
        "frame_count": len(times),
        "mean_fps": mean_fps,
        "median_frame_ms": median_ms,
        "p95_frame_ms": percentile(times, 0.95),
        "p99_frame_ms": percentile(times, 0.99),
        "one_percent_low_fps_approx": one_percent_low,
        "stutter_threshold_ms": stutter_ms,
        "stutter_frame_count": sum(event["frame_count"] for event in events),
        "stutter_events": events,
        "limitations": "Frame times alone cannot identify CPU/GPU/network root cause.",
    }
