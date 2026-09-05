# Data provenance

Source: Los Angeles World Airports (LAWA), **CY2024 LAX On and Off Airport Monthly Stats**.

- Official PDF: https://www.lawa.org/sites/lawa/files/documents/CY2024%20LAX%20On%20and%20Off%20Airport%20Monthly%20Stats.pdf
- Official archive: https://www.lawa.org/lawa-investor-relations/statistics-for-lax/lax-rental-car-statistics
- Scope used: on-airport rental-car monthly transactions, market share, and gross revenue after exclusions for calendar year 2024
- LAWA disclaimer: https://www.lawa.org/disclaimer
- Revenue figures are described by LAWA as unaudited
- No proprietary rental-company or customer-level data are used

The original PDF and extracted raw tables are not committed. Running python scripts/download_data.py retrieves the canonical report, verifies that it is a PDF, parses both tables, and records retrieval time plus the document SHA-256 hash in the ignored raw-data directory. Pass --pdf with a local path to reproduce parsing without another download.

## Quality note

The company rows in the official revenue table sum to **$816,143,885**, while the printed total row is **$816,143,884**. The repository preserves this $1 reconciliation difference instead of altering a source value.

Monthly share volatility is defined consistently in Python and SQL as the **population standard deviation across all 12 months**. The analysis is a single-year market description, not an estimate of price, utilization, margin, or profitability.
