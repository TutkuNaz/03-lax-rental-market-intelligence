# Contributing

Contributions that improve LAWA source coverage, parser resilience, reproducibility, documentation, tests, or market interpretation are welcome.

## Development workflow

1. Fork the repository and create a focused branch.
2. Use Python 3.11 or 3.12 in a virtual environment.
3. Install dependencies with pip install -r requirements.txt.
4. Run python scripts/download_data.py, python scripts/run_analysis.py, and python -m pytest -q.
5. Compile sources with python -m compileall -q src scripts dashboard.

## Data and parser checklist

- Use an official LAWA report URL and record the report year and scope.
- Preserve printed source values and document reconciliation differences.
- Add a compact synthetic fixture when PDF parsing behavior changes.
- Keep the original PDF and extracted raw tables out of Git.
- Define denominator, aggregation level, and population/sample convention for metrics.
- Do not add customer-level, personal, confidential, or proprietary rental-company data.

Open an issue before adding a new year or materially changing the analytical schema so the cross-year normalization can be reviewed.
