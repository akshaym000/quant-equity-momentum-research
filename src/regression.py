"""Panel regression with two-way date and ticker clustered inference."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import norm
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups

@dataclass
class ClusteredResult:
    """Regression coefficients with two-way clustered large-sample inference."""
    params: pd.Series
    bse: pd.Series
    pvalues: pd.Series
    nobs: int

def fit_primary(df: pd.DataFrame):
    """OLS association with pre-signal controls and two-way clustered errors."""
    cols=["future_5d","past_5d","volatility_20d","relative_volume","market_past_5d","date","ticker"]
    x=df[cols].dropna().copy()
    if len(x)<30: raise ValueError(f"Too few complete rows for regression ({len(x)})")
    fit=smf.ols("future_5d ~ past_5d + volatility_20d + relative_volume + market_past_5d",data=x).fit()
    # Two-way cluster-robust covariance (Cameron, Gelbach & Miller construction).
    date_codes=pd.factorize(x.date)[0]; ticker_codes=pd.factorize(x.ticker)[0]
    covariance=cov_cluster_2groups(fit,date_codes,ticker_codes)[2]
    se=np.sqrt(np.clip(np.diag(covariance),0,None))
    p=2*norm.sf(np.abs(fit.params.to_numpy()/se))
    return ClusteredResult(fit.params,pd.Series(se,index=fit.params.index),pd.Series(p,index=fit.params.index),int(fit.nobs))
