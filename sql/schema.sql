CREATE TABLE rental_transactions_monthly (
    company TEXT,
    annual_transactions INTEGER,
    annual_market_share_pct REAL,
    month TEXT,
    transactions INTEGER,
    month_number INTEGER,
    monthly_market_share_pct REAL
);

CREATE TABLE rental_market_annual (
    company TEXT,
    annual_transactions INTEGER,
    annual_market_share_pct REAL,
    annual_gross_revenue_after_exclusions_usd REAL,
    gross_revenue_per_transaction_usd REAL
);
