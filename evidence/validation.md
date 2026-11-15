# FrameTrace — Cross-platform validation record

**Validated date:** 2026-11-15  
**Tested source commit:** [`5a5861f205a78509f22cbb6617a8aff517c4d51f`](https://github.com/Preciouscrazy/FrameTrace/commit/5a5861f205a78509f22cbb6617a8aff517c4d51f)  
**Pull request:** [#2 — Reliability, CI and engineering case study](https://github.com/Preciouscrazy/FrameTrace/pull/2)

## Verified GitHub Actions

Both [the push run #43692720117](https://github.com/Preciouscrazy/FrameTrace/actions/runs/43692720117) and [the PR run #43692731951](https://github.com/Preciouscrazy/FrameTrace/actions/runs/43692731951) completed with **success** for the same tested source commit.

| Runner | Python 3.10 | Python 3.11 | Python 3.12 |
| --- | --- | --- | --- |
| `ubuntu-24.04` | PASS | PASS | PASS |
| `windows-latest` | PASS | PASS | PASS |

Each job installs FrameTrace in editable mode and runs `python -m unittest discover -s tests -v`. The upgrade defines **25 analysis/CSV unit test methods** and **9 end-to-end CLI regression test methods**. The tests include exact parsed JSON equality with [the committed 12-frame report](sample-frame-report.json), plus input validation, percentile edge cases, stutter run grouping, source-file collision checks, and safe report-file replacement. The hard-link CLI case may be skipped if a runner does not support creating hard links; the other tests remain enforced.

### Baseline

The earlier main branch shipped five unit test methods and passed Ubuntu CI for Python 3.10–3.12: [run #43115386513](https://github.com/Preciouscrazy/FrameTrace/actions/runs/43115386513).

## Reproduce

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m frametrace --input examples/frames.csv --output frame-report.json --stutter-ms 33.3
```

**Scope:** Results establish behavior of these test cases on GitHub-hosted Windows and Ubuntu for the tested source. They do not establish performance on live games, production readiness, or compatibility with every Python version newer than 3.12. Sample frame-time data are synthetic. No runtime dependencies are required beyond Python's standard library.
