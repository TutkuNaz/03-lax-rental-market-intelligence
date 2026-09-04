# SQL analysis outputs — 03-lax-rental-market-intelligence

## Query 1

| month | total_transactions | seasonality_index |
| --- | --- | --- |
| jan | 170839 | 0.902 |
| feb | 167965 | 0.886 |
| mar | 187889 | 0.992 |
| apr | 182769 | 0.965 |
| may | 199960 | 1.055 |
| jun | 197687 | 1.043 |
| jul | 197101 | 1.04 |
| aug | 211493 | 1.116 |
| sep | 200835 | 1.06 |
| oct | 209083 | 1.103 |
| nov | 183581 | 0.969 |
| dec | 164617 | 0.869 |

## Query 2

| company | annual_transactions | share_pct | market_rank | hhi_contribution |
| --- | --- | --- | --- | --- |
| Hertz | 420765 | 18.5 | 1 | 342.43 |
| Avis | 385529 | 16.96 | 2 | 287.48 |
| Enterprise | 317610 | 13.97 | 3 | 195.11 |
| National | 259449 | 11.41 | 4 | 130.19 |
| Budget | 250358 | 11.01 | 5 | 121.23 |
| Alamo | 208718 | 9.18 | 6 | 84.26 |
| Sixt | 142579 | 6.27 | 7 | 39.32 |
| Thrifty | 115688 | 5.09 | 8 | 25.89 |
| Fox | 110403 | 4.86 | 9 | 23.57 |
| Dollar | 60114 | 2.64 | 10 | 6.99 |
| Zipcar | 2108 | 0.09 | 11 | 0.01 |
| Payless | 498 | 0.02 | 12 | 0.0 |

## Query 3

| company | avg_share_pct | share_stddev_pct_points |
| --- | --- | --- |
| Hertz | 18.52 | 0.958 |
| Alamo | 9.16 | 0.908 |
| Budget | 10.98 | 0.848 |
| National | 11.44 | 0.745 |
| Thrifty | 5.09 | 0.699 |
| Avis | 16.96 | 0.665 |
| Enterprise | 13.96 | 0.625 |
| Sixt | 6.3 | 0.604 |
| Fox | 4.85 | 0.552 |
| Dollar | 2.63 | 0.311 |
| Payless | 0.02 | 0.051 |
| Zipcar | 0.09 | 0.03 |

## Query 4

| company | annual_transactions | annual_gross_revenue | gross_revenue_per_transaction |
| --- | --- | --- | --- |
| Sixt | 142579 | 79495429.0 | 557.55 |
| Dollar | 60114 | 26821933.0 | 446.18 |
| Alamo | 208718 | 88298063.0 | 423.05 |
| Thrifty | 115688 | 43244471.0 | 373.8 |
| Payless | 498 | 185835.0 | 373.16 |
| Hertz | 420765 | 155099800.0 | 368.61 |
| Budget | 250358 | 89026433.0 | 355.6 |
| Enterprise | 317610 | 109975152.0 | 346.26 |
| Avis | 385529 | 119988077.0 | 311.23 |
| Fox | 110403 | 33249574.0 | 301.17 |
| National | 259449 | 70366873.0 | 271.22 |
| Zipcar | 2108 | 392245.0 | 186.07 |
