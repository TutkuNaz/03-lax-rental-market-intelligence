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
SOURCE_YEAR = 2024
SOURCE_REPORTED_REVENUE_TOTAL_USD = 816_143_884
SOURCE_REPORT_URL = "https://www.lawa.org/sites/lawa/files/documents/CY2024%20LAX%20On%20and%20Off%20Airport%20Monthly%20Stats.pdf"
SOURCE_ARCHIVE_URL = "https://www.lawa.org/lawa-investor-relations/statistics-for-lax/lax-rental-car-statistics"
TRANSACTION_REQUIRED_COLUMNS = {
    "company",
    *MONTHS,
    "annual_transactions",
    "annual_market_share_pct",
}
REVENUE_REQUIRED_COLUMNS = {
    "company",
    "annual_gross_revenue_after_exclusions_usd",
}


@dataclass(frozen=True)
class DataQuality:
    companies: int
    company_month_rows: int
    missing_cells: int
    annual_total_matches_months: bool
    market_share_matches_transactions: bool
    revenue_company_match: bool


def _require_columns(frame: pd.DataFrame, required: set[str], table_name: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{table_name} is missing required columns: {', '.join(missing)}")


def load_and_transform(
    transactions_path: Path,
    revenue_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, DataQuality]:
    wide = pd.read_csv(transactions_path)
    revenue = pd.read_csv(revenue_path)
    _require_columns(wide, TRANSACTION_REQUIRED_COLUMNS, "Transactions table")
    _require_columns(revenue, REVENUE_REQUIRED_COLUMNS, "Revenue table")

    missing_cells = int(wide.isna().sum().sum() + revenue.isna().sum().sum())
    wide["company"] = wide["company"].astype("string").str.strip()
    revenue["company"] = revenue["company"].astype("string").str.strip()

    numeric = MONTHS + ["annual_transactions", "annual_market_share_pct"]
    for col in numeric:
        wide[col] = pd.to_numeric(wide[col], errors="coerce")
    revenue["annual_gross_revenue_after_exclusions_usd"] = pd.to_numeric(
        revenue["annual_gross_revenue_after_exclusions_usd"],
        errors="coerce",
    )
    if wide[numeric].isna().any().any() or revenue[
        "annual_gross_revenue_after_exclusions_usd"
    ].isna().any():
        raise ValueError("Source tables contain missing or non-numeric required values")
    if (wide[MONTHS + ["annual_transactions"]].lt(0).any().any()) or (
        revenue["annual_gross_revenue_after_exclusions_usd"] < 0
    ).any():
        raise ValueError("Transaction and revenue values must be non-negative")
    if wide["company"].eq("").any() or revenue["company"].eq("").any():
        raise ValueError("Company names must not be empty")
    if wide["company"].duplicated().any():
        raise ValueError("Company names must be unique in the transactions table")
    if revenue["company"].duplicated().any():
        raise ValueError("Company names must be unique in the revenue table")

    transaction_companies = set(wide["company"])
    revenue_companies = set(revenue["company"])
    revenue_company_match = transaction_companies == revenue_companies
    if not revenue_company_match:
        missing_revenue = sorted(transaction_companies - revenue_companies)
        unexpected_revenue = sorted(revenue_companies - transaction_companies)
        raise ValueError(
            "Revenue companies do not match transaction companies: "
            f"missing={missing_revenue}, unexpected={unexpected_revenue}"
        )

    calculated = wide[MONTHS].sum(axis=1)
    annual_matches = bool((calculated == wide["annual_transactions"]).all())
    if not annual_matches:
        bad = wide.loc[
            calculated != wide["annual_transactions"],
            ["company", "annual_transactions"],
        ]
        raise ValueError(
            "Monthly transactions do not reconcile to annual totals: "
            f"{bad.to_dict('records')}"
        )

    annual_total = float(wide["annual_transactions"].sum())
    if annual_total <= 0:
        raise ValueError("Annual transaction total must be positive")
    calculated_annual_share = wide["annual_transactions"] / annual_total * 100
    share_matches = bool(
        np.allclose(
            calculated_annual_share,
            wide["annual_market_share_pct"],
            atol=0.11,
            rtol=0,
        )
    )
    if not share_matches:
        raise ValueError("Reported annual market shares do not match transaction totals")

    long = wide.melt(
        id_vars=["company", "annual_transactions", "annual_market_share_pct"],
        value_vars=MONTHS,
        var_name="month",
        value_name="transactions",
    )
    long["month_number"] = long["month"].map(
        {month: index + 1 for index, month in enumerate(MONTHS)}
    )
    monthly_totals = long.groupby("month_number", observed=True)["transactions"].transform("sum")
    if (monthly_totals <= 0).any():
        raise ValueError("Every month must have a positive transaction total")
    long["monthly_market_share_pct"] = long["transactions"] / monthly_totals * 100
    long = long.sort_values(["month_number", "company"]).reset_index(drop=True)

    annual = wide[["company", "annual_transactions", "annual_market_share_pct"]].merge(
        revenue,
        on="company",
        how="left",
        validate="one_to_one",
    )
    annual["gross_revenue_per_transaction_usd"] = np.where(
        annual["annual_transactions"] > 0,
        annual["annual_gross_revenue_after_exclusions_usd"]
        / annual["annual_transactions"],
        np.nan,
    )
    quality = DataQuality(
        companies=len(wide),
        company_month_rows=len(long),
        missing_cells=missing_cells,
        annual_total_matches_months=annual_matches,
        market_share_matches_transactions=share_matches,
        revenue_company_match=revenue_company_match,
    )
    return long, annual, quality


def write_sqlite(long: pd.DataFrame, annual: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        long.to_sql("rental_transactions_monthly", connection, if_exists="replace", index=False)
        annual.to_sql("rental_market_annual", connection, if_exists="replace", index=False)
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_rental_month "
            "ON rental_transactions_monthly(month_number)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_rental_company "
            "ON rental_transactions_monthly(company)"
        )


def _format_markdown_value(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        value = round(value, 4)
        if value.is_integer():
            value = int(value)
    return str(value).replace("|", "\\|").replace("\n", " ")


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows returned._"
    columns = [str(column) for column in frame.columns]
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = [
        "| " + " | ".join(_format_markdown_value(value) for value in row) + " |"
        for row in frame.itertuples(index=False, name=None)
    ]
    return "\n".join([header, divider, *rows])


def write_sql_report(database_path: Path, query_path: Path, output_path: Path) -> None:
    sections: list[str] = []
    script = query_path.read_text(encoding="utf-8")
    with sqlite3.connect(database_path) as connection:
        for index, block in enumerate(script.split(";"), start=1):
            statement = block.strip()
            if not statement:
                continue
            title = next(
                (
                    line.removeprefix("--").strip()
                    for line in statement.splitlines()
                    if line.strip().startswith("--")
                ),
                f"Query {index}",
            )
            result = pd.read_sql_query(statement, connection)
            sections.append(f"## {title}\n\n{_markdown_table(result)}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "# Executed SQL results\n\n"
        "Generated by the reproducible pipeline from the cleaned SQLite dataset.\n\n"
        + "\n\n".join(sections)
        + "\n",
        encoding="utf-8",
    )


def summarize(long: pd.DataFrame, annual: pd.DataFrame, quality: DataQuality) -> dict:
    monthly = (
        long.groupby(["month_number", "month"], observed=True)["transactions"]
        .sum()
        .reset_index()
        .sort_values("month_number")
    )
    peak = monthly.loc[monthly["transactions"].idxmax()]
    trough = monthly.loc[monthly["transactions"].idxmin()]
    market = annual.sort_values("annual_transactions", ascending=False).copy()
    total = market["annual_transactions"].sum()
    market["calculated_share"] = market["annual_transactions"] / total
    hhi = float(((market["calculated_share"] * 100) ** 2).sum())
    # Population SD (ddof=0) matches the SQL definition across all 12 months.
    volatility = (
        long.groupby("company", observed=True)["monthly_market_share_pct"]
        .agg(lambda values: values.std(ddof=0))
        .sort_values(ascending=False)
    )
    revenue_rank = annual.sort_values(
        "gross_revenue_per_transaction_usd",
        ascending=False,
    )
    return {
        "source": {
            "organization": "Los Angeles World Airports (LAWA)",
            "report_year": SOURCE_YEAR,
            "report_url": SOURCE_REPORT_URL,
            "archive_url": SOURCE_ARCHIVE_URL,
        },
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
        "share_volatility_definition": (
            "Population standard deviation of 12 monthly market-share percentages (ddof=0)"
        ),
        "most_volatile_share_company": str(volatility.index[0]),
        "most_volatile_share_std_pct_points": float(volatility.iloc[0]),
        "highest_revenue_per_transaction_company": str(revenue_rank.iloc[0]["company"]),
        "highest_revenue_per_transaction_usd": float(
            revenue_rank.iloc[0]["gross_revenue_per_transaction_usd"]
        ),
        "company_row_revenue_sum_usd": float(
            annual["annual_gross_revenue_after_exclusions_usd"].sum()
        ),
        "source_reported_revenue_total_usd": float(SOURCE_REPORTED_REVENUE_TOTAL_USD),
        "revenue_reconciliation_difference_usd": float(
            annual["annual_gross_revenue_after_exclusions_usd"].sum()
            - SOURCE_REPORTED_REVENUE_TOTAL_USD
        ),
    }


def save_figures(long: pd.DataFrame, annual: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    monthly = long.groupby("month_number", observed=True)["transactions"].sum().sort_index()
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.plot(range(1, 13), monthly.values, marker="o")
    ax.set_xticks(range(1, 13), MONTH_LABELS)
    ax.set(
        title="LAX on-airport rental transactions by month — CY2024",
        xlabel="Month",
        ylabel="Transactions",
    )
    fig.tight_layout()
    fig.savefig(output_dir / "monthly_transactions.svg", bbox_inches="tight")
    plt.close(fig)

    share = annual.sort_values("annual_market_share_pct")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(share["company"], share["annual_market_share_pct"])
    ax.set(
        title="Annual on-airport rental market share — CY2024",
        xlabel="Market share (%)",
        ylabel="Company",
    )
    fig.tight_layout()
    fig.savefig(output_dir / "annual_market_share.svg", bbox_inches="tight")
    plt.close(fig)

    pivot = long.pivot(
        index="company",
        columns="month_number",
        values="monthly_market_share_pct",
    )
    ordered = annual.sort_values("annual_transactions", ascending=False)["company"]
    pivot = pivot.loc[ordered]
    fig, ax = plt.subplots(figsize=(10, 6.2))
    image = ax.imshow(pivot.values, aspect="auto")
    ax.set_xticks(np.arange(12), MONTH_LABELS)
    ax.set_yticks(np.arange(len(pivot.index)), pivot.index)
    ax.set(title="Monthly market share heatmap (%)", xlabel="Month", ylabel="Company")
    fig.colorbar(image, ax=ax, label="Market share (%)")
    fig.tight_layout()
    fig.savefig(output_dir / "market_share_heatmap.svg", bbox_inches="tight")
    plt.close(fig)

    revenue = annual.sort_values("gross_revenue_per_transaction_usd")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(revenue["company"], revenue["gross_revenue_per_transaction_usd"])
    ax.set(
        title="Gross revenue after exclusions per transaction",
        xlabel="USD per transaction",
        ylabel="Company",
    )
    fig.tight_layout()
    fig.savefig(output_dir / "revenue_per_transaction.svg", bbox_inches="tight")
    plt.close(fig)


def run(
    transactions_path: Path,
    revenue_path: Path,
    project_root: Path,
) -> dict:
    long, annual, quality = load_and_transform(transactions_path, revenue_path)
    processed_dir = project_root / "data" / "processed"
    reports_dir = project_root / "reports"
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    long.to_csv(processed_dir / "rental_transactions_monthly.csv", index=False)
    annual.to_csv(processed_dir / "rental_market_annual.csv", index=False)
    database_path = processed_dir / "lax_rental_market.sqlite"
    write_sqlite(long, annual, database_path)
    write_sql_report(
        database_path,
        project_root / "sql" / "business_analysis.sql",
        reports_dir / "sql_results.md",
    )
    save_figures(long, annual, reports_dir / "figures")
    summary = summarize(long, annual, quality)
    (reports_dir / "metrics.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return summary
