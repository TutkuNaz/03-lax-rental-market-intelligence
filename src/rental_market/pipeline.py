from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SOURCE_REPORTED_REVENUE_TOTAL_USD = 816_143_884


@dataclass(frozen=True)
class DataQuality:
    companies: int
    company_month_rows: int
    missing_cells: int
    annual_total_matches_months: bool


def load_and_transform(transactions_path: Path, revenue_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, DataQuality]:
    wide = pd.read_csv(transactions_path)
    revenue = pd.read_csv(revenue_path)
    numeric = MONTHS + ["annual_transactions", "annual_market_share_pct"]
    for col in numeric:
        wide[col] = pd.to_numeric(wide[col], errors="coerce")
    revenue["annual_gross_revenue_after_exclusions_usd"] = pd.to_numeric(
        revenue["annual_gross_revenue_after_exclusions_usd"], errors="coerce"
    )
    if wide["company"].duplicated().any():
        raise ValueError("Company names must be unique in the source table.")

    calculated = wide[MONTHS].sum(axis=1)
    annual_matches = bool((calculated == wide["annual_transactions"]).all())
    if not annual_matches:
        bad = wide.loc[calculated != wide["annual_transactions"], ["company", "annual_transactions"]]
        raise ValueError(f"Monthly transactions do not reconcile to annual totals: {bad.to_dict('records')}")

    long = wide.melt(
        id_vars=["company", "annual_transactions", "annual_market_share_pct"],
        value_vars=MONTHS,
        var_name="month",
        value_name="transactions",
    )
    long["month_number"] = long["month"].map({m: i + 1 for i, m in enumerate(MONTHS)})
    monthly_totals = long.groupby("month_number", observed=True)["transactions"].transform("sum")
    long["monthly_market_share_pct"] = np.where(monthly_totals > 0, long["transactions"] / monthly_totals * 100, 0)
    long = long.sort_values(["month_number", "company"]).reset_index(drop=True)

    annual = wide[["company", "annual_transactions", "annual_market_share_pct"]].merge(revenue, on="company", how="left")
    annual["gross_revenue_per_transaction_usd"] = (
        annual["annual_gross_revenue_after_exclusions_usd"] / annual["annual_transactions"]
    )
    quality = DataQuality(
        companies=len(wide),
        company_month_rows=len(long),
        missing_cells=int(wide.isna().sum().sum() + revenue.isna().sum().sum()),
        annual_total_matches_months=annual_matches,
    )
    return long, annual, quality


