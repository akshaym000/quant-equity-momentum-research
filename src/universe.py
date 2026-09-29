"""Explicit universe handling without retrospective membership inference."""
import pandas as pd

def supplied_universe(df: pd.DataFrame) -> pd.DataFrame:
    """Return supplied rows unchanged; no constituents are inferred or filtered."""
    if "ticker" not in df: raise ValueError("ticker field required")
    return df.copy()
