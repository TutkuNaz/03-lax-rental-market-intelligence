from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from rental_market.pipeline import run

TRANSACTIONS = ROOT / "data" / "raw" / "lax_rental_transactions_2024.csv"
REVENUE = ROOT / "data" / "raw" / "lax_rental_annual_revenue_2024.csv"

if __name__ == "__main__":
    if not TRANSACTIONS.exists() or not REVENUE.exists():
        raise SystemExit("Extracted source tables not found. Run `python scripts/download_data.py` first.")
    summary = run(TRANSACTIONS, REVENUE, ROOT)
    print(summary)
