# FrameTrace — Validation and reproducibility

**Upgrade branch:** `improve/frametrace-reliability-ci-case-study`  
**Prior baseline:** [`2810f023905647846492fbec776e974b99c71237`](https://github.com/Preciouscrazy/FrameTrace/commit/2810f023905647846492fbec776e974b99c71237)

## Earlier evidence

The original source included five Python unit tests, one 12-frame fixture, and a GitHub Actions workflow that passed on Ubuntu for Python 3.10–3.12: [successful baseline run #43115386513](https://github.com/Preciouscrazy/FrameTrace/actions/runs/43115386513).

## Upgrade verification (awaiting initial CI run)

The new matrix tests Python **3.10, 3.11, 3.12** on **Windows and Ubuntu**. It installs the package in editable mode, executes unit and CLI subprocess tests, and compares results with the committed report.

| Verification | Expected | Current status |
| --- | --- | --- |
| Ubuntu, 3 Python versions | Unit + CLI suite passes | Awaiting run |
| Windows, 3 Python versions | Unit + CLI suite passes | Awaiting run |
| Golden JSON regression | Exact parsed report equality | Awaiting run |
| CSV validation / CLI overwrite safety | Invalid input rejected without data loss | Awaiting run |

This file will be updated with the exact GitHub Actions run and verified results after CI finishes.

## Reproduce locally

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m frametrace --input examples/frames.csv --output frame-report.json --stutter-ms 33.3
```

The example is **synthetic**, and no CI run constitutes a hardware benchmark or diagnosis of a real game's performance.
