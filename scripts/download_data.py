"""Download the official CY2024 LAWA PDF and extract the analysis tables.

The source document remains external. The script can download the canonical PDF
or parse a caller-supplied local copy, making parser validation repeatable.
"""
from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import urllib.request

import pandas as pd
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PDF_URL = "https://www.lawa.org/sites/lawa/files/documents/CY2024%20LAX%20On%20and%20Off%20Airport%20Monthly%20Stats.pdf"
ARCHIVE_URL = "https://www.lawa.org/lawa-investor-relations/statistics-for-lax/lax-rental-car-statistics"
PDF_PATH = RAW / "CY2024_LAX_RAC_Monthly_Stats.pdf"
EXPECTED_ANNUAL_TRANSACTIONS = 2_273_819
COMPANIES = [
    "Alamo",
    "Avis",
    "Budget",
    "Dollar",
    "Enterprise",
    "Fox",
    "Hertz",
    "National",
    "Payless",
    "Sixt",
    "Thrifty",
    "Zipcar",
]
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def _download_pdf(destination: Path = PDF_PATH) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        PDF_URL,
        headers={"User-Agent": "automotive-open-data/1.0"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
        payload = response.read()
    if not payload.startswith(b"%PDF"):
        raise RuntimeError("LAWA source did not return a PDF document")
    destination.write_bytes(payload)
    return destination


def _numbers(line: str) -> list[str]:
    return re.findall(r"(?:\$\s*)?[0-9][0-9,]*(?:\.\d+)?%?", line)


def _company_lines(text: str, companies: list[str] = COMPANIES) -> dict[str, str]:
    rows: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        for company in companies:
            if line.startswith(company + " ") or line == company:
                rows[company] = line
                break
    return rows


def _company_rows(text: str, companies: list[str] = COMPANIES) -> dict[str, list[str]]:
    """Collect repeated company rows while ignoring duplicated table headers."""
    rows = {company: [] for company in companies}
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        for company in companies:
            if line.startswith(company + " ") or line == company:
                rows[company].append(line)
                break
    return rows


def _transaction_half(line: str, second_half: bool) -> tuple[list[int], int | None]:
    tokens = _numbers(line)
    values = [
        int(tokens[index].replace(",", ""))
        for index in range(0, min(12, len(tokens)), 2)
    ]
    period_total = int(tokens[12].replace(",", "")) if len(tokens) >= 13 else None
    if second_half and len(tokens) < 13:
        present = [
            int(token.replace(",", ""))
            for token in tokens
            if not token.endswith("%")
        ]
        annual = present[-1] if present else None
        month_values = [0, 0, 0, 0, 0, 0]
        if len(present) >= 4:
            month_values[3:] = present[-4:-1]
        return month_values, annual
    return values, period_total


def _parse_transactions(
    page_text: str,
    companies: list[str] = COMPANIES,
    expected_total: int = EXPECTED_ANNUAL_TRANSACTIONS,
) -> pd.DataFrame:
    rows = _company_rows(page_text, companies)
    records = []
    for company in companies:
        if company == "Payless":
            if len(rows[company]) != 1:
                raise RuntimeError(
                    f"Expected one partial-year transaction row for {company}; "
                    f"found {len(rows[company])}"
                )
            jan_jun = [0] * 6
            jul_dec, annual = _transaction_half(rows[company][0], True)
        else:
            if len(rows[company]) != 2:
                raise RuntimeError(
                    f"Expected two transaction rows for {company}; "
                    f"found {len(rows[company])}"
                )
            jan_jun, _ = _transaction_half(rows[company][0], False)
            jul_dec, annual = _transaction_half(rows[company][1], True)
        if len(jan_jun) != 6 or len(jul_dec) != 6 or annual is None:
            raise RuntimeError(f"Failed to parse transaction row for {company}")
        values = (jan_jun + jul_dec)[:12]
        record = {
            "company": company,
            **dict(zip(MONTHS, values)),
            "annual_transactions": annual or sum(values),
        }
        record["annual_market_share_pct"] = round(
            record["annual_transactions"] / expected_total * 100,
            1,
        )
        records.append(record)
    frame = pd.DataFrame(records)
    extracted_total = int(frame["annual_transactions"].sum())
    if extracted_total != expected_total:
        raise RuntimeError(
            "Extracted annual transaction total does not match the source report: "
            f"expected {expected_total:,}, received {extracted_total:,}"
        )
    return frame


def _parse_annual_revenue(
    page_text: str,
    companies: list[str] = COMPANIES,
) -> pd.DataFrame:
    rows = _company_lines(page_text, companies)
    records = []
    for company in companies:
        tokens = _numbers(rows.get(company, ""))
        money = [
            int(token.replace("$", "").replace(",", ""))
            for token in tokens
            if not token.endswith("%")
        ]
        if not money:
            raise RuntimeError(f"Failed to parse revenue row for {company}")
        records.append(
            {
                "company": company,
                "annual_gross_revenue_after_exclusions_usd": money[-1],
            }
        )
    return pd.DataFrame(records)


def extract_pdf(pdf_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) < 2:
            raise RuntimeError("LAWA source PDF must contain at least two pages")
        revenue_text = pdf.pages[0].extract_text(layout=True) or ""
        transaction_text = pdf.pages[1].extract_text(layout=True) or ""
    return _parse_transactions(transaction_text), _parse_annual_revenue(revenue_text)


def _write_source_metadata(pdf_path: Path, downloaded: bool) -> None:
    payload = pdf_path.read_bytes()
    metadata = {
        "publisher": "Los Angeles World Airports (LAWA)",
        "report_year": 2024,
        "source_url": PDF_URL,
        "archive_url": ARCHIVE_URL,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "downloaded_by_script": downloaded,
        "pdf_sha256": hashlib.sha256(payload).hexdigest(),
    }
    (RAW / "source_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = ArgumentParser(description="Download or parse the official CY2024 LAWA report")
    parser.add_argument(
        "--pdf",
        type=Path,
        help="Parse an existing local copy instead of downloading the canonical PDF",
    )
    args = parser.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    downloaded = args.pdf is None
    pdf_path = _download_pdf() if downloaded else args.pdf.resolve()
    if not pdf_path.is_file():
        raise SystemExit(f"PDF not found: {pdf_path}")

    transactions, revenue = extract_pdf(pdf_path)
    transactions.to_csv(RAW / "lax_rental_transactions_2024.csv", index=False)
    revenue.to_csv(RAW / "lax_rental_annual_revenue_2024.csv", index=False)
    _write_source_metadata(pdf_path, downloaded)
    print(
        f"Extracted {len(transactions)} companies and "
        f"{transactions['annual_transactions'].sum():,} transactions"
    )


if __name__ == "__main__":
    main()