def write_sqlite(long: pd.DataFrame, annual: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
        long.to_sql("rental_transactions_monthly", con, if_exists="replace", index=False)
        annual.to_sql("rental_market_annual", con, if_exists="replace", index=False)
        con.execute("CREATE INDEX IF NOT EXISTS idx_rental_month ON rental_transactions_monthly(month_number)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_rental_company ON rental_transactions_monthly(company)")


def summarize(long: pd.DataFrame, annual: pd.DataFrame, quality: DataQuality) -> dict:
    monthly = long.groupby(["month_number", "month"], observed=True)["transactions"].sum().reset_index()
    monthly = monthly.sort_values("month_number")
    peak = monthly.loc[monthly["transactions"].idxmax()]
    trough = monthly.loc[monthly["transactions"].idxmin()]
    market = annual.sort_values("annual_transactions", ascending=False).copy()
    total = market["annual_transactions"].sum()
    market["calculated_share"] = market["annual_transactions"] / total
    hhi = float(((market["calculated_share"] * 100) ** 2).sum())
    volatility = long.groupby("company", observed=True)["monthly_market_share_pct"].std().sort_values(ascending=False)
    revenue_rank = annual.sort_values("gross_revenue_per_transaction_usd", ascending=False)
    return {
        "data_quality": asdict(quality),
        "annual_transactions": int(total),
        "peak_month": str(peak["month"]).title(),
        "peak_month_transactions": int(peak["transactions"]),
        "trough_month": str(trough["month"]).title(),
        "trough_month_transactions": int(trough["transactions"]),
        "peak_to_trough_ratio": float(peak["transactions"] / trough["transactions"]),
        "largest_company": str(market.iloc[0]["company"]),
        "largest_company_share_pct": float(market.iloc[0]["calculated_share"] * 100),
        "top3_share_pct": float(market.head(3)["calculated_share"].sum() * 100),
        "hhi": hhi,
        "most_volatile_share_company": str(volatility.index[0]),
        "most_volatile_share_std_pct_points": float(volatility.iloc[0]),
        "highest_revenue_per_transaction_company": str(revenue_rank.iloc[0]["company"]),
        "highest_revenue_per_transaction_usd": float(revenue_rank.iloc[0]["gross_revenue_per_transaction_usd"]),
        "company_row_revenue_sum_usd": float(annual["annual_gross_revenue_after_exclusions_usd"].sum()),
        "source_reported_revenue_total_usd": float(SOURCE_REPORTED_REVENUE_TOTAL_USD),
        "revenue_reconciliation_difference_usd": float(annual["annual_gross_revenue_after_exclusions_usd"].sum() - SOURCE_REPORTED_REVENUE_TOTAL_USD),
    }


def save_figures(long: pd.DataFrame, annual: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    monthly = long.groupby("month_number", observed=True)["transactions"].sum().sort_index()
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.plot(range(1, 13), monthly.values, marker="o")
    ax.set_xticks(range(1, 13), MONTH_LABELS)
    ax.set(title="LAX on-airport rental transactions by month — CY2024", xlabel="Month", ylabel="Transactions")
    fig.tight_layout(); fig.savefig(output_dir / "monthly_transactions.png", dpi=180); plt.close(fig)

    share = annual.sort_values("annual_market_share_pct")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(share["company"], share["annual_market_share_pct"])
    ax.set(title="Annual on-airport rental market share — CY2024", xlabel="Market share (%)", ylabel="Company")
    fig.tight_layout(); fig.savefig(output_dir / "annual_market_share.png", dpi=180); plt.close(fig)

    pivot = long.pivot(index="company", columns="month_number", values="monthly_market_share_pct")
    ordered = annual.sort_values("annual_transactions", ascending=False)["company"]
    pivot = pivot.loc[ordered]
    fig, ax = plt.subplots(figsize=(10, 6.2))
    image = ax.imshow(pivot.values, aspect="auto")
    ax.set_xticks(np.arange(12), MONTH_LABELS)
    ax.set_yticks(np.arange(len(pivot.index)), pivot.index)
    ax.set(title="Monthly market share heatmap (%)", xlabel="Month", ylabel="Company")
    fig.colorbar(image, ax=ax, label="Market share (%)")
    fig.tight_layout(); fig.savefig(output_dir / "market_share_heatmap.png", dpi=180); plt.close(fig)

    rev = annual.sort_values("gross_revenue_per_transaction_usd")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(rev["company"], rev["gross_revenue_per_transaction_usd"])
    ax.set(title="Gross revenue after exclusions per transaction", xlabel="USD per transaction", ylabel="Company")
    fig.tight_layout(); fig.savefig(output_dir / "revenue_per_transaction.png", dpi=180); plt.close(fig)


def run(transactions_path: Path, revenue_path: Path, project_root: Path) -> dict:
    long, annual, quality = load_and_transform(transactions_path, revenue_path)
    processed = project_root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    long.to_csv(processed / "rental_transactions_monthly.csv", index=False)
    annual.to_csv(processed / "rental_market_annual.csv", index=False)
    write_sqlite(long, annual, processed / "lax_rental_market.sqlite")
    save_figures(long, annual, project_root / "reports" / "figures")
    summary = summarize(long, annual, quality)
    (project_root / "reports" / "metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
