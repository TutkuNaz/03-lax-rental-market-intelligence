from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from rental_market.pipeline import load_and_transform, run, summarize
from scripts.download_data import _parse_annual_revenue, _parse_transactions

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def _source_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    transactions = pd.DataFrame(
        [
            {
                "company": "Alpha",
                **{month: 10 + index for index, month in enumerate(MONTHS)},
                "annual_transactions": 186,
                "annual_market_share_pct": 66.7,
            },
            {
                "company": "Beta",
                **{month: 5 + index / 2 for index, month in enumerate(MONTHS)},
                "annual_transactions": 93,
                "annual_market_share_pct": 33.3,
            },
        ]
    )
    revenue = pd.DataFrame(
        {
            "company": ["Alpha", "Beta"],
            "annual_gross_revenue_after_exclusions_usd": [186_000, 69_750],
        }
    )
    return transactions, revenue


def _write_tables(tmp_path: Path) -> tuple[Path, Path]:
    transactions, revenue = _source_tables()
    transactions_path = tmp_path / "transactions.csv"
    revenue_path = tmp_path / "revenue.csv"
    transactions.to_csv(transactions_path, index=False)
    revenue.to_csv(revenue_path, index=False)
    return transactions_path, revenue_path


def test_monthly_transactions_reconcile_and_schema_is_validated(tmp_path: Path):
    transactions_path, revenue_path = _write_tables(tmp_path)
    long, annual, quality = load_and_transform(transactions_path, revenue_path)

    assert quality.annual_total_matches_months
    assert quality.market_share_matches_transactions
    assert quality.revenue_company_match
    assert len(long) == 24
    assert int(annual["annual_transactions"].sum()) == 279
    assert annual.set_index("company").loc[
        "Alpha", "gross_revenue_per_transaction_usd"
    ] == 1000


def test_missing_schema_column_is_rejected(tmp_path: Path):
    transactions, revenue = _source_tables()
    transactions = transactions.drop(columns="dec")
    transactions_path = tmp_path / "transactions.csv"
    revenue_path = tmp_path / "revenue.csv"
    transactions.to_csv(transactions_path, index=False)
    revenue.to_csv(revenue_path, index=False)
    with pytest.raises(ValueError, match="missing required columns: dec"):
        load_and_transform(transactions_path, revenue_path)


def test_revenue_company_mismatch_is_rejected(tmp_path: Path):
    transactions, revenue = _source_tables()
    revenue.loc[1, "company"] = "Unexpected"
    transactions_path = tmp_path / "transactions.csv"
    revenue_path = tmp_path / "revenue.csv"
    transactions.to_csv(transactions_path, index=False)
    revenue.to_csv(revenue_path, index=False)
    with pytest.raises(ValueError, match="Revenue companies do not match"):
        load_and_transform(transactions_path, revenue_path)


def test_python_volatility_uses_population_standard_deviation(tmp_path: Path):
    transactions_path, revenue_path = _write_tables(tmp_path)
    long, annual, quality = load_and_transform(transactions_path, revenue_path)
    metrics = summarize(long, annual, quality)
    expected = (
        long.groupby("company")["monthly_market_share_pct"]
        .agg(lambda values: np.std(values, ddof=0))
        .sort_values(ascending=False)
    )
    assert metrics["most_volatile_share_std_pct_points"] == pytest.approx(expected.iloc[0])
    assert "ddof=0" in metrics["share_volatility_definition"]


def test_text_parser_contract_with_synthetic_lawa_layout():
    companies = ["Alpha", "Beta"]
    first_half = "\n".join(
        [
            "Transactions MS",
            "Alpha 10 50% 10 50% 10 50% 10 50% 10 50% 10 50% 60",
            "Beta 5 50% 5 50% 5 50% 5 50% 5 50% 5 50% 30",
        ]
    )
    second_half = "\n".join(
        [
            "Transactions MS",
            "Alpha 10 50% 10 50% 10 50% 10 50% 10 50% 10 50% 120",
            "Beta 5 50% 5 50% 5 50% 5 50% 5 50% 5 50% 60",
        ]
    )
    transactions = _parse_transactions(
        first_half + "\n" + second_half,
        companies=companies,
        expected_total=180,
    )
    revenue = _parse_annual_revenue(
        "Alpha $120,000\nBeta $45,000",
        companies=companies,
    )
    assert transactions.set_index("company").loc["Alpha", "annual_transactions"] == 120
    assert transactions.loc[:, MONTHS].sum().sum() == 180
    assert revenue.set_index("company").loc[
        "Beta", "annual_gross_revenue_after_exclusions_usd"
    ] == 45_000


def test_run_materializes_all_outputs_from_a_fresh_directory(tmp_path: Path):
    transactions_path, revenue_path = _write_tables(tmp_path)
    (tmp_path / "sql").mkdir()
    source_sql = Path(__file__).resolve().parents[1] / "sql" / "business_analysis.sql"
    (tmp_path / "sql" / "business_analysis.sql").write_text(
        source_sql.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    metrics = run(transactions_path, revenue_path, tmp_path)

    assert metrics["annual_transactions"] == 279
    assert (tmp_path / "data" / "processed" / "rental_transactions_monthly.csv").is_file()
    assert (tmp_path / "data" / "processed" / "rental_market_annual.csv").is_file()
    assert (tmp_path / "data" / "processed" / "lax_rental_market.sqlite").is_file()
    assert (tmp_path / "reports" / "sql_results.md").is_file()
    assert (tmp_path / "reports" / "metrics.json").is_file()
    assert len(list((tmp_path / "reports" / "figures").glob("*.svg"))) == 4
