from pathlib import Path
import json

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
MONTHLY = ROOT / "data" / "processed" / "rental_transactions_monthly.csv"
ANNUAL = ROOT / "data" / "processed" / "rental_market_annual.csv"
METRICS = ROOT / "reports" / "metrics.json"

st.set_page_config(page_title="LAX Rental Market Intelligence", layout="wide")
st.title("LAX Rental Market Intelligence")
st.caption("Calendar Year 2024 — public aggregate on-airport rental-car statistics")

if not MONTHLY.exists() or not ANNUAL.exists():
    st.error("Processed data not found. Run scripts/download_data.py and scripts/run_analysis.py first.")
    st.stop()

monthly = pd.read_csv(MONTHLY)
annual = pd.read_csv(ANNUAL)
metrics = json.loads(METRICS.read_text())
companies = sorted(annual["company"].unique())
selected = st.sidebar.multiselect("Companies", companies, default=companies)
view = monthly[monthly["company"].isin(selected)]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Annual transactions", f"{metrics['annual_transactions']:,}")
c2.metric("Peak month", metrics["peak_month"])
c3.metric("Top-3 share", f"{metrics['top3_share_pct']:.1f}%")
c4.metric("HHI", f"{metrics['hhi']:.0f}")

month_totals = view.groupby(["month_number", "month"], as_index=False)["transactions"].sum().sort_values("month_number")
st.plotly_chart(px.line(month_totals, x="month", y="transactions", markers=True, title="Monthly transactions — selected companies"), use_container_width=True)

left, right = st.columns(2)
with left:
    market = annual[annual["company"].isin(selected)].sort_values("annual_market_share_pct")
    st.plotly_chart(px.bar(market, x="annual_market_share_pct", y="company", orientation="h", title="Annual market share"), use_container_width=True)
with right:
    revenue = annual[annual["company"].isin(selected)].sort_values("gross_revenue_per_transaction_usd")
    st.plotly_chart(px.bar(revenue, x="gross_revenue_per_transaction_usd", y="company", orientation="h", title="Gross revenue after exclusions / transaction"), use_container_width=True)

pivot = view.pivot(index="company", columns="month_number", values="monthly_market_share_pct")
st.plotly_chart(px.imshow(pivot, aspect="auto", labels={"x":"Month number", "y":"Company", "color":"Share %"}, title="Monthly market-share heatmap"), use_container_width=True)
st.caption("Revenue-per-transaction is descriptive and is not a price, margin, or profitability measure.")
