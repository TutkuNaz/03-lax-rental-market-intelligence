# LAX Rental Market Intelligence

A business-analysis project built from public Los Angeles World Airports (LAWA) aggregate rental-car statistics for calendar year 2024. It examines seasonality, market concentration, share volatility and a descriptive revenue-per-transaction benchmark.

## Overview

Airport rental operations sit at the intersection of travel demand, fleet availability and competitive market structure. This repository converts a public monthly report into a reproducible analytical dataset, SQLite model, executed SQL analysis and interactive dashboard.

No customer-level, reservation-level or proprietary rental-company data are used.

## Business Problem

A mobility analyst wants to understand:

- when airport rental demand is strongest or weakest;
- how concentrated the on-airport market is;
- which company shares are relatively stable or volatile month to month;
- how LAWA-reported gross revenue after exclusions compares with transaction volume.

The project does **not** attempt to infer internal pricing, utilization, fleet size or profitability.

## Dataset

**Los Angeles World Airports — CY2024 LAX On and Off Airport Monthly Stats**

- Official source: https://www.lawa.org/sites/lawa/files/documents/CY2024%20LAX%20On%20and%20Off%20Airport%20Monthly%20Stats.pdf
- Scope used: on-airport rental-car transactions, market share and gross revenue after exclusions.
- LAWA general disclaimer: https://www.lawa.org/disclaimer
- Original PDF and extracted source tables are not committed; `scripts/download_data.py` retrieves them from LAWA.
- Revenue data are labeled **unaudited** by LAWA.

See [`data/README.md`](data/README.md) for the conservative redistribution approach and source reconciliation note.

## Key Questions

1. Which months show the highest and lowest transaction volume?
2. How large is peak-to-trough seasonality?
3. How concentrated is the market using top-three share and HHI?
4. Which company shares fluctuate most across months?
5. What does annual gross revenue after exclusions per transaction look like across companies, without treating it as price or margin?

## Methodology

1. Retrieve the official LAWA PDF at runtime.
2. Extract on-airport monthly transaction and annual revenue tables.
3. Validate company uniqueness, missing values and monthly-to-annual transaction reconciliation.
4. Reshape to company-month format and calculate monthly market shares.
5. Materialize SQLite analytical tables.
6. Run seasonality, concentration, ranking and volatility SQL analyses.
7. Build static figures, executed notebooks and an interactive dashboard.

## Tech Stack

Python · pandas · NumPy · SQLite · SQL · Matplotlib · Plotly · Streamlit · pdfplumber · pytest · GitHub Actions

## Data Cleaning

- **12 companies** and **144 company-month rows**.
- **0 missing source cells** after the validated extraction.
- Monthly company transactions reconcile exactly to source annual transaction counts.
- The printed annual revenue total is **$816,143,884**, while the sum of company rows is **$816,143,885** — a **$1 source reconciliation difference** preserved in QA.

## Exploratory Data Analysis

![Monthly transactions](reports/figures/monthly_transactions.svg)

![Annual market share](reports/figures/annual_market_share.svg)

![Monthly share heatmap](reports/figures/market_share_heatmap.svg)

## Key Insights

- LAWA reports **2,273,819 on-airport rental transactions** in CY2024.
- **August** was the peak month with **211,493 transactions**; **December** was the trough with **164,617**. Peak volume was about **28.5%** above the trough.
- The three largest companies by annual transaction count represented **49.4%** of transactions.
- The transaction-share HHI is approximately **1,256** on the 0–10,000 scale. This is descriptive market-structure context, not a regulatory conclusion.
- Hertz had the highest monthly share standard deviation in the source year at about **1.00 percentage point** using the pandas sample-standard-deviation calculation.
- Sixt has the highest calculated gross-revenue-after-exclusions per transaction (**$558**). This ratio is **not** rental price, margin or profitability because duration, vehicle mix, fees and accounting definitions differ.

## SQL Analysis

Executed results are in [`reports/sql_results.md`](reports/sql_results.md). Queries use CTEs, aggregations and window functions for:

- monthly seasonality indices;
- market ranking and HHI contributions;
- monthly share volatility;
- annual revenue-per-transaction benchmarking.

![Revenue per transaction](reports/figures/revenue_per_transaction.svg)

## Machine Learning

No ML model is used. Twelve months of aggregate data are not enough to justify a serious forecasting model. A future version should add multiple years, passenger traffic, holidays and other exogenous demand variables before forecasting.

## Results

The public 2024 data show meaningful monthly seasonality and a market where the top three companies account for just under half of annual on-airport transactions. The analysis is useful for market monitoring and demand context but cannot reveal fleet utilization or internal pricing behavior.

## Business Recommendations

- Treat airport rental demand planning as seasonal rather than flat; May–October generally sits above the 2024 monthly average, with August and October especially strong.
- Use multi-year data before converting 2024 seasonality into staffing or fleet-allocation rules.
- Pair rental transactions with passenger arrivals/deplanements to distinguish market growth from airport traffic growth.
- Keep gross-revenue-per-transaction as a descriptive screening metric only; it is insufficient for price or profitability comparisons.

## Dashboard

A Streamlit dashboard is available at [`dashboard/app.py`](dashboard/app.py).

```bash
streamlit run dashboard/app.py
```

## Repository Structure

```text
03-lax-rental-market-intelligence/
├── README.md
├── data/README.md
├── notebooks/
├── scripts/
├── src/rental_market/
├── sql/
├── dashboard/
├── reports/
│   └── figures/
├── tests/
└── .github/workflows/ci.yml
```

## How to Run

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/download_data.py
python scripts/run_analysis.py
pytest -q
streamlit run dashboard/app.py
```

## Data License

The repository does not redistribute the original LAWA PDF. LAWA's general website disclaimer states that information is considered public domain unless otherwise indicated; its Investor Relations area also publishes additional Terms of Use. The project therefore uses runtime retrieval and keeps the original source external. Repository code and original analysis are MIT licensed.

## Limitations

- One calendar year is insufficient for robust demand forecasting.
- Transactions are aggregate and do not reveal rental duration, fleet size, vehicle class, utilization or customer attributes.
- Revenue data are unaudited according to LAWA.
- Revenue per transaction is not price, margin or profit.
- Company structure/brands should not be combined unless the business question explicitly requires a parent-group view.

## Future Improvements

- Add historical LAWA periods where source definitions and extraction remain consistent.
- Normalize transactions by destination/deplaned passenger counts.
- Add airport traffic and holiday features for a proper time-series model.
- Compare on-airport and off-airport rental segments without mixing their revenue definitions.
