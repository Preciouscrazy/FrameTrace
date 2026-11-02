# FrameTrace

**Offline frame-time diagnostics** for analyzing game stutter from timestamped frame samples.

FrameTrace reads frame-time CSV files and calculates mean FPS (derived from mean frame time), median frame time, p95/p99 frame time, 1% low FPS approximation, and contiguous stutter events. It generates a JSON report for local investigation.

## Quick start

Requires Python 3.10+; runtime uses the standard library only.

```bash
python -m pip install -e .
python -m frametrace --input examples/frames.csv --output frame-report.json --stutter-ms 33.3
python -m unittest discover -s tests -v
```

Input columns: `timestamp_ms,frame_time_ms`. Timestamp values must be strictly increasing, and frame times must be finite and positive. All times are in milliseconds.

## Metrics

- **Mean FPS** = 1000 / mean frame time (not the arithmetic mean of instantaneous FPS).
- **p95/p99** use nearest-rank percentiles.
- **1% low FPS approximation** = 1000 / mean of the slowest max(1, ceil(1% of frames)) frame times.
- **Stutter event** = consecutive frames whose frame time is at least the configurable threshold; each event includes first and last timestamps, frame count, and peak frame time.

## Limitations

This tool cannot distinguish CPU bottlenecks, GPU bottlenecks, network lag, display presentation effects, or driver problems from frame times alone. Capture methodology and hardware matter. Input samples are illustrative; no Riot client or API is accessed.

## Development

MIT licensed. CI runs unit tests on Python 3.10–3.12.
