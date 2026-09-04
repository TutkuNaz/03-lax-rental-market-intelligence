from pathlib import Path

import pandas as pd

from rental_market.pipeline import load_and_transform

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def test_monthly_transactions_reconcile_without_external_files(tmp_path: Path):
    transactions = pd.DataFrame([
        {"company": "Alpha", **{month: 10 for month in MONTHS}, "annual_transactions": 120, "annual_market_share_pct": 60.0},
        {"company": "Beta", **{month: 5 for month in MONTHS}, "annual_transactions": 60, "annual_market_share_pct": 30.0},
    ])
    revenue = pd.DataFrame({
        "company": ["Alpha", "Beta"],
        "annual_gross_revenue_after_exclusions_usd": [120_000, 45_000],
    })
    transactions_path = tmp_path / "transactions.csv"
    revenue_path = tmp_path / "revenue.csv"
    transactions.to_csv(transactions_path, index=False)
    revenue.to_csv(revenue_path, index=False)

    long, annual, quality = load_and_transform(transactions_path, revenue_path)

    assert quality.annual_total_matches_months
    assert len(long) == 24
    assert int(annual["annual_transactions"].sum()) == 180
    assert annual.set_index("company").loc["Alpha", "gross_revenue_per_transaction_usd"] == 1000


def test_reconciliation_failure_is_rejected(tmp_path: Path):
    row = {"company": "Alpha", **{month: 10 for month in MONTHS}, "annual_transactions": 999, "annual_market_share_pct": 100.0}
    transactions_path = tmp_path / "transactions.csv"
    revenue_path = tmp_path / "revenue.csv"
    pd.DataFrame([row]).to_csv(transactions_path, index=False)
    pd.DataFrame({"company": ["Alpha"], "annual_gross_revenue_after_exclusions_usd": [1_000]}).to_csv(revenue_path, index=False)

    try:
        load_and_transform(transactions_path, revenue_path)
    except ValueError as exc:
        assert "do not reconcile" in str(exc)
    else:
        raise AssertionError("Expected reconciliation failure")
