"""Predeclared descriptive robustness partitions."""
import pandas as pd
from inference import welch_comparison

def by_calendar_year(df: pd.DataFrame) -> pd.DataFrame:
    """Repeat the primary comparison by calendar year; exploratory only."""
    rows=[]
    for year, part in df.groupby(pd.to_datetime(df.date).dt.year):
        rows.append({"year":int(year),**welch_comparison(part)})
    return pd.DataFrame(rows)

def winsorized_comparison(df: pd.DataFrame, lower=.01, upper=.99) -> dict:
    """Return a sensitivity result after outcome clipping at fixed quantiles."""
    x=df.copy(); lo,hi=x.future_5d.quantile([lower,upper]); x["future_5d"]=x.future_5d.clip(lo,hi)
    return {"lower_quantile":lower,"upper_quantile":upper,"lower_cutoff":float(lo),"upper_cutoff":float(hi),**welch_comparison(x)}
