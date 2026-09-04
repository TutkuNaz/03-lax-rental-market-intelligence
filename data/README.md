# Data provenance

**Source:** Los Angeles World Airports (LAWA), *CY2024 LAX On and Off Airport Monthly Stats*.

- Official PDF: https://www.lawa.org/sites/lawa/files/documents/CY2024%20LAX%20On%20and%20Off%20Airport%20Monthly%20Stats.pdf
- Scope used: on-airport rental-car monthly transactions, market share, and gross revenue after exclusions for calendar year 2024.
- LAWA general website disclaimer: https://www.lawa.org/disclaimer
- LAWA states that website information is considered public domain unless otherwise indicated. The Investor Relations section also publishes additional Terms of Use. To stay conservative, the original PDF and extracted source tables are **not committed**; `scripts/download_data.py` retrieves the official document at runtime.
- Revenue figures are explicitly described by LAWA as coming from unaudited revenue reports.
- No proprietary rental-company data are used.

## Quality note

The company rows in the official revenue table sum to **$816,143,885**, while the printed total row is **$816,143,884**. The repository preserves this $1 reconciliation difference as a data-quality observation instead of silently changing a source value.
