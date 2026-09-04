# LAX Rental Market Intelligence

A market-level analysis of Los Angeles World Airports (LAWA) rental-car activity for calendar year 2024.

## Objective

The project examines airport rental demand, seasonality, market concentration and company-level transaction share using public LAWA statistics.

Questions addressed:

- Which months have the highest and lowest rental transaction volume?
- How large is the seasonal peak-to-trough difference?
- How concentrated is the on-airport market?
- Which company shares vary most from month to month?
- How does LAWA-reported gross revenue after exclusions compare with transaction volume?

The analysis is based on aggregate public data. It does not estimate internal pricing, utilization, fleet size, customer behavior or profitability.

## Data

Source: **Los Angeles World Airports — CY2024 LAX On and Off Airport Monthly Stats**

- Official PDF: https://www.lawa.org/sites/lawa/files/documents/CY2024%20LAX%20On%20and%20Off%20Airport%20Monthly%20Stats.pdf
- Scope: on-airport rental-car transactions, market share and gross revenue after exclusions
- LAWA disclaimer: https://www.lawa.org/disclaimer
- Revenue figures are identified by LAWA as unaudited.

The original PDF and extracted source tables are not committed. `scripts/download_data.py` retrieves and parses the official document at runtime.

See [`data/README.md`](data/README.md) for provenance and source-handling notes.

## Approach

1. Download the official LAWA report.
2. Extract monthly transaction and annual revenue tables.
3. Validate company names, missing values and annual reconciliation.
4. Reshape monthly data into company-month format.
5. Calculate monthly market shares and seasonality measures.
6. Materialize the analytical tables in SQLite.
7. Run SQL analysis for concentration, ranking and share volatility.
8. Publish figures, executed notebooks and an interactive dashboard.

## Stack

Python · pandas · NumPy · SQLite · SQL · Plotly · Streamlit · pdfplumber · pytest · GitHub Actions

## Data Quality

The analytical dataset contains **12 companies** and **144 company-month observations**.

Monthly transactions reconcile to the annual source totals. One source-level exception is preserved: the printed annual revenue total is **$816,143,884**, while the sum of company rows is **$816,143,885**, a **$1 difference**.

## Analysis

![Monthly transactions](reports/figures/monthly_transactions.svg)

![Annual market share](reports/figures/annual_market_share.svg)

![Monthly share heatmap](reports/figures/market_share_heatmap.svg)

Key findings:

- CY2024 on-airport rental transactions: **2,273,819**.
- **August** recorded the highest monthly volume at **211,493** transactions.
- **December** recorded the lowest at **164,617**.
- Peak monthly volume was approximately **28.5%** above the trough.
- The three largest companies accounted for **49.4%** of annual transactions.
- Transaction-share HHI was approximately **1,256** on the 0–10,000 scale.
- Hertz showed the highest monthly share variability in the source year at roughly **1.00 percentage point** standard deviation.

The concentration measures are used as descriptive market indicators, not regulatory conclusions.

## Revenue Benchmark

![Revenue per transaction](reports/figures/revenue_per_transaction.svg)

Sixt has the highest calculated gross-revenue-after-exclusions per transaction at approximately **$558** in the 2024 data.

This ratio should not be interpreted as rental price, margin or profitability. Rental duration, vehicle mix, fees and reporting definitions are not controlled for in the public source.

## SQL

The SQL layer covers:

- monthly seasonality indices;
- company ranking and HHI contributions;
- monthly share volatility;
- annual revenue-per-transaction benchmarking.

Executed outputs are available in [`reports/sql_results.md`](reports/sql_results.md).

## Business Interpretation

- Rental demand at LAX is meaningfully seasonal rather than evenly distributed across the year.
- Multi-year data would be required before converting 2024 seasonality into staffing or fleet-allocation rules.
- Passenger arrivals and deplanements would improve demand normalization and help separate airport traffic growth from rental-market movement.
- Revenue per transaction is useful as a descriptive benchmark but not as a substitute for pricing or profitability analysis.

## Dashboard

The Streamlit dashboard is available in [`dashboard/app.py`](dashboard/app.py).

```bash
streamlit run dashboard/app.py
```

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/download_data.py
python scripts/run_analysis.py
pytest -q
```

## Repository Layout

```text
03-lax-rental-market-intelligence/
├── data/
├── notebooks/
├── scripts/
├── src/rental_market/
├── sql/
├── dashboard/
├── reports/
├── tests/
└── .github/workflows/ci.yml
```

## Limitations

- The analysis covers one calendar year.
- Source data are aggregate and do not include rental duration, vehicle class, fleet size, utilization or customer attributes.
- Revenue figures are unaudited according to LAWA.
- Revenue per transaction is not equivalent to price, margin or profit.
- Company and parent-brand structures are kept separate unless the business question requires consolidation.

## License

The repository does not redistribute the original LAWA PDF. LAWA's general disclaimer states that website information is considered public domain unless otherwise indicated; additional terms apply within its Investor Relations area. Repository code and original analysis are MIT licensed.
