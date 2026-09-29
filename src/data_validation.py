"""Data checks that fail loudly rather than silently repairing raw data."""
import pandas as pd

def validate_data(df: pd.DataFrame) -> dict:
    """Validate panel keys, required fields and plausible adjusted prices."""
    needed = {"date", "ticker", "adj_close", "volume"}
    missing = needed - set(df.columns)
    if missing: raise ValueError(f"Missing required fields: {sorted(missing)}")
    x = df.copy()
    x["date"] = pd.to_datetime(x["date"], errors="coerce")
    if x["date"].isna().any(): raise ValueError("Unparseable or missing dates found")
    if x["ticker"].isna().any() or (x["ticker"].astype(str).str.strip() == "").any(): raise ValueError("Missing tickers found")
    if x.duplicated(["date", "ticker"]).any(): raise ValueError("Duplicate date/ticker rows found")
    x["adj_close"] = pd.to_numeric(x["adj_close"], errors="coerce")
    if x["adj_close"].isna().any() or (x["adj_close"] <= 0).any(): raise ValueError("Adjusted prices must be present and positive")
    if (pd.to_numeric(x["volume"], errors="coerce").dropna() < 0).any(): raise ValueError("Negative volume found")
    x = x.sort_values(["ticker", "date"])
    ratios = x.groupby("ticker")["adj_close"].pct_change().abs()
    suspicious = int((ratios > 0.8).sum())
    calendar_gaps=x.groupby("ticker")["date"].diff().dt.days
    long_gaps=int((calendar_gaps > 7).sum())
    dates = sorted(x.date.unique())
    return {"rows": len(x), "tickers": int(x.ticker.nunique()), "dates": len(dates), "start": str(x.date.min().date()), "end": str(x.date.max().date()), "suspicious_abs_daily_moves_over_80pct": suspicious, "ticker_calendar_gaps_over_7_days": long_gaps, "missing_volume": int(pd.to_numeric(x.volume, errors="coerce").isna().sum())}
