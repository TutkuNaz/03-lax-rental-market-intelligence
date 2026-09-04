-- 1. Monthly demand profile and seasonality relative to the 2024 monthly average.
WITH monthly AS (
    SELECT month_number, month, SUM(transactions) AS total_transactions
    FROM rental_transactions_monthly
    GROUP BY month_number, month
), baseline AS (
    SELECT AVG(total_transactions) AS monthly_average FROM monthly
)
SELECT m.month, m.total_transactions,
       ROUND(m.total_transactions / b.monthly_average, 3) AS seasonality_index
FROM monthly m CROSS JOIN baseline b
ORDER BY m.month_number;

-- 2. Annual market ranking and concentration contribution.
WITH market AS (
    SELECT company, annual_transactions,
           annual_transactions * 1.0 / SUM(annual_transactions) OVER () AS share
    FROM rental_market_annual
)
SELECT company, annual_transactions, ROUND(share * 100, 2) AS share_pct,
       DENSE_RANK() OVER (ORDER BY share DESC) AS market_rank,
       ROUND(POWER(share * 100, 2), 2) AS hhi_contribution
FROM market
ORDER BY market_rank;

-- 3. Identify companies with the most variable monthly share.
WITH company_stats AS (
    SELECT company,
           AVG(monthly_market_share_pct) AS avg_share,
           AVG(monthly_market_share_pct * monthly_market_share_pct) AS avg_share_squared
    FROM rental_transactions_monthly
    GROUP BY company
)
SELECT company, ROUND(avg_share, 2) AS avg_share_pct,
       ROUND(SQRT(MAX(avg_share_squared - avg_share * avg_share, 0)), 3) AS share_stddev_pct_points
FROM company_stats
ORDER BY share_stddev_pct_points DESC;

-- 4. Revenue-per-transaction benchmark. This is descriptive, not profit or margin.
SELECT company,
       annual_transactions,
       ROUND(annual_gross_revenue_after_exclusions_usd, 0) AS annual_gross_revenue,
       ROUND(gross_revenue_per_transaction_usd, 2) AS gross_revenue_per_transaction
FROM rental_market_annual
ORDER BY gross_revenue_per_transaction DESC;
