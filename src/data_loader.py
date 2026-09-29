"""Provider-agnostic local CSV ingestion. Raw data is only read, never rewritten."""
from pathlib import Path
import pandas as pd

REQUIRED = {"date", "ticker", "adj_close", "volume"}

def load_csv(path: str | Path, date_col: str = "date", ticker_col: str = "ticker", price_col: str = "adj_close", volume_col: str = "volume") -> pd.DataFrame:
    """Load a supplied daily OHLCV CSV and normalize required column names."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Market data not found: {p}. See README.md for the required CSV schema.")
    mapping = {date_col: "date", ticker_col: "ticker", price_col: "adj_close", volume_col: "volume"}
    df = pd.read_csv(p, usecols=list(mapping))
    absent = set(mapping) - set(df.columns)
    if absent:
        raise ValueError(f"CSV is missing configured columns: {sorted(absent)}")
    return df.rename(columns=mapping)

class CSVProvider:
    """Minimal provider contract implementation for user-supplied local data."""
    def __init__(self, path: str | Path, date_col="date", ticker_col="ticker", price_col="adj_close", volume_col="volume"):
        self.path = Path(path); self.columns=(date_col,ticker_col,price_col,volume_col)
    def fetch(self) -> pd.DataFrame:
        return load_csv(self.path,*self.columns)
