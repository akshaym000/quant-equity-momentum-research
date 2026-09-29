# Empirical Study of Short-Term Equity Momentum

This project tests whether a stock's return over the previous five trading sessions is associated with its return over the next five sessions. It is a research study, not a strategy pitch: the hypothesis is fixed in advance, failed and null tests are retained, and the analysis can support momentum, reversal, or no detectable relationship.

## Research design

**Primary hypothesis:** no association is the null; the pre-specified alternative is a positive association between prior and subsequent five-session returns. Gradual information diffusion could produce continuation, while temporary liquidity pressure could produce reversal. Both are candidate explanations, not assumptions.

The signal is formed after the close on date *t*. Features use data available through that close; the forward *h*-session outcome is adjusted close at *t+h* divided by adjusted close at *t*, less one. Thus the outcome begins after the signal timestamp. The primary comparison forms cross-sectional quintiles by date and compares top versus bottom. An OLS panel regression includes trailing volatility, relative volume, and a cross-sectional trailing-market proxy, with date and ticker clustered errors.

The sequence is intentionally cheap-first: data quality, descriptive distributions, quintile comparison, Welch comparison and confidence interval, regression, then exploratory and robustness work. The Welch calculation is a reference estimate and does not account for overlapping outcomes. Regression uses two-way date/ticker clustering, which still cannot eliminate all dependence concerns.

## Data

The supplied [`SP500_Historical_Data.csv` source page on Kaggle](https://www.kaggle.com/code/lalit7881/s-p-500-historical-analysis) provides the dataset used here. The file is stored locally at `data/raw/equity_daily.csv`. It contains 2,703,531 rows for 472 tickers from 2000-01-03 through 2026-02-20, with no missing required fields or duplicate ticker-date rows. Kaggle describes the prices as sourced from Yahoo Finance via `yfinance`; this project analyzes the supplied snapshot and does not fetch additional market data. The validator flags three adjusted-close moves above 80% for review (HIG on 2008-12-05, MS on 2008-10-13, and WMB on 2002-07-29); these are retained. For another file, set its path and the source column names in `config.json`; the minimum required columns are date, ticker, adjusted close, and volume. The loader reads only those fields. Adjusted close is assumed to reflect corporate actions as supplied by the vendor. Keep raw files immutable; processing writes to `data/processed/`.

The loader is provider-agnostic and accepts local CSV paths. It validates duplicate keys, date parseability, ticker presence, nonpositive prices, negative volume, and flags unusually large daily moves for review. A price panel alone cannot demonstrate point-in-time index membership, sector histories, or market capitalization. These are not invented; corresponding subgroup analyses are omitted unless timestamp-safe fields are supplied and integrated.

## Inference, multiplicity, and robustness

The primary five-by-five test is distinct from the exploratory grid of 25 lookback/horizon combinations. All grid rows are saved, including null or unavailable results, with Bonferroni and Benjamini-Hochberg adjustments. Declared diagnostics include calendar-year slices and raw versus 1%/99% winsorized outcomes. Costs are simple round-trip sensitivity assumptions applied to the spread, not a performance claim; turnover, market impact, borrow, and fill assumptions are not modeled.

Unique dates are divided chronologically 60/20/20, with a 20-session embargo at each boundary to reduce target overlap across periods. The final holdout is not used to choose the features or thresholds. If the data history is too short, an empty/unstable split will be reported as a limitation. A textbook iid power sensitivity uses a predeclared 10 bp spread and observed dispersion; overlapping outcomes and cross-sectional dependence make this an approximation, not formal power assurance.

## Key findings

In the development period, the top-minus-bottom five-session spread was **−0.386%** (95% date-level interval −0.455% to −0.317%; date-level *p* = 1.18×10⁻²⁷). The validation-period spread was also negative (−0.261%; *p* = 0.00096). In the untouched final holdout it was −0.070%, with an interval spanning zero and date-level *p* = 0.218. The pre-specified positive momentum hypothesis is not supported; the negative association did not remain statistically distinguishable from zero in the final holdout. These estimates are observational, and the date-level tests do not adjust for serial dependence from overlapping five-session targets.

The complete exploratory grid contains 25 lookback/horizon tests with Bonferroni and Benjamini-Hochberg corrections. Results, nulls, and robustness slices are retained under `results/tables/` and `results/experiment_log.csv`.

## Demo walkthrough

For a short project walkthrough, start with [`results/research_report.md`](results/research_report.md), then view [`results/figures/future_5d_by_quintile.png`](results/figures/future_5d_by_quintile.png) and [`results/tables/chronological_splits.csv`](results/tables/chronological_splits.csv). The report states the hypothesis, design, main estimate, robustness work, and final holdout result. The charts and tables let a reviewer verify the evidence without installing an interactive app.

## Run

Python 3.11+ is recommended. Install the pinned dependencies and run:

```powershell
python -m pip install -e ".[dev]"
python scripts/validate_data.py
python scripts/run_full_research.py
python -m pytest
```

The full command writes machine-readable tables and figures under `results/`, a report, and resume bullets derived from that execution. The supplied raw CSV is excluded from version control by `.gitignore`; provide a suitably licensed copy at the configured path when reproducing the run. Tests use small synthetic series only to verify transformations and never populate research conclusions.

## Project map

- `src/`: ingestion, validation, point-in-time feature construction, chronological splits, inference, regression, multiplicity, and reporting.
- `scripts/`: validation, dataset construction, primary/full run, and robustness entry points.
- `notebooks/`: concise, reproducible guides that call the same source modules.
- `tests/`: data validation, feature and target timing, split isolation, descriptive inference, and p-value corrections.
- `results/`: generated report, resume bullets, experiment log, tables, and figures from the supplied data run.

## Findings

The full pipeline has been executed on the supplied data. Consult `results/research_report.md` and `results/summary.json` for the complete results and limitations. Conclusions remain limited to the supplied data and design and are explicitly observational.
