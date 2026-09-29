"""Descriptive and inferential utilities for the pre-specified comparison."""
import numpy as np
import pandas as pd
from scipy import stats

def _assign_quintiles(x: pd.DataFrame, signal: str, q: int) -> pd.Series:
    """Rank signal values within date without per-date Python qcut callbacks."""
    ranks=x.groupby("date",sort=False)[signal].rank(method="first")
    counts=x.groupby("date",sort=False)[signal].transform("count")
    # Equivalent to qcut's interpolated rank cutpoints: the k-th cut is
    # 1 + (n - 1) * k / q, with boundary values in the lower bin.
    labels=np.ceil((ranks-1)*q/(counts-1)).clip(1,q)
    return labels.where(counts>=q)

def quintile_summary(df: pd.DataFrame, signal="past_5d", target="future_5d", q=5):
    x = df[[signal,target,"date","ticker"]].dropna().copy()
    x["quintile"] = _assign_quintiles(x,signal,q)
    return x.dropna(subset=["quintile"]).groupby("quintile")[target].agg(n="count",mean="mean",median="median",std="std",q05=lambda s:s.quantile(.05),q95=lambda s:s.quantile(.95)).reset_index()

def welch_comparison(df: pd.DataFrame, signal="past_5d", target="future_5d", q=5):
    x=df[[signal,target,"date"]].dropna().copy()
    x["q"]=_assign_quintiles(x,signal,q)
    lo=x.loc[x.q==1,target].to_numpy(); hi=x.loc[x.q==q,target].to_numpy()
    daily=x.loc[x.q.isin([1,q])].pivot_table(index="date",columns="q",values=target,aggfunc="mean").dropna()
    if len(lo)<2 or len(hi)<2 or len(daily)<2: return {"n_bottom":len(lo),"n_top":len(hi),"n_dates":len(daily),"spread":np.nan,"se":np.nan,"ci_low":np.nan,"ci_high":np.nan,"p_value":np.nan,"welch_p_value":np.nan}
    # Equal-weight date-level top-minus-bottom spreads reduce stock-count imbalance
    # and avoid treating every stock-day as independent. Time dependence remains.
    date_spread=(daily[q]-daily[1]).to_numpy()
    spread=float(np.mean(date_spread)); se=float(stats.sem(date_spread))
    ci=stats.t.ppf(.975,len(date_spread)-1)*se
    date_t,date_p=stats.ttest_1samp(date_spread,0)
    wt,wp=stats.ttest_ind(hi,lo,equal_var=False)
    return {"n_bottom":len(lo),"n_top":len(hi),"n_dates":len(daily),"spread":spread,"se":se,"ci_low":spread-float(ci),"ci_high":spread+float(ci),"welch_t":float(wt),"welch_p_value":float(wp),"date_level_t":float(date_t),"p_value":float(date_p),"cohen_d_date":float(spread/np.std(date_spread,ddof=1)) if np.std(date_spread,ddof=1)>0 else np.nan}
