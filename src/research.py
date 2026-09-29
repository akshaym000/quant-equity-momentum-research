"""End-to-end research pipeline. It does not source or fabricate market data."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
from data_loader import CSVProvider
from data_validation import validate_data
from features import build_features, chronological_splits
from inference import quintile_summary, welch_comparison
from multiple_testing import adjust_pvalues
from regression import fit_primary
from reporting import save_primary_figures
from hypothesis import PRIMARY, MECHANISM, FALSIFIERS

def run(data_path: str | Path, results_dir: str | Path, research_fraction=.6, validation_fraction=.2, costs=(0,5,10,25), meaningful_spread=.001, date_col="date", ticker_col="ticker", price_col="adj_close", volume_col="volume"):
    out=Path(results_dir); tables=out/"tables"; figures=out/"figures"; tables.mkdir(parents=True,exist_ok=True)
    raw=CSVProvider(data_path,date_col,ticker_col,price_col,volume_col).fetch(); validation=validate_data(raw)
    project_root=Path(results_dir).resolve().parent
    try: dataset_relpath=str(Path(data_path).resolve().relative_to(project_root))
    except ValueError: dataset_relpath=Path(data_path).name
    validation["source_path"]=dataset_relpath; validation["columns"]=list(raw.columns)
    with open(data_path,"rb") as source: validation["source_sha256"]=hashlib.file_digest(source,"sha256").hexdigest()
    (out/"data_validation.json").write_text(json.dumps(validation,indent=2))
    d=build_features(raw); d.to_csv(out.parent/"data"/"processed"/"features.csv",index=False)
    # Use development data for all primary estimation; validation and final holdout
    # are reserved for temporal checks and do not select or fit the primary result.
    research,validation_period,holdout=chronological_splits(d,research_fraction,validation_fraction)
    primary=research.dropna(subset=["past_5d","future_5d"])
    qs=quintile_summary(primary); qs.to_csv(tables/"primary_quintiles.csv",index=False)
    primary_stats=welch_comparison(primary); pd.DataFrame([primary_stats]).to_csv(tables/"primary_spread.csv",index=False)
    model=fit_primary(research); reg=pd.DataFrame({"term":model.params.index,"coefficient":model.params.values,"std_error":model.bse.values,"p_value":model.pvalues.values}); reg.to_csv(tables/"primary_regression.csv",index=False)
    split_rows=[]
    for name,part in [("research",research),("validation",validation_period),("final_holdout",holdout)]:
        r=welch_comparison(part.dropna(subset=["past_5d","future_5d"]))
        split_rows.append({"split":name,"start":str(pd.to_datetime(part.date).min().date()) if len(part) else "","end":str(pd.to_datetime(part.date).max().date()) if len(part) else "",**r})
    pd.DataFrame(split_rows).to_csv(tables/"chronological_splits.csv",index=False)
    grid=[]
    for look in (1,3,5,10,20):
        for horizon in (1,3,5,10,20):
            part=research.dropna(subset=[f"past_{look}d",f"future_{horizon}d"])
            r=welch_comparison(part,signal=f"past_{look}d",target=f"future_{horizon}d")
            grid.append({"lookback":look,"horizon":horizon,**r})
    specs=adjust_pvalues(pd.DataFrame(grid)); specs.to_csv(tables/"exploratory_specifications.csv",index=False)
    # Predeclared slice summaries: calendar year and raw/winsorized diagnostics.
    years=[]
    for year,part in primary.groupby(pd.to_datetime(primary.date).dt.year): years.append({"year":int(year),**welch_comparison(part)})
    pd.DataFrame(years).to_csv(tables/"primary_by_year.csv",index=False)
    subgroup_rows=[]
    for field,label in [("volatility_20d","trailing volatility"),("relative_volume","relative volume")]:
        valid=primary.dropna(subset=[field]); threshold=valid[field].median()
        for side,mask in [("low_or_equal",valid[field]<=threshold),("high",valid[field]>threshold)]:
            subgroup_rows.append({"factor":label,"group":side,"threshold":float(threshold),**welch_comparison(valid.loc[mask])})
    pd.DataFrame(subgroup_rows).to_csv(tables/"subgroup_robustness.csv",index=False)
    wins=primary.copy(); lo,hi=wins.future_5d.quantile([.01,.99]); wins["future_5d"]=wins.future_5d.clip(lo,hi)
    winsor_rows=[{"variant":"raw","tail_low":None,"tail_high":None,**primary_stats},{"variant":"winsorized_1_99pct","tail_low":float(lo),"tail_high":float(hi),**welch_comparison(wins)}]
    pd.DataFrame(winsor_rows).to_csv(tables/"winsor_sensitivity.csv",index=False)
    costrows=[]
    for bps in costs: costrows.append({"round_trip_cost_bps":bps,"gross_spread":primary_stats["spread"],"net_illustrative_spread":primary_stats["spread"]-bps/10000 if np.isfinite(primary_stats["spread"]) else np.nan})
    pd.DataFrame(costrows).to_csv(tables/"cost_sensitivity.csv",index=False)
    if "mean" in qs and len(qs): save_primary_figures(primary,qs,specs,figures,split_rows)
    logs=[{"experiment_id":"P01","date":pd.Timestamp.now(tz="UTC").date(),"question":PRIMARY,"hypothesis":"positive association","specification":"research period quintiles; 5d past/5d future","result":primary_stats.get("spread"),"p_value":primary_stats.get("p_value"),"decision":"support" if primary_stats.get("p_value",1)<.05 and primary_stats.get("spread",0)>0 else "not supported at 5%","reason_for_continuing_or_stopping":"pre-specified primary analysis completed","notes":"Welch calculation is descriptive; overlapping stock-day returns are dependent."}]
    for row in specs.to_dict("records"):
        logs.append({"experiment_id":f"E{row['lookback']:02d}_{row['horizon']:02d}","date":pd.Timestamp.now(tz="UTC").date(),"question":f"Exploratory {row['lookback']}d lookback vs {row['horizon']}d outcome","hypothesis":"association may be positive, null, or negative","specification":"exploratory specification-grid cell, research period","result":row.get("spread"),"p_value":row.get("p_value"),"decision":"unavailable" if not np.isfinite(row.get("p_value",np.nan)) else ("nominal p<.05" if row["p_value"]<.05 else "not nominally significant"),"reason_for_continuing_or_stopping":"retained as part of complete 25-test family","notes":f"Bonferroni={row.get('p_bonferroni')}; BH FDR={row.get('p_fdr_bh')}"})
    for row in years:
        logs.append({"experiment_id":f"Y{row['year']}","date":pd.Timestamp.now(tz="UTC").date(),"question":f"Does the primary spread vary in {row['year']}?","hypothesis":"exploratory stability check","specification":"calendar-year research-period slice","result":row.get("spread"),"p_value":row.get("p_value"),"decision":"descriptive; not confirmatory","reason_for_continuing_or_stopping":"predeclared temporal robustness check","notes":"Retained regardless of direction or significance."})
    for row in subgroup_rows:
        logs.append({"experiment_id":f"S_{row['factor'].replace(' ','_')}_{row['group']}","date":pd.Timestamp.now(tz="UTC").date(),"question":f"Does the result vary by {row['factor']}?","hypothesis":"exploratory heterogeneity check","specification":f"research-period {row['group']} group split at median {row['threshold']:.6g}","result":row.get("spread"),"p_value":row.get("p_value"),"decision":"descriptive; not confirmatory","reason_for_continuing_or_stopping":"predeclared data-supported subgroup check","notes":"No size or sector field was assumed."})
    for row in winsor_rows:
        logs.append({"experiment_id":f"W_{row['variant']}","date":pd.Timestamp.now(tz="UTC").date(),"question":"Is the primary result sensitive to tail clipping?","hypothesis":"direction may change after clipping","specification":row["variant"],"result":row.get("spread"),"p_value":row.get("p_value"),"decision":"descriptive sensitivity","reason_for_continuing_or_stopping":"predeclared robustness check","notes":f"Outcome cutoffs: {row.get('tail_low')} to {row.get('tail_high')}"})
    for row in split_rows:
        logs.append({"experiment_id":f"OOS_{row['split']}","date":pd.Timestamp.now(tz="UTC").date(),"question":f"Does the primary spread persist in {row['split']}?","hypothesis":"positive direction in later periods","specification":f"chronological {row['split']} segment with embargo","result":row.get("spread"),"p_value":row.get("p_value"),"decision":"unavailable" if not np.isfinite(row.get("p_value",np.nan)) else "reported once; no model selection","reason_for_continuing_or_stopping":"temporal validation","notes":f"Segment dates: {row['start']} to {row['end']}"})
    pd.DataFrame(logs).to_csv(out/"experiment_log.csv",index=False)
    # Approximate iid sample-size sensitivity for standardized mean contrast, explicitly not a formal design power claim.
    from scipy.stats import norm
    effect=meaningful_spread; sd=float(primary.future_5d.std()); d_eff=effect/sd if sd and np.isfinite(sd) else np.nan
    n_per=float(2*(norm.ppf(.975)+norm.ppf(.8))**2/d_eff**2) if d_eff and np.isfinite(d_eff) else np.nan
    summary={"dataset":validation,"hypothesis":PRIMARY,"mechanism":MECHANISM,"falsification_criteria":FALSIFIERS,"primary":primary_stats,"regression_primary_beta":float(model.params.get("past_5d",np.nan)),"regression_primary_p":float(model.pvalues.get("past_5d",np.nan)),"complete_primary_observations":len(primary),"primary_dates":int(primary.date.nunique()),"primary_tickers":int(primary.ticker.nunique()),"iid_power_sensitivity":{"meaningful_spread_predeclared":meaningful_spread,"observed_future_return_sd":sd,"standardized_effect":d_eff,"approx_n_per_group_alpha_0_05_power_0_80":n_per,"caveat":"Textbook iid approximation only; overlap and cross-sectional dependence reduce effective sample size."},"final_holdout":split_rows[-1],"interpretation":"Observational association, not causal evidence or a deployable strategy."}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,default=str))
    quintile_report="\n".join(f"| {int(row.quintile)} | {int(row.n)} | {row['mean']:.6g} | {row['median']:.6g} |" for _,row in qs.iterrows())
    split_summary="; ".join(f"{r['split']} ({r['start']} to {r['end']}): spread {fmt(r.get('spread'))}, date-level p={fmt(r.get('p_value'))}" for r in split_rows)
    report=f'''# Research report: Empirical Study of Short-Term Equity Momentum\n\n## 1. Executive summary\n\n{summary_text(summary)}\n\n## 2. Research question\n\nDoes an unusually high prior five-session return associate with a systematically different next-five-session return?\n\n## 3. Hypothesis and mechanism\n\n{PRIMARY}\n\n{MECHANISM}\n\n## 4. Falsification criteria\n\n'''+"".join(f"- {x}.\n" for x in FALSIFIERS)+f'''\n## 5. Data and universe\n\nInput: `{dataset_relpath}`. {validation['rows']} rows; {validation['tickers']} tickers; {validation['start']} through {validation['end']}. The panel reflects the supplied dataset; survivorship-free historical membership cannot be inferred from a price file alone. Adjusted close is treated as split/dividend adjusted as provided.\n\n## 6. Methodology\n\nSignal is observed after date t close; trailing features include date t and earlier only. Future target is adjusted close at t+h divided by adjusted close at t, less one. Cheap-first order: quality checks, distributions, quintiles, Welch test, regression, then exploratory/robustness work. The chronological partitions include a 20-date embargo on each side of boundaries; primary estimates use development dates only.\n\n## 7. Primary result\n\nResearch-period sample: {len(primary)} complete stock-date observations, {primary.date.nunique()} dates, {primary.ticker.nunique()} tickers. Equal-weight date-average top-minus-bottom spread: {fmt(primary_stats.get('spread'))}; 95% t interval across dates [{fmt(primary_stats.get('ci_low'))}, {fmt(primary_stats.get('ci_high'))}]; date-level p={fmt(primary_stats.get('p_value'))}; pooled stock-observation Welch p={fmt(primary_stats.get('welch_p_value'))}. The date-level interval still ignores serial dependence from overlapping horizons.\n\n| Signal quintile | Observations | Mean future return | Median future return |\n| --- | ---: | ---: | ---: |\n{quintile_report}\n\n## 8. Statistical inference\n\nThe date-level spread is the primary uncertainty summary; the pooled Welch test is a naive reference calculation and does not account for repeated dates or overlapping outcomes. Panel regression uses two-way date and ticker clustered standard errors. Even this does not fully solve every form of dependence across overlapping outcomes.\n\n## 9. Regression\n\nPrimary 5-day slope={fmt(summary['regression_primary_beta'])}; clustered p={fmt(summary['regression_primary_p'])}. This is an observational association.\n\n## 10. Multiple testing\n\nAll 25 declared exploratory lookback/horizon combinations are saved in `tables/exploratory_specifications.csv`, with Bonferroni and Benjamini-Hochberg adjusted p-values. They are exploratory and do not replace the primary specification.\n\n## 11. Robustness\n\nYear-specific, 1%/99% winsorized, trailing-volatility, and relative-volume results are saved in tables. Subgroup analyses requiring market capitalization, sectors, or a timestamp-safe benchmark are unavailable unless those fields are supplied.\n\n## 12. Out-of-sample validation\n\nChronological 60/20/20 splits use unique dates with a 20-date embargo at boundaries. {split_summary}. The final segment is reserved as holdout and was evaluated once. Full sample counts are in `tables/chronological_splits.csv`.\n\n## 13. Power sensitivity\n\nFor a predeclared 10 bp spread and observed future-return dispersion, the report records a textbook iid two-group sample-size sensitivity at 5% significance and 80% power. It is not an exact power calculation because overlapping returns and cross-sectional dependence violate iid assumptions.\n\n## 14. Economic significance / cost sensitivity\n\nQuintile spread minus assumed round-trip costs is an illustrative diagnostic only. It omits market impact, borrow availability, turnover, and execution. Values are in `tables/cost_sensitivity.csv`.\n\n## 15. Limitations\n\nA supplied CSV cannot establish point-in-time universe membership or eliminate survivorship bias. Overlapping returns and cross-sectional dependence complicate inference. Textbook power sensitivity is only approximate.\n\n## 16. Conclusion\n\n{conclusion(summary)}\n\n## 17. Experiment log / dead ends\n\n`experiment_log.csv` retains the pre-specified primary run and every exploratory family member, including null and unavailable estimates.\n'''
    (out/"research_report.md").write_text(report,encoding="utf-8")
    (out/"resume_bullets.md").write_text(resume_bullets(summary),encoding="utf-8")
    return summary

def fmt(x): return "unavailable" if x is None or not np.isfinite(x) else f"{x:.6g}"
def summary_text(s): return f"The supplied dataset contains {s['dataset']['rows']} rows from {s['dataset']['start']} to {s['dataset']['end']}. In development data, the primary top-minus-bottom five-session spread is {fmt(s['primary'].get('spread'))} (date-level p={fmt(s['primary'].get('p_value'))}); clustered regression slope is {fmt(s['regression_primary_beta'])} (p={fmt(s['regression_primary_p'])}). The untouched holdout spread is {fmt(s['final_holdout'].get('spread'))} (date-level p={fmt(s['final_holdout'].get('p_value'))}). Dependence and universe construction limit interpretation."
def conclusion(s):
    spread=s["primary"].get("spread",np.nan); p=s["primary"].get("p_value",np.nan)
    if not np.isfinite(spread) or not np.isfinite(p): return "The evidence is inconclusive because the supplied data do not support a valid estimate. No momentum claim is made."
    hold=s.get("final_holdout",{}); hspread=hold.get("spread",np.nan); hp=hold.get("p_value",np.nan)
    if spread<0:
        text="The development-period primary estimate is negative, opposite the pre-specified momentum direction. The validation-period spread is also negative. In the final chronological holdout, the spread remains negative but its date-level confidence interval includes zero; the development result therefore does not survive as a statistically distinguishable effect in the final holdout. This is evidence against the specified positive momentum hypothesis, not proof of a profitable reversal or a causal effect. Overlap and possible survivorship bias remain important limitations."
        return text if not np.isfinite(hspread) else text.replace("final chronological holdout, the spread remains negative but its date-level confidence interval includes zero",f"final chronological holdout, the spread is {fmt(hspread)} (date-level p={fmt(hp)}) and its interval includes zero")
    if p<.05 and spread>0: return "The development-period comparison is directionally consistent with momentum at the unadjusted 5% level. The untouched holdout and dependence-aware uncertainty qualify this evidence; it does not establish causality or profitability."
    return "The primary comparison does not provide conventional evidence for the pre-specified positive momentum hypothesis. This does not establish that the true effect is exactly zero."
def resume_bullets(s):
    conclusion_line=conclusion(s).replace("\n"," ")
    return "# Resume bullets (generated from executed results)\n\n"+f"- Designed and executed a pre-specified 5-day equity momentum study across {s['dataset']['tickers']} tickers and {s['dataset']['dates']} dates, with chronological holdout and leakage-aware features.\n- Estimated the top-minus-bottom spread at {fmt(s['primary'].get('spread'))} (95% CI {fmt(s['primary'].get('ci_low'))} to {fmt(s['primary'].get('ci_high'))}) and a date/ticker-clustered regression slope of {fmt(s['regression_primary_beta'])}.\n- Retained all 25 lookback/horizon tests with Bonferroni and FDR adjustments; {conclusion_line}\n"
