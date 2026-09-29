"""Point-in-time features and forward targets from adjusted close prices."""
import numpy as np
import pandas as pd

def build_features(df: pd.DataFrame, lookbacks=(1,3,5,10,20), horizons=(1,3,5,10,20)) -> pd.DataFrame:
    """Signal forms after date t close; targets measure close-to-close from t to t+h."""
    x = df.copy()
    x["date"] = pd.to_datetime(x.date)
    x = x.sort_values(["ticker", "date"]).reset_index(drop=True)
    g = x.groupby("ticker", group_keys=False)
    x["daily_return"] = g.adj_close.pct_change()
    for n in lookbacks:
        x[f"past_{n}d"] = g.adj_close.pct_change(n)
    x["volatility_20d"] = g.daily_return.transform(lambda s: s.rolling(20, min_periods=20).std())
    # Volume z score uses observations through signal close, per ticker.
    logv = np.log1p(pd.to_numeric(x.volume, errors="coerce"))
    x["relative_volume"] = logv.groupby(x.ticker).transform(lambda s: (s - s.rolling(20, min_periods=10).mean()) / s.rolling(20, min_periods=10).std())
    for n in horizons:
        x[f"future_{n}d"] = g.adj_close.shift(-n) / x.adj_close - 1
    if "past_5d" in x:
        x["market_past_5d"] = x.groupby("date")["past_5d"].transform("mean")
    else:
        # This optional cross-sectional control exists only when 5-day features
        # are requested; smaller feature subsets remain valid for focused tests.
        x["market_past_5d"] = np.nan
    return x

def chronological_splits(df: pd.DataFrame, research_fraction=.6, validation_fraction=.2, embargo=20):
    """Split unique dates chronologically with an embargo for forward labels."""
    dates = sorted(pd.to_datetime(df.date).unique())
    if not 0 < research_fraction < 1 or not 0 < validation_fraction < 1 or research_fraction + validation_fraction >= 1: raise ValueError("Split fractions must be positive and sum to less than one")
    a, b = int(len(dates)*research_fraction), int(len(dates)*(research_fraction+validation_fraction))
    # Remove observations near boundaries so a 20-session target cannot run
    # from one period into another. Date gaps are conservative for a common panel.
    bounds=[(0,max(0,a-embargo)),(min(len(dates),a+embargo),max(0,b-embargo)),(min(len(dates),b+embargo),len(dates))]
    return tuple(df[pd.to_datetime(df.date).isin(set(dates[i:j]))].copy() for i,j in bounds)
