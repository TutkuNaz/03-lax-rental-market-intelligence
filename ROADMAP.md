# Roadmap

## Near term

- Add regression fixtures for additional LAWA PDF layouts.
- Record parser version, retrieval time, and source-document hash with every local extraction.
- Add passenger-volume normalization using an official LAWA traffic series.

## Multi-year release

- Extend the pipeline across the official LAWA rental-car archive, which currently exposes reports from 2011 onward.
- Normalize company-name and parent-brand changes without rewriting source labels.
- Separate nominal revenue movement from transaction-volume change.
- Publish year-over-year seasonality, concentration, and revenue-per-transaction panels.
- Add explicit missing-report and revised-report handling.

## Longer term

- Package the normalized tables as a versioned, machine-readable dataset with a data dictionary.
- Add uncertainty and sensitivity views for operational scenarios.
- Link the project to comparable airport-mobility sources through the Automotive Open Data Hub.

Source archive: https://www.lawa.org/lawa-investor-relations/statistics-for-lax/lax-rental-car-statistics
