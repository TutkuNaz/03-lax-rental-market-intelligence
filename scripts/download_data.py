"""Download the official CY2024 LAX rental-car PDF and extract analysis tables.

The source PDF itself is not committed. LAWA's general website disclaimer states
that information is public domain unless otherwise indicated, while its Investor
Relations section has additional Terms of Use. This project therefore keeps the
original document external and regenerates tabular inputs from LAWA at runtime.
"""
from __future__ import annotations

from pathlib import Path
import re
import urllib.request

import pandas as pd
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PDF_URL = "https://www.lawa.org/sites/lawa/files/documents/CY2024%20LAX%20On%20and%20Off%20Airport%20Monthly%20Stats.pdf"
PDF_PATH = RAW / "CY2024_LAX_RAC_Monthly_Stats.pdf"
COMPANIES = ["Alamo", "Avis", "Budget", "Dollar", "Enterprise", "Fox", "Hertz", "National", "Payless", "Sixt", "Thrifty", "Zipcar"]
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def _download_pdf() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(PDF_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310 - fixed official URL
        PDF_PATH.write_bytes(response.read())


def _numbers(line: str) -> list[str]:
    return re.findall(r"(?:\$\s*)?[0-9][0-9,]*(?:\.\d+)?%?", line)


def _company_lines(text: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        for company in COMPANIES:
            if line.startswith(company + " ") or line == company:
                rows[company] = line
                break
    return rows


def _transaction_half(line: str, second_half: bool) -> tuple[list[int], int | None]:
    tokens = _numbers(line)
    values = [int(tokens[i].replace(",", "")) for i in range(0, min(12, len(tokens)), 2)]
    period_total = int(tokens[12].replace(",", "")) if len(tokens) >= 13 else None
    if second_half and len(tokens) < 13:
        present = [int(t.replace(",", "")) for t in tokens if not t.endswith("%")]
        annual = present[-1] if present else None
        month_values = [0, 0, 0, 0, 0, 0]
        if len(present) >= 4:
            month_values[3:] = present[-4:-1]
        return month_values, annual
    return values, period_total


def _parse_transactions(page_text: str) -> pd.DataFrame:
    parts = page_text.split("Transactions MS")
    if len(parts) < 3:
        raise RuntimeError("Could not identify transaction-table halves in the LAWA PDF.")
    first = _company_lines(parts[1])
    second = _company_lines("Transactions MS".join(parts[2:]))
    records = []
    for company in COMPANIES:
        jan_jun, _ = _transaction_half(first.get(company, ""), False)
        jul_dec, annual = _transaction_half(second.get(company, ""), True)
        if company != "Payless" and (len(jan_jun) != 6 or len(jul_dec) != 6 or annual is None):
            raise RuntimeError(f"Failed to parse transaction row for {company}.")
        if company == "Payless":
            jan_jun = [0] * 6
        vals = (jan_jun + jul_dec)[:12]
        record = {"company": company, **dict(zip(MONTHS, vals)), "annual_transactions": annual or sum(vals)}
        record["annual_market_share_pct"] = round(record["annual_transactions"] / 2_273_819 * 100, 1)
        records.append(record)
    frame = pd.DataFrame(records)
    if int(frame["annual_transactions"].sum()) != 2_273_819:
        raise RuntimeError("Extracted annual transaction total does not match the source report.")
    return frame


def _parse_annual_revenue(page_text: str) -> pd.DataFrame:
    rows = _company_lines(page_text)
    records = []
    for company in COMPANIES:
        tokens = _numbers(rows.get(company, ""))
        money = [int(t.replace("$", "").replace(",", "")) for t in tokens if not t.endswith("%")]
        if not money:
            raise RuntimeError(f"Failed to parse revenue row for {company}.")
        records.append({"company": company, "annual_gross_revenue_after_exclusions_usd": money[-1]})
    return pd.DataFrame(records)


def main() -> None:
    _download_pdf()
    with pdfplumber.open(PDF_PATH) as pdf:
        revenue_text = pdf.pages[0].extract_text(layout=True) or ""
        transaction_text = pdf.pages[1].extract_text(layout=True) or ""
    transactions = _parse_transactions(transaction_text)
    revenue = _parse_annual_revenue(revenue_text)
    transactions.to_csv(RAW / "lax_rental_transactions_2024.csv", index=False)
    revenue.to_csv(RAW / "lax_rental_annual_revenue_2024.csv", index=False)
    print(f"Extracted {len(transactions)} companies and {transactions['annual_transactions'].sum():,} transactions.")


if __name__ == "__main__":
    main()
