# Research report: Empirical Study of Short-Term Equity Momentum

## 1. Executive summary

The supplied dataset contains 2703531 rows from 2000-01-03 to 2026-02-20. In development data, the primary top-minus-bottom five-session spread is -0.00385973 (date-level p=1.17955e-27); clustered regression slope is -0.0394806 (p=1.11405e-15). The untouched holdout spread is -0.000702977 (date-level p=0.21841). Dependence and universe construction limit interpretation.
## 2. Research question

Does an unusually high prior five-session return associate with a systematically different next-five-session return?

## 3. Hypothesis and mechanism

H0: conditional on the design, past 5-session return has no association with next 5-session return. H1: association is positive (momentum).

Gradual information diffusion or underreaction could produce continuation; temporary liquidity pressure could produce reversal. Both are hypotheses, not assumed facts.

## 4. Falsification criteria

- primary slope/spread is not distinguishable from zero.
- estimated sign is non-positive.
- direction fails in the untouched final chronological holdout.
- effect is economically small under declared cost sensitivity.
- effect is concentrated in a narrow time or security slice.

## 5. Data and universe

Input: `data/raw/equity_daily.csv`. 2703531 rows; 472 tickers; 2000-01-03 through 2026-02-20. The panel reflects the supplied dataset; survivorship-free historical membership cannot be inferred from a price file alone. Adjusted close is treated as split/dividend adjusted as provided.

## 6. Methodology

Signal is observed after date t close; trailing features include date t and earlier only. Future target is adjusted close at t+h divided by adjusted close at t, less one. Cheap-first order: quality checks, distributions, quintiles, Welch test, regression, then exploratory/robustness work. The chronological partitions include a 20-date embargo on each side of boundaries; primary estimates use development dates only.

## 7. Primary result

Research-period sample: 1491262 complete stock-date observations, 3918 dates, 435 tickers. Equal-weight date-average top-minus-bottom spread: -0.00385973; 95% t interval across dates [-0.00454881, -0.00317065]; date-level p=1.17955e-27; pooled stock-observation Welch p=1.15393e-114. The date-level interval still ignores serial dependence from overlapping horizons.

| Signal quintile | Observations | Mean future return | Median future return |
| --- | ---: | ---: | ---: |
| 1 | 299699 | 0.00609501 | 0.00394737 |
| 2 | 297545 | 0.00387637 | 0.00325115 |
| 3 | 297593 | 0.00310463 | 0.003 |
| 4 | 297545 | 0.00267275 | 0.00288109 |
| 5 | 298880 | 0.00237606 | 0.00251704 |

## 8. Statistical inference

The date-level spread is the primary uncertainty summary; the pooled Welch test is a naive reference calculation and does not account for repeated dates or overlapping outcomes. Panel regression uses two-way date and ticker clustered standard errors. Even this does not fully solve every form of dependence across overlapping outcomes.

## 9. Regression

Primary 5-day slope=-0.0394806; clustered p=1.11405e-15. This is an observational association.

## 10. Multiple testing

All 25 declared exploratory lookback/horizon combinations are saved in `tables/exploratory_specifications.csv`, with Bonferroni and Benjamini-Hochberg adjusted p-values. They are exploratory and do not replace the primary specification.

## 11. Robustness

Year-specific, 1%/99% winsorized, trailing-volatility, and relative-volume results are saved in tables. Subgroup analyses requiring market capitalization, sectors, or a timestamp-safe benchmark are unavailable unless those fields are supplied.

## 12. Out-of-sample validation

Chronological 60/20/20 splits use unique dates with a 20-date embargo at boundaries. research (2000-01-03 to 2015-08-06): spread -0.00385973, date-level p=1.17955e-27; validation (2015-10-05 to 2020-10-26): spread -0.00260917, date-level p=0.000962116; final_holdout (2020-12-23 to 2026-02-20): spread -0.000702977, date-level p=0.21841. The final segment is reserved as holdout and was evaluated once. Full sample counts are in `tables/chronological_splits.csv`.
## 13. Power sensitivity

For a predeclared 10 bp spread and observed future-return dispersion, the report records a textbook iid two-group sample-size sensitivity at 5% significance and 80% power. It is not an exact power calculation because overlapping returns and cross-sectional dependence violate iid assumptions.

## 14. Economic significance / cost sensitivity

Quintile spread minus assumed round-trip costs is an illustrative diagnostic only. It omits market impact, borrow availability, turnover, and execution. Values are in `tables/cost_sensitivity.csv`.

## 15. Limitations

A supplied CSV cannot establish point-in-time universe membership or eliminate survivorship bias. Overlapping returns and cross-sectional dependence complicate inference. Textbook power sensitivity is only approximate.

## 16. Conclusion

The development-period primary estimate is negative, opposite the pre-specified momentum direction. The validation-period spread is also negative. In the final chronological holdout, the spread is -0.000702977 (date-level p=0.21841) and its interval includes zero; the development result therefore does not survive as a statistically distinguishable effect in the final holdout. This is evidence against the specified positive momentum hypothesis, not proof of a profitable reversal or a causal effect. Overlap and possible survivorship bias remain important limitations.
## 17. Experiment log / dead ends

`experiment_log.csv` retains the pre-specified primary run and every exploratory family member, including null and unavailable estimates.
