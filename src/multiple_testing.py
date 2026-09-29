"""Bonferroni and Benjamini-Hochberg adjustments."""
import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

def adjust_pvalues(frame: pd.DataFrame, p_column="p_value") -> pd.DataFrame:
    """Add family-wise Bonferroni and FDR q-values, preserving missing tests."""
    x=frame.copy(); p=pd.to_numeric(x[p_column],errors="coerce"); valid=p.notna()
    x["p_bonferroni"]=np.nan; x["p_fdr_bh"]=np.nan
    if valid.any():
        x.loc[valid,"p_bonferroni"]=multipletests(p[valid],method="bonferroni")[1]
        x.loc[valid,"p_fdr_bh"]=multipletests(p[valid],method="fdr_bh")[1]
    return x
