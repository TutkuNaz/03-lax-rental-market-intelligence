# LAX Rental Market Intelligence

[![CI](https://github.com/atasardacagan/03-lax-rental-market-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/atasardacagan/03-lax-rental-market-intelligence/actions/workflows/ci.yml)
[![LAWA source check](https://github.com/atasardacagan/03-lax-rental-market-intelligence/actions/workflows/source-check.yml/badge.svg)](https://github.com/atasardacagan/03-lax-rental-market-intelligence/actions/workflows/source-check.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A reproducible Python and SQL analysis of Los Angeles World Airports rental-car demand, seasonality, market share, concentration, and revenue benchmarks for calendar year 2024.

Part of the [Automotive Open Data Hub](https://github.com/atasardacagan/automotive-data-portfolio), a curated collection of automotive and mobility datasets with reproducible starter analyses.

## What this project answers

- Which months have the highest and lowest on-airport rental transaction volume?
- How concentrated is the observed company-level market?
- Which company shares vary most across the 12 reported months?
- How does LAWA-reported gross revenue after exclusions compare with transaction volume?

The analysis uses aggregate public data. It does not estimate internal pricing, fleet utilization, customer behavior, margin, or profitability.

## Official source and provenance

Primary source: [LAWA — CY2024 LAX On and Off Airport Monthly Stats](https://www.lawa.org/sites/lawa/files/documents/CY2024%20LAX%20On%20and%20Off%20Airport%20Monthly%20Stats.pdf).

The retrieval script downloads the official PDF, validates its file signature, extracts the transaction and revenue tables, and records the retrieval timestamp and SHA-256 hash locally. The original document and extracted raw tables are excluded from Git. LAWA's [rental-car statistics archive](https://www.lawa.org/lawa-investor-relations/statistics-for-lax/lax-rental-car-statistics) provides the path toward a multi-year release.

See [data/README.md](data/README.md) for source scope, licensing notes, and the documented $1 revenue reconciliation difference.

## Analytical workflow

1. Download the canonical report or parse a supplied local copy.
2. Validate required columns, numeric values, unique companies, and company coverage across tables.
3. Reconcile all 12 monthly company rows to annual transactions.
4. Check reported annual shares against transaction-derived shares.
5. Reshape the source to a company-month table and compute monthly shares.
6. Materialize both analytical tables in an indexed SQLite database.
7. Execute version-controlled SQL and export its results to Markdown.
8. Generate metrics and SVG figures for the README and dashboard.

## Data quality contract

- 12 companies and 144 company-month observations
- 2,273,819 on-airport transactions in CY2024
- monthly company values reconcile to annual source totals
- transaction and revenue company sets match one-to-one
- printed revenue total: $816,143,884
- sum of printed company revenue rows: $816,143,885
- preserved reconciliation difference: $1

The pipeline fails clearly when the PDF-derived schema, reconciliation, or company coverage changes.

## Findings

![Monthly transactions](reports/figures/monthly_transactions.svg)

![Annual market share](reports/figures/annual_market_share.svg)

![Monthly share heatmap](reports/figures/market_share_heatmap.svg)

- August is the peak month with **211,493** transactions; December is the trough with **164,617**.
- Peak volume is approximately **28.5%** above the trough.
- The three largest companies account for **49.4%** of annual transactions.
- Transaction-share HHI is approximately **1,256** on the 0–10,000 scale.
- Hertz has the highest monthly share variability at approximately **0.96 percentage points**.

Volatility is defined consistently in Python and SQL as the population standard deviation across all 12 monthly percentages. Concentration measures are descriptive market indicators, not regulatory conclusions.

## Revenue benchmark

![Revenue per transaction](reports/figures/revenue_per_transaction.svg)

Sixt has the highest calculated gross-revenue-after-exclusions per transaction at approximately **$558** in the source year. This ratio is not a rental price, margin, or profitability measure: rental duration, vehicle mix, fees, and reporting definitions are not controlled for.

## SQL and dashboard

The SQL layer covers monthly seasonality, company ranking and HHI contribution, population share volatility, and revenue per transaction. The pipeline regenerates [reports/sql_results.md](reports/sql_results.md) directly from [sql/business_analysis.sql](sql/business_analysis.sql).

After building the processed data, launch the interactive explorer with:

    streamlit run dashboard/app.py

## Run locally

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    python scripts/download_data.py
    python scripts/run_analysis.py
    python -m pytest -q

Windows activation: .venv\Scripts\activate

To parse an existing report without downloading it again:

    python scripts/download_data.py --pdf /path/to/CY2024-report.pdf

## Repository layout

    03-lax-rental-market-intelligence/
    ├── data/              # provenance and ignored raw/processed boundaries
    ├── notebooks/         # transparent analytical views
    ├── scripts/           # PDF retrieval, parsing, and pipeline entry point
    ├── src/rental_market/ # tested transformation and analysis package
    ├── sql/               # executable business queries
    ├── dashboard/         # Streamlit explorer
    ├── reports/           # compact reference outputs
    ├── tests/             # schema, parser, metric, and end-to-end tests
    └── .github/           # CI, dependency updates, and source monitoring

## Roadmap and limitations

The current analysis covers one calendar year and cannot separate airport traffic growth from rental-market dynamics. The public source omits rental duration, vehicle class, fleet size, utilization, and customer attributes. Revenue is unaudited according to LAWA.

The [roadmap](ROADMAP.md) defines a multi-year panel, company-name normalization, passenger-volume normalization, revised-report handling, and a versioned machine-readable release.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) for the data and parser checklist. Report vulnerabilities privately using [SECURITY.md](SECURITY.md).

## License

Repository code and original analysis are MIT licensed. The original LAWA document is not redistributed; consult LAWA for the source material's current terms.
